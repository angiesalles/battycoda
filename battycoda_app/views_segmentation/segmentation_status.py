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

    # Get task ID from session
    task_id = request.session.get(f"auto_segment_task_{recording_id}")

    if not task_id:
        # Try to get the segmentation from the database instead
        segmentation = Segmentation.objects.filter(recording_id=recording_id).first()

        if segmentation and segmentation.task_id:
            task_id = segmentation.task_id
        else:
            return JsonResponse(
                {"success": False, "status": "not_found", "message": "No active segmentation task found"}
            )

    try:
        from celery.result import AsyncResult

        # Get the segmentation from database
        segmentation = Segmentation.objects.filter(task_id=task_id).first()

        # Get task result
        result = AsyncResult(task_id)

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
                    if segmentation:
                        segmentation.status = "completed"
                        segmentation.progress = 100
                        segmentation.save()

                    # Clear task ID from session
                    if f"auto_segment_task_{recording_id}" in request.session:
                        del request.session[f"auto_segment_task_{recording_id}"]

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
                    if segmentation:
                        segmentation.status = "failed"
                        segmentation.save()

                    # Clear task ID from session
                    if f"auto_segment_task_{recording_id}" in request.session:
                        del request.session[f"auto_segment_task_{recording_id}"]

                    return JsonResponse({"success": False, "status": "failed", "message": error_message})
            else:
                # Task failed with exception
                error_info = str(result.result)

                # Update segmentation status
                if segmentation:
                    segmentation.status = "failed"
                    segmentation.save()

                # Clear task ID from session
                if f"auto_segment_task_{recording_id}" in request.session:
                    del request.session[f"auto_segment_task_{recording_id}"]

                return JsonResponse(
                    {"success": False, "status": "failed", "message": f"Segmentation task failed: {error_info}"}
                )
        else:
            # Task is still running
            # Update segmentation status if it exists
            if segmentation and segmentation.status != "in_progress":
                segmentation.status = "in_progress"
                segmentation.save()

            return JsonResponse(
                {"success": True, "status": "in_progress", "message": "Segmentation is still processing..."}
            )

    except Exception as e:
        return JsonResponse({"success": False, "status": "error", "message": f"Error checking task status: {str(e)}"})
