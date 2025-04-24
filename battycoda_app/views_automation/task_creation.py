"""Views for creating tasks from detection runs.

Provides functionality to convert detection run results into manual tasks for review.
"""

import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models.detection import CallProbability, DetectionResult, DetectionRun
from battycoda_app.models.organization import Species
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


def get_pending_runs_for_species(species, user_profile):
    """Helper function to get completed runs without task batches for a species."""
    base_query = DetectionRun.objects.filter(
        segmentation__recording__species=species,
        status="completed", 
    )
    
    # Filter by user permissions
    if user_profile.group and user_profile.is_admin:
        # Admin sees all runs in the group
        base_query = base_query.filter(segmentation__recording__group=user_profile.group)
    else:
        # Regular user only sees own runs
        base_query = base_query.filter(segmentation__recording__created_by=user_profile.user)
    
    # Filter runs without task batches
    return base_query.filter(task_batches__isnull=True)


@login_required
def create_task_batches_for_species_view(request):
    """Display species with completed classification runs that don't have task batches."""
    profile = request.user.profile
    
    # Get all species with completed detection runs
    if profile.group and profile.is_admin:
        # Admin sees all species in their group
        species_list = Species.objects.filter(
            recordings__segmentations__detection_runs__status="completed",
            recordings__group=profile.group
        ).distinct()
    else:
        # Regular user sees only species for their own recordings
        species_list = Species.objects.filter(
            recordings__segmentations__detection_runs__status="completed",
            recordings__created_by=request.user
        ).distinct()
    
    items = []
    for species in species_list:
        # Get pending runs for this species
        pending_runs = get_pending_runs_for_species(species, profile)
        pending_runs_count = pending_runs.count()
        
        if pending_runs_count > 0:
            items.append({
                'name': species.name,
                'type_name': 'Bat Species',
                'count': pending_runs_count,
                'created_at': species.created_at,
                'detail_url': reverse('battycoda_app:species_detail', args=[species.id]),
                'action_url': reverse('battycoda_app:create_tasks_for_species', args=[species.id])
            })
    
    context = {
        'title': 'Create Task Batches for Classified Segments',
        'list_title': 'Species with Completed Classification Runs',
        'parent_url': 'battycoda_app:automation_home',
        'parent_name': 'Automation',
        'th1': 'Species',
        'th2': 'Type',
        'th3': 'Classification Runs',
        'show_count': True,
        'action_text': 'Create Tasks',
        'action_icon': 'clipboard',
        'empty_message': 'No species with pending classification runs found.',
        'items': items
    }
    
    return render(request, "automation/select_entity.html", context)


@login_required
def create_tasks_for_species_view(request, species_id):
    """Create task batches for all completed classification runs of a species."""
    species = get_object_or_404(Species, id=species_id)
    profile = request.user.profile
    
    # Check permissions
    if profile.group and profile.is_admin:
        if not DetectionRun.objects.filter(
            segmentation__recording__species=species, 
            segmentation__recording__group=profile.group,
            status="completed"
        ).exists():
            messages.error(request, "No completed classification runs for this species in your group.")
            return redirect('battycoda_app:create_task_batches_for_species')
    else:
        if not DetectionRun.objects.filter(
            segmentation__recording__species=species, 
            segmentation__recording__created_by=request.user,
            status="completed"
        ).exists():
            messages.error(request, "You don't have permission to create tasks for this species.")
            return redirect('battycoda_app:create_task_batches_for_species')
    
    # For POST request, create task batches for each completed run
    if request.method == "POST":
        batch_prefix = request.POST.get('name_prefix') or f"Review of {species.name} classifications"
        
        try:
            # Get all completed runs without task batches
            runs = get_pending_runs_for_species(species, profile)
            
            # Create task batches for each run
            batches_created = 0
            tasks_created = 0
            
            for run in runs:
                try:
                    with transaction.atomic():
                        # Get the recording from the segmentation
                        recording = run.segmentation.recording
                        
                        # Create a name for this batch
                        batch_name = f"{batch_prefix} - {recording.name}"
                        
                        # Create the task batch
                        batch = TaskBatch.objects.create(
                            name=batch_name,
                            description=f"Automatically created from classification run: {run.name}",
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
                        run_tasks_created = 0
                        for result in results:
                            segment = result.segment
                            
                            # Skip segments that already have tasks
                            if segment.task:
                                continue
                                
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
                            
                            run_tasks_created += 1
                        
                        # If no tasks were created, delete the batch
                        if run_tasks_created == 0:
                            batch.delete()
                        else:
                            batches_created += 1
                            tasks_created += run_tasks_created
                        
                except Exception as e:
                    # Log the error but continue with other runs
                    print(f"Error creating task batch for run {run.id}: {str(e)}")
                    continue
            
            if batches_created > 0:
                messages.success(
                    request, 
                    f"Created {batches_created} task batches with a total of {tasks_created} tasks for {species.name}."
                )
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
    
    return render(request, 'automation/create_species_tasks.html', context)