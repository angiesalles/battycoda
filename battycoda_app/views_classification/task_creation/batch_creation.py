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

from battycoda_app.models.classification import CallProbability, ClassificationResult, ClassificationRun
from battycoda_app.models.organization import Species
from battycoda_app.models.task import Task, TaskBatch
from .helpers import create_task_batch_helper


@login_required
def create_task_batch_from_detection_run(request, run_id):
    """Create a task batch from a detection run's results for manual review and correction."""
    # Get the detection run
    run = get_object_or_404(ClassificationRun, id=run_id)

    # Check if the user has permission
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to create a task batch from this classification run.")
        return redirect("battycoda_app:classification_home")

    # Check if the run is completed
    if run.status != "completed":
        messages.error(request, "Cannot create a task batch from an incomplete classification run.")
        return redirect("battycoda_app:detection_run_detail", run_id=run_id)

    if request.method == "POST":
        # Get form data
        batch_name = request.POST.get("name") or f"Review of {run.name}"
        description = request.POST.get("description") or f"Manual review of classification run: {run.name}"
        confidence_threshold = request.POST.get("confidence_threshold")
        
        # Parse confidence threshold
        max_confidence = None
        if confidence_threshold:
            try:
                max_confidence = float(confidence_threshold)
                if max_confidence < 0 or max_confidence > 1:
                    messages.error(request, "Confidence threshold must be between 0 and 1.")
                    return redirect("battycoda_app:detection_run_detail", run_id=run_id)
            except ValueError:
                messages.error(request, "Invalid confidence threshold value.")
                return redirect("battycoda_app:detection_run_detail", run_id=run_id)

        try:
            # Use helper function to create the batch
            batch, tasks_created, tasks_filtered = create_task_batch_helper(
                run=run,
                batch_name=batch_name,
                description=description,
                created_by=request.user,
                group=profile.group,
                max_confidence=max_confidence
            )

            if batch is None:
                messages.warning(request, "No tasks were created. All segments may already have tasks or were filtered out.")
                return redirect("battycoda_app:detection_run_detail", run_id=run_id)

            # Create success message with filtering info
            success_msg = f"Created task batch '{batch.name}' with {tasks_created} tasks for review."
            if tasks_filtered > 0:
                success_msg += f" ({tasks_filtered} high-confidence tasks filtered out)"
            messages.success(request, success_msg)
            return redirect("battycoda_app:task_batch_detail", batch_id=batch.id)

        except Exception as e:
            import traceback
            print(f"Error creating task batch for run {run_id}: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Error creating task batch: {str(e)}")
            return redirect("battycoda_app:detection_run_detail", run_id=run_id)

    # For GET requests, show the form
    context = {
        "run": run,
        "recording": run.segmentation.recording,
        "default_name": f"Review of {run.name}",
        "default_description": f"Manual review of classification run: {run.name}",
    }

    return render(request, "classification/create_task_batch.html", context)


def get_pending_runs_for_species(species, user_profile, lock_for_processing=False):
    """
    Helper function to get completed runs without task batches for a species.

    Args:
        species: Species to get runs for
        user_profile: UserProfile for permission filtering
        lock_for_processing: If True, uses select_for_update(skip_locked=True)
                           to prevent concurrent processing of the same runs.
                           Only use this within a transaction context.

    Returns:
        QuerySet of ClassificationRun objects
    """
    from django.db.models import Exists, OuterRef

    base_query = ClassificationRun.objects.filter(
        segmentation__recording__species=species,
        status="completed",
    )

    # Filter by user permissions
    if user_profile.group and user_profile.is_current_group_admin:
        # Admin sees all runs in the group
        base_query = base_query.filter(segmentation__recording__group=user_profile.group)
    else:
        # Regular user only sees own runs
        base_query = base_query.filter(segmentation__recording__created_by=user_profile.user)

    # Filter runs without task batches using a subquery to avoid outer join
    # (select_for_update doesn't work with outer joins)
    has_task_batch = TaskBatch.objects.filter(detection_run=OuterRef('pk'))
    query = base_query.annotate(has_batch=Exists(has_task_batch)).filter(has_batch=False)

    # Optionally lock rows to prevent race conditions during processing
    if lock_for_processing:
        # skip_locked=True means if another process is already working on some runs,
        # we'll skip those and only get the unlocked ones
        query = query.select_for_update(skip_locked=True)

    return query


@login_required
def create_task_batches_for_species_view(request):
    """Display species with completed classification runs that don't have task batches."""
    profile = request.user.profile

    project_id = request.GET.get('project')

    # Get all species with completed detection runs
    if profile.group and profile.is_current_group_admin:
        query = Species.objects.filter(
            recordings__segmentations__classification_runs__status="completed",
            recordings__group=profile.group
        )
        if project_id:
            try:
                query = query.filter(recordings__project_id=int(project_id))
            except (ValueError, TypeError):
                pass
        species_list = query.distinct()
    else:
        query = Species.objects.filter(
            recordings__segmentations__classification_runs__status="completed",
            recordings__created_by=request.user
        )
        if project_id:
            try:
                query = query.filter(recordings__project_id=int(project_id))
            except (ValueError, TypeError):
                pass
        species_list = query.distinct()
    
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
        'parent_url': 'battycoda_app:classification_home',
        'parent_name': 'Classification',
        'th1': 'Species',
        'th2': 'Type',
        'th3': 'Classification Runs',
        'show_count': True,
        'action_text': 'Create Tasks',
        'action_icon': 'clipboard',
        'empty_message': 'No species with pending classification runs found.',
        'items': items
    }
    
    return render(request, "classification/select_entity.html", context)


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
            messages.error(request, "No completed classification runs for this species.")
            return redirect('battycoda_app:create_task_batches_for_species')
