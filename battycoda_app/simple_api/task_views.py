"""
Task management API views for task batches and annotation.
"""

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import Task, TaskBatch
from ..models.classification import CallProbability, ClassificationResult, ClassificationRun
from ..utils_modules.validation import get_int_param
from .auth import api_key_required

# --- Helper functions to reduce duplication ---


def get_task_batch_for_user(batch_id, user):
    """
    Get a TaskBatch by ID with permission checking.
    Returns (batch, None) on success, or (None, error_response) on failure.
    """
    user_group = user.profile.group

    try:
        if user_group and user.profile.is_current_group_admin:
            return TaskBatch.objects.get(id=batch_id, group=user_group), None
        elif user_group:
            return TaskBatch.objects.get(Q(id=batch_id) & (Q(created_by=user) | Q(group=user_group))), None
        else:
            return TaskBatch.objects.get(id=batch_id, created_by=user), None
    except TaskBatch.DoesNotExist:
        return None, JsonResponse(
            {"success": False, "error": f"Task batch with ID {batch_id} not found or not accessible"}, status=404
        )


def get_task_batches_queryset(user):
    """Get TaskBatch queryset filtered by user permissions."""
    user_group = user.profile.group

    if user_group and user.profile.is_current_group_admin:
        return TaskBatch.objects.filter(group=user_group)
    elif user_group:
        return TaskBatch.objects.filter(Q(created_by=user) | Q(group=user_group))
    else:
        return TaskBatch.objects.filter(created_by=user)


def serialize_task_batch(batch, include_progress=True):
    """Convert a TaskBatch to a dict for JSON response."""
    data = {
        "id": batch.id,
        "name": batch.name,
        "description": batch.description,
        "species_name": batch.species.name if batch.species else None,
        "species_id": batch.species.id if batch.species else None,
        "project_name": batch.project.name if batch.project else None,
        "project_id": batch.project.id if batch.project else None,
        "created_by": batch.created_by.username,
        "created_at": batch.created_at.isoformat(),
    }

    if include_progress:
        total_tasks = batch.tasks.count()
        completed_tasks = batch.tasks.filter(is_done=True).count()
        data["total_tasks"] = total_tasks
        data["completed_tasks"] = completed_tasks
        data["progress_percentage"] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return data


def serialize_task(task):
    """Convert a Task to a dict for JSON response."""
    return {
        "id": task.id,
        "onset": task.onset,
        "offset": task.offset,
        "label": task.label,
        "classification_result": task.classification_result,
        "confidence": task.confidence,
        "is_done": task.is_done,
        "status": task.status,
        "annotated_by": task.annotated_by.username if task.annotated_by else None,
        "annotated_at": task.annotated_at.isoformat() if task.annotated_at else None,
    }


# --- API views ---


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_create_task_batch(request, run_id):
    """Create task batch from completed classification"""
    user = request.api_user
    user_group = user.profile.group

    if not user_group:
        return JsonResponse(
            {"success": False, "error": "User must be assigned to a group to create task batches"}, status=400
        )

    # Get the classification run
    try:
        run = ClassificationRun.objects.get(id=run_id, group=user_group)
    except ClassificationRun.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": f"Classification run with ID {run_id} not found or not accessible"},
            status=404,
        )

    if run.status != "completed":
        return JsonResponse(
            {"success": False, "error": "Classification run must be completed before creating task batch"},
            status=400,
        )

    # Get parameters
    name = request.POST.get("name")
    description = request.POST.get("description", "")
    confidence_threshold = request.POST.get("confidence_threshold")

    if not name:
        return JsonResponse({"success": False, "error": "Task batch name is required"}, status=400)

    # Parse confidence threshold
    max_confidence = None
    if confidence_threshold:
        try:
            max_confidence = float(confidence_threshold)
            if max_confidence < 0 or max_confidence > 1:
                raise ValueError("Confidence threshold must be between 0 and 1")
        except ValueError as e:
            return JsonResponse({"success": False, "error": f"Invalid confidence threshold: {str(e)}"}, status=400)

    # Create task batch using transaction
    recording = run.segmentation.recording

    with transaction.atomic():
        # Create the task batch
        task_batch = TaskBatch.objects.create(
            name=name,
            description=description,
            created_by=user,
            wav_file_name=recording.wav_file.name if recording.wav_file else "",
            wav_file=recording.wav_file,
            species=recording.species,
            project=recording.project,
            group=user_group,
            classification_run=run,
        )

        # Get all classification results from this run
        results = ClassificationResult.objects.filter(classification_run=run)

        tasks_created = 0
        for result in results:
            segment = result.segment

            # Skip segments that already have tasks
            if hasattr(segment, "task") and segment.task:
                continue

            # Get the highest probability call type
            top_probability = (
                CallProbability.objects.filter(classification_result=result)
                .select_related("call")
                .order_by("-probability")
                .first()
            )

            # Skip if confidence threshold is set and this result's confidence is too high
            if max_confidence is not None and top_probability and top_probability.probability > max_confidence:
                continue

            # Skip if call object is missing (broken foreign key)
            if top_probability and not top_probability.call:
                continue

            # Create a task for this segment
            predicted_call = top_probability.call.short_name if top_probability else None
            confidence = top_probability.probability if top_probability else 0.0

            Task.objects.create(
                wav_file_name=task_batch.wav_file_name,
                onset=segment.onset,
                offset=segment.offset,
                species=task_batch.species,
                project=task_batch.project,
                batch=task_batch,
                classification_result=predicted_call,
                confidence=confidence,
                created_by=user,
                group=user_group,
                source_segment=segment,
            )

            tasks_created += 1

    return JsonResponse(
        {
            "success": True,
            "message": "Task batch created successfully",
            "task_batch": {
                "id": task_batch.id,
                "name": task_batch.name,
                "description": task_batch.description,
                "species_name": task_batch.species.name if task_batch.species else None,
                "project_name": task_batch.project.name if task_batch.project else None,
                "total_tasks": tasks_created,
                "created_at": task_batch.created_at.isoformat(),
            },
        }
    )


@require_http_methods(["GET"])
@api_key_required
def simple_task_batches_list(request):
    """List existing task batches"""
    batches = get_task_batches_queryset(request.api_user).order_by("-created_at")

    # Apply project filter if provided
    project_id = request.GET.get("project_id")
    if project_id:
        try:
            batches = batches.filter(project_id=int(project_id))
        except (ValueError, TypeError):
            return JsonResponse({"success": False, "error": "Invalid project_id format"}, status=400)

    batches_data = [serialize_task_batch(batch) for batch in batches]
    return JsonResponse({"success": True, "task_batches": batches_data, "count": len(batches_data)})


@require_http_methods(["GET"])
@api_key_required
def simple_task_batch_tasks(request, batch_id):
    """List tasks in a batch for annotation"""
    batch, error_response = get_task_batch_for_user(batch_id, request.api_user)
    if error_response:
        return error_response

    # Get tasks with optional filtering
    tasks = batch.tasks.order_by("id")

    # Apply call type filter if provided
    call_type = request.GET.get("call_type")
    if call_type and call_type != "all":
        tasks = tasks.filter(
            Q(label=call_type)
            | Q(label__isnull=True, classification_result=call_type)
            | Q(label="", classification_result=call_type)
        )

    # Simple pagination
    limit = get_int_param(request, "limit", default=50, min_val=1, max_val=1000)
    offset = get_int_param(request, "offset", default=0, min_val=0)

    total_tasks = tasks.count()
    tasks_page = tasks[offset : offset + limit]
    tasks_data = [serialize_task(task) for task in tasks_page]

    # Build batch info with available call types
    batch_data = serialize_task_batch(batch, include_progress=False)
    if batch.species:
        batch_data["available_call_types"] = list(batch.species.calls.values_list("short_name", flat=True))
    else:
        batch_data["available_call_types"] = []

    return JsonResponse(
        {
            "success": True,
            "task_batch": batch_data,
            "tasks": tasks_data,
            "pagination": {
                "total": total_tasks,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total_tasks,
                "has_previous": offset > 0,
            },
        }
    )
