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

        try:
            # Get all completed runs without task batches
            runs = get_pending_runs_for_species(species, profile)

            # Create task batches for each run
            batches_created = 0
            tasks_created = 0
            total_filtered = 0

            # Use a single transaction for the entire process to prevent race conditions
            with transaction.atomic():
                # First, lock all segments we might modify to prevent concurrent access
                # Get all segments associated with these runs
                from battycoda_app.models import Segment
                all_segments_ids = []

                for run in runs:
                    # Get segment IDs for this run
                    result_segments = ClassificationResult.objects.filter(
                        classification_run=run
                    ).values_list('segment_id', flat=True)
                    all_segments_ids.extend(result_segments)

                # Lock all these segments using SELECT FOR UPDATE to prevent concurrent modifications
                if all_segments_ids:
                    locked_segments = list(Segment.objects.filter(
                        id__in=all_segments_ids
                    ).select_for_update())  # This locks the rows

                # Now process each run
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
                        # Don't continue - raise the exception to rollback the transaction
                        raise

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
    # Count pending runs
    pending_runs_count = get_pending_runs_for_species(species, profile).count()

    context = {
        'species': species,
        'pending_runs_count': pending_runs_count,
        'default_name_prefix': f"Review of {species.name} classifications"
    }

    return render(request, 'classification/create_species_tasks.html', context)
