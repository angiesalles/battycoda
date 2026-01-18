"""
Views for checking segmentation task status.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models import Recording, Segmentation


@login_required
def auto_segment_status_view(request, recording_id):
    """Check the status of an auto-segmentation task"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    # Get the most recent in-progress or pending segmentation for this recording
    segmentation = (
        Segmentation.objects.filter(recording_id=recording_id, status__in=["in_progress", "pending"])
        .order_by("-created_at")
        .first()
    )

    if not segmentation or not segmentation.task_id:
        return JsonResponse({"success": False, "status": "not_found", "message": "No active segmentation task found"})

    try:
        from celery.result import AsyncResult

        # Get task result
        result = AsyncResult(segmentation.task_id)

        if result.ready():
            # Task is complete
            if result.successful():
                # Get result data
                task_result = result.get()

                # Success with segments
                if task_result.get("status") == "success":
                    segments_created = task_result.get("segments_created", 0)
                    message = f"Successfully created {segments_created} segments."

                    # Update segmentation status
                    segmentation.status = "completed"
                    segmentation.progress = 100
                    segmentation.save(update_fields=["status", "progress"])

                    # Prepare response with basic information
                    response_data = {
                        "success": True,
                        "status": "completed",
                        "message": message,
                        "segments_created": segments_created,
                        "result": task_result,
                    }

                    return JsonResponse(response_data)
                else:
                    # Task returned error status
                    error_message = task_result.get("message", "Unknown error in segmentation task")

                    # Update segmentation status
                    segmentation.status = "failed"
                    segmentation.save(update_fields=["status"])

                    return JsonResponse({"success": False, "status": "failed", "message": error_message})
            else:
                # Task failed with exception
                error_info = str(result.result)

                # Update segmentation status
                segmentation.status = "failed"
                segmentation.save(update_fields=["status"])

                return JsonResponse(
                    {"success": False, "status": "failed", "message": f"Segmentation task failed: {error_info}"}
                )
        else:
            # Task is still running
            if segmentation.status != "in_progress":
                segmentation.status = "in_progress"
                segmentation.save(update_fields=["status"])

            return JsonResponse(
                {"success": True, "status": "in_progress", "message": "Segmentation is still processing..."}
            )

    except Exception as e:
        return JsonResponse({"success": False, "status": "error", "message": f"Error checking task status: {str(e)}"})
