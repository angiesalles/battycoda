"""Views for creating tasks for all classification runs of a species."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import ClassificationResult, ClassificationRun
from battycoda_app.models.organization import Species

from .batch_creation import get_pending_runs_for_species


@login_required
def create_tasks_for_species_view(request, species_id):
    """Create task batches for all completed classification runs of a species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile

    # Check permissions
    if profile.group and profile.is_current_group_admin:
        if not ClassificationRun.objects.filter(
            segmentation__recording__species=species, segmentation__recording__group=profile.group, status="completed"
        ).exists():
            messages.error(request, "No completed classification runs for this species in your group.")
            return redirect("battycoda_app:create_task_batches_for_species")
    else:
        if not ClassificationRun.objects.filter(
            segmentation__recording__species=species,
            segmentation__recording__created_by=request.user,
            status="completed",
        ).exists():
            messages.error(request, "You don't have permission to create tasks for this species.")
            return redirect("battycoda_app:create_task_batches_for_species")

    # For POST request, queue background task
    if request.method == "POST":
        batch_prefix = request.POST.get("name_prefix") or f"Review of {species.name} classifications"
        confidence_threshold = request.POST.get("confidence_threshold")

        # Parse confidence threshold
        max_confidence = None
        if confidence_threshold:
            try:
                max_confidence = float(confidence_threshold)
                if max_confidence < 0 or max_confidence > 1:
                    messages.error(request, "Confidence threshold must be between 0 and 1.")
                    return redirect("battycoda_app:create_task_batches_for_species")
            except ValueError:
                messages.error(request, "Invalid confidence threshold value.")
                return redirect("battycoda_app:create_task_batches_for_species")

        # Check total task count before proceeding
        pending_runs = get_pending_runs_for_species(species, profile)
        total_results = ClassificationResult.objects.filter(classification_run__in=pending_runs).count()

        MAX_TASKS = 50000
        if total_results > MAX_TASKS:
            messages.error(
                request,
                f"Cannot create task batches: {total_results:,} tasks would be created, "
                f"which exceeds the maximum of {MAX_TASKS:,}. Please use confidence threshold "
                f"filtering or process runs individually.",
            )
            return redirect("battycoda_app:create_task_batches_for_species")

        # Queue the background task
        from battycoda_app.tasks import create_task_batches_for_species_task

        create_task_batches_for_species_task.delay(
            species.id,
            request.user.id,
            profile.group.id if profile.group else None,
            batch_prefix,
            max_confidence,
        )

        messages.info(
            request,
            f"Task batch creation for {species.name} has been started in the background. "
            "You will receive a notification when it completes.",
        )
        return redirect("battycoda_app:task_batch_list")

    # For GET request, show confirmation form
    # Count pending runs and estimate total tasks
    pending_runs = get_pending_runs_for_species(species, profile)
    pending_runs_count = pending_runs.count()

    estimated_tasks = ClassificationResult.objects.filter(classification_run__in=pending_runs).count()

    context = {
        "species": species,
        "pending_runs_count": pending_runs_count,
        "estimated_tasks": estimated_tasks,
        "max_tasks": 50000,
        "default_name_prefix": f"Review of {species.name} classifications",
    }

    return render(request, "classification/create_species_tasks.html", context)
