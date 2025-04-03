"""Views for creating tasks from detection runs.

Provides functionality to convert detection run results into manual tasks for review.
"""

import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from battycoda_app.models.detection import CallProbability, DetectionResult, DetectionRun
from battycoda_app.models.task import Task, TaskBatch

@login_required
def create_task_batch_from_detection_run(request, run_id):
    """Create a task batch from a detection run's results for manual review and correction."""
    # Get the detection run
    run = get_object_or_404(DetectionRun, id=run_id)

    # Check if the user has permission
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to create a task batch from this classification run.")
        return redirect("battycoda_app:automation_home")

    # Check if the run is completed
    if run.status != "completed":
        messages.error(request, "Cannot create a task batch from an incomplete classification run.")
        return redirect("battycoda_app:detection_run_detail", run_id=run_id)

    if request.method == "POST":
        # Get form data
        batch_name = request.POST.get("name") or f"Review of {run.name}"
        description = request.POST.get("description") or f"Manual review of classification run: {run.name}"

        try:
            with transaction.atomic():
                # Get the recording from the segmentation
                recording = run.segmentation.recording

                # Use the batch name as is, no need for timestamps or unique constraints
                # batch_name is already set from the form data above

                # Create the task batch
                batch = TaskBatch.objects.create(
                    name=batch_name,
                    description=description,
                    created_by=request.user,
                    wav_file_name=recording.wav_file.name,
                    wav_file=recording.wav_file,
                    species=recording.species,
                    project=recording.project,
                    group=profile.group,
                    detection_run=run,  # Link to the detection run
                )

                # Get all detection results from this run
                results = DetectionResult.objects.filter(detection_run=run)

                # Create tasks for each detection result's segment
                tasks_created = 0
                for result in results:
                    segment = result.segment

                    # Get the highest probability call type
                    top_probability = (
                        CallProbability.objects.filter(detection_result=result).order_by("-probability").first()
                    )

                    # Create a task for this segment
                    task = Task.objects.create(
                        wav_file_name=recording.wav_file.name,
                        onset=segment.onset,
                        offset=segment.offset,
                        species=recording.species,
                        project=recording.project,
                        batch=batch,
                        created_by=request.user,
                        group=profile.group,
                        # Use the highest probability call type as the initial label
                        label=top_probability.call.short_name if top_probability else None,
                        status="pending",
                    )

                    # Link the task back to the segment
                    segment.task = task
                    segment.save()

                    tasks_created += 1

                messages.success(request, f"Created task batch '{batch.name}' with {tasks_created} tasks for review.")

                return redirect("battycoda_app:task_batch_detail", batch_id=batch.id)

        except Exception as e:

            messages.error(request, f"Error creating task batch: {str(e)}")
            return redirect("battycoda_app:detection_run_detail", run_id=run_id)

    # For GET requests, show the form
    context = {
        "run": run,
        "recording": run.segmentation.recording,
        "default_name": f"Review of {run.name}",
        "default_description": f"Manual review of classification run: {run.name}",
    }

    return render(request, "automation/create_task_batch.html", context)
