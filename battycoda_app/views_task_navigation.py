from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from .models.task import Task, TaskBatch

# Stale lock timeout in minutes
STALE_LOCK_MINUTES = 30


def _filter_by_user_access(queryset, user):
    """Filter queryset by user's group or ownership."""
    profile = user.profile
    if profile.group:
        return queryset.filter(group=profile.group)
    return queryset.filter(created_by=user)


def _get_available_tasks(user):
    """Get undone tasks available to the user (not locked by others)."""
    stale_time = timezone.now() - timedelta(minutes=STALE_LOCK_MINUTES)
    tasks = Task.objects.filter(is_done=False).filter(
        Q(status="pending")
        | Q(in_progress_by=user)
        | Q(in_progress_since__lt=stale_time)
        | Q(in_progress_by__isnull=True)
    )
    return _filter_by_user_access(tasks, user)


@login_required
def get_next_task_from_batch_view(request, batch_id):
    """Get the next undone task from a specific batch and redirect to the annotation interface."""
    batch = get_object_or_404(TaskBatch, id=batch_id)
    profile = request.user.profile

    # Check if user has access to this batch
    has_access = (
        (profile.group and batch.group == profile.group) or batch.created_by == request.user
    )
    if not has_access:
        messages.error(request, "You don't have permission to annotate tasks from this batch.")
        return redirect("battycoda_app:task_batch_list")

    # Find the first undone task from this batch that's not locked by another user
    next_task = _get_available_tasks(request.user).filter(batch=batch).order_by("created_at").first()

    if next_task:
        # Redirect to the annotation interface with the task ID
        return redirect("battycoda_app:annotate_task", task_id=next_task.id)
    else:
        # No undone tasks found in this batch
        batch_name = batch.name
        messages.info(request, f'No undone tasks found in batch "{batch_name}". All tasks in this batch are completed.')

        # Store completed batch info in session to show toastr notification
        request.session["batch_completed"] = {"name": batch_name, "id": batch.id}

        return redirect("battycoda_app:task_batch_detail", batch_id=batch.id)


@login_required
def get_next_task_view(request):
    """Get the next undone task and redirect to the annotation interface,
    preferentially selecting from the same batch as the last completed task."""
    tasks_query = _get_available_tasks(request.user)

    # Filter by project if specified in URL parameter
    project_id = request.GET.get("project")
    if project_id:
        try:
            tasks_query = tasks_query.filter(project_id=int(project_id))
        except (ValueError, TypeError):
            pass  # Invalid project ID, ignore filter

    # Find the most recently completed task to check its batch
    recent_tasks = _filter_by_user_access(Task.objects.filter(is_done=True), request.user)
    recent_task = recent_tasks.order_by("-updated_at").first()

    # Check if previous task was the last one in a batch
    previous_batch = None
    if "batch_completed" in request.session:
        previous_batch = request.session.pop("batch_completed")

    # If we found a recent task and it has a batch, preferentially get tasks from that batch
    if recent_task and recent_task.batch:
        # Look for undone tasks from the same batch
        same_batch_tasks = tasks_query.filter(batch=recent_task.batch)
        next_task = same_batch_tasks.order_by("created_at").first()

        if next_task:
            # If coming from a completed batch AND it's a different batch, store that info for notification
            if previous_batch and previous_batch["id"] != recent_task.batch.id:
                request.session["batch_switch"] = {
                    "from_batch_name": previous_batch["name"],
                    "from_batch_id": previous_batch["id"],
                    "to_batch_name": recent_task.batch.name,
                    "to_batch_id": recent_task.batch.id,
                }
            return redirect("battycoda_app:annotate_task", task_id=next_task.id)

    # If no tasks from same batch, try to find tasks from same project
    task = None
    if recent_task and recent_task.batch and recent_task.batch.project:
        same_project_tasks = tasks_query.filter(batch__project=recent_task.batch.project)
        task = same_project_tasks.order_by("created_at").first()

    # Fall back to any task if no tasks found from same project
    if not task:
        task = tasks_query.order_by("created_at").first()

    if task:
        # If coming from a completed batch AND it's a different batch, store that info for notification
        if previous_batch and task.batch and previous_batch["id"] != task.batch.id:
            # Check if both batches are from the same project
            same_project = False
            if recent_task and recent_task.batch and task.batch:
                same_project = recent_task.batch.project_id == task.batch.project_id

            request.session["batch_switch"] = {
                "from_batch_name": previous_batch["name"],
                "from_batch_id": previous_batch["id"],
                "to_batch_name": task.batch.name,
                "to_batch_id": task.batch.id,
                "same_project": same_project,
                "project_name": task.batch.project.name if task.batch.project else None,
            }
        # Redirect to the annotation interface with the task ID
        return redirect("battycoda_app:annotate_task", task_id=task.id)
    else:
        # No undone tasks found
        messages.info(request, "No undone tasks found. All tasks are completed!")
        # Redirect to task batch list instead of non-existent task_list
        return redirect("battycoda_app:task_batch_list")


@login_required
def get_last_task_view(request):
    """Get the last task the user worked on (most recently updated) and redirect to it"""
    task = _filter_by_user_access(Task.objects.all(), request.user).order_by("-updated_at").first()

    if task:
        # Redirect to the annotation interface with the task ID
        return redirect("battycoda_app:annotate_task", task_id=task.id)
    else:
        # No tasks found
        messages.info(request, "No tasks found. Please create new tasks or task batches.")
        # Redirect to task batch list instead of non-existent task_list
        return redirect("battycoda_app:task_batch_list")


@login_required
def skip_to_next_batch_view(request, current_task_id):
    """Skip the current batch and go to the first task of the next batch with undone tasks."""
    current_task = get_object_or_404(Task, id=current_task_id)
    current_batch = current_task.batch

    if not current_batch:
        messages.warning(request, "This task is not part of a batch. Redirecting to next available task.")
        return redirect("battycoda_app:get_next_task")

    # Build query for batches with undone tasks, filtered by user access
    batches_query = _filter_by_user_access(
        TaskBatch.objects.filter(tasks__is_done=False).distinct(), request.user
    )

    # Exclude the current batch
    batches_query = batches_query.exclude(id=current_batch.id)

    # Prefer batches from the same project
    if current_batch.project:
        same_project_batch = batches_query.filter(project=current_batch.project).order_by("created_at").first()
        if same_project_batch:
            next_task = Task.objects.filter(batch=same_project_batch, is_done=False).order_by("created_at").first()
            if next_task:
                messages.info(request, f'Skipped to next batch: "{same_project_batch.name}"')
                return redirect("battycoda_app:annotate_task", task_id=next_task.id)

    # Fall back to any batch with undone tasks
    next_batch = batches_query.order_by("created_at").first()
    if next_batch:
        next_task = Task.objects.filter(batch=next_batch, is_done=False).order_by("created_at").first()
        if next_task:
            messages.info(request, f'Skipped to next batch: "{next_batch.name}"')
            return redirect("battycoda_app:annotate_task", task_id=next_task.id)

    # No other batches with undone tasks
    messages.info(
        request, f'No other batches with undone tasks found. Staying in current batch "{current_batch.name}".'
    )
    return redirect("battycoda_app:annotate_task", task_id=current_task_id)
