"""Views for creating tasks for all classification runs of a species."""

import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.classification import CallProbability, ClassificationResult, ClassificationRun
from battycoda_app.models.organization import Species
from battycoda_app.models.task import Task, TaskBatch

from .batch_creation import get_pending_runs_for_species, create_task_batch_helper


@login_required
def create_tasks_for_species_view(request, species_id):
    """Create task batches for all completed classification runs of a species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile

    # Check permissions
    if profile.group and profile.is_current_group_admin:
        if not ClassificationRun.objects.filter(
            segmentation__recording__species=species,
            segmentation__recording__group=profile.group,
            status="completed"
        ).exists():
            messages.error(request, "No completed classification runs for this species in your group.")
            return redirect('battycoda_app:create_task_batches_for_species')
    else:
        if not ClassificationRun.objects.filter(
            segmentation__recording__species=species,
            segmentation__recording__created_by=request.user,
            status="completed"
        ).exists():
            messages.error(request, "You don't have permission to create tasks for this species.")
            return redirect('battycoda_app:create_task_batches_for_species')

    # For POST request, create task batches for each completed run
    if request.method == "POST":
        batch_prefix = request.POST.get('name_prefix') or f"Review of {species.name} classifications"
        confidence_threshold = request.POST.get("confidence_threshold")

        # Parse confidence threshold
        max_confidence = None
        if confidence_threshold:
            try:
                max_confidence = float(confidence_threshold)
                if max_confidence < 0 or max_confidence > 1:
                    messages.error(request, "Confidence threshold must be between 0 and 1.")
                    return redirect('battycoda_app:create_task_batches_for_species')
            except ValueError:
                messages.error(request, "Invalid confidence threshold value.")
                return redirect('battycoda_app:create_task_batches_for_species')

        # Check total task count before proceeding
        pending_runs = get_pending_runs_for_species(species, profile)
        total_results = ClassificationResult.objects.filter(
            classification_run__in=pending_runs
        ).count()

        MAX_TASKS = 50000
        if total_results > MAX_TASKS:
            messages.error(
                request,
                f"Cannot create task batches: {total_results:,} tasks would be created, "
                f"which exceeds the maximum of {MAX_TASKS:,}. Please use confidence threshold "
                f"filtering or process runs individually."
            )
            return redirect('battycoda_app:create_task_batches_for_species')

        try:
            # Create task batches for each run
            batches_created = 0
            tasks_created = 0
            total_filtered = 0

            # Use a transaction to lock runs and prevent concurrent processing
            with transaction.atomic():
                # Get all completed runs without task batches and lock them
                # skip_locked=True ensures we only get runs not being processed by others
                runs = get_pending_runs_for_species(species, profile, lock_for_processing=True)

                # Process each run individually
                for run in runs:
                    try:
                        # Get the recording from the segmentation
                        recording = run.segmentation.recording

                        # Create a name for this batch
                        batch_name = f"{batch_prefix} - {recording.name}"
                        description = f"Automatically created from classification run: {run.name}"

                        # Use the helper function to create the batch and tasks
                        batch, run_tasks_created, run_tasks_filtered = create_task_batch_helper(
                            run=run,
                            batch_name=batch_name,
                            description=description,
                            created_by=request.user,
                            group=profile.group,
                            max_confidence=max_confidence
                        )

                        # If tasks were created, increment counters
                        if batch is not None:
                            batches_created += 1
                            tasks_created += run_tasks_created
                            total_filtered += run_tasks_filtered

                    except Exception as e:
                        # Log the error but continue with other runs
                        print(f"Error creating task batch for run {run.id}: {str(e)}")
                        print(traceback.format_exc())
                        # Continue processing other runs
                        continue

            if batches_created > 0:
                # Create success message with filtering info
                success_msg = f"Created {batches_created} task batches with a total of {tasks_created} tasks for {species.name}."
                if total_filtered > 0:
                    success_msg += f" ({total_filtered} high-confidence tasks filtered out)"
                messages.success(request, success_msg)
            else:
                messages.warning(request, f"No task batches were created. All segments may already have tasks.")

            return redirect('battycoda_app:task_batch_list')

        except Exception as e:
            messages.error(request, f"Error creating task batches: {str(e)}")
            return redirect('battycoda_app:create_task_batches_for_species')

    # For GET request, show confirmation form
    # Count pending runs and estimate total tasks
    pending_runs = get_pending_runs_for_species(species, profile)
    pending_runs_count = pending_runs.count()

    estimated_tasks = ClassificationResult.objects.filter(
        classification_run__in=pending_runs
    ).count()

    context = {
        'species': species,
        'pending_runs_count': pending_runs_count,
        'estimated_tasks': estimated_tasks,
        'max_tasks': 50000,
        'default_name_prefix': f"Review of {species.name} classifications"
    }

    return render(request, 'classification/create_species_tasks.html', context)
