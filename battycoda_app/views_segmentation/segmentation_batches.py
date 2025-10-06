"""
Views for managing batch segmentation operations.
"""
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models import Recording, Segmentation, Segment, Project

@login_required
def batch_segmentation_view(request):
    """Display a page for batch segmentation operations"""
    # Get user profile
    profile = request.user.profile

    # Filter recordings by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all recordings in their group
            recordings = Recording.objects.filter(group=profile.group).order_by("-created_at")
        else:
            # Regular user only sees their own recordings
            recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")
    else:
        # Fallback to showing only user's recordings if no group is assigned
        recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")

    # Apply project filter if provided
    project_id = request.GET.get('project')
    selected_project_id = None
    if project_id:
        try:
            project_id = int(project_id)
            recordings = recordings.filter(project_id=project_id)
            selected_project_id = project_id
        except (ValueError, TypeError):
            pass

    # Get available projects for the filter dropdown
    if profile.group:
        available_projects = Project.objects.filter(group=profile.group).order_by('name')
    else:
        available_projects = Project.objects.filter(created_by=request.user).order_by('name')

    context = {
        "recordings": recordings,
        "title": "Segmentations",
        "page_description": "Apply segmentation strategies to multiple recordings and monitor segmentation jobs.",
        "available_projects": available_projects,
        "selected_project_id": selected_project_id,
    }

    return render(request, "recordings/batch_segmentation.html", context)

@login_required
def segmentation_jobs_status_view(request):
    """API endpoint to get the status of all segmentation jobs for the user"""
    # Get user profile
    profile = request.user.profile

    # Filter segmentations by user and group permissions
    if profile.group and profile.is_current_group_admin:
        # Admin sees all segmentations in their group
        segmentations = Segmentation.objects.filter(recording__group=profile.group).order_by("-created_at")
    else:
        # Regular user only sees their own segmentations
        segmentations = Segmentation.objects.filter(created_by=request.user).order_by("-created_at")

    # Check if any segmentations have pending task status that we should update
    if segmentations.filter(status__in=["pending", "in_progress"]).exists():
        from celery.result import AsyncResult

        for segmentation in segmentations.filter(status__in=["pending", "in_progress"]):
            # Only process if there's a task_id
            if not segmentation.task_id:
                continue

            # Get task result
            result = AsyncResult(segmentation.task_id)

            if result.ready():
                if result.successful():
                    # Get result data
                    task_result = result.get()

                    # Success with segments
                    if task_result.get("status") == "success":
                        segments_created = task_result.get("segments_created", 0)
                        segmentation.status = "completed"
                        segmentation.progress = 100
                        segmentation.save()
                    else:
                        # Task returned error status
                        error_message = task_result.get("message", "Unknown error in segmentation task")
                        segmentation.status = "failed"
                        segmentation.save()
                else:
                    # Task failed with exception
                    error_info = str(result.result)
                    segmentation.status = "failed"
                    segmentation.save()

    # Format the segmentations for the response
    formatted_jobs = []
    for segmentation in segmentations[:20]:  # Limit to 20 most recent segmentations
        # Count segments for this specific segmentation
        segments_count = segmentation.segments.count()

        # Basic job information
        formatted_job = {
            "id": segmentation.id,
            "recording_id": segmentation.recording.id,
            "recording_name": segmentation.recording.name,
            "name": segmentation.name,
            "status": segmentation.status,
            "progress": segmentation.progress,
            "start_time": segmentation.created_at.isoformat(),
            "segments_created": segments_count,
            "algorithm_name": segmentation.algorithm.name if segmentation.algorithm else "Manual Import",
            "algorithm_type": segmentation.algorithm.get_algorithm_type_display()
            if segmentation.algorithm
            else "Manual",
            "view_url": reverse("battycoda_app:segmentation_detail", kwargs={"segmentation_id": segmentation.id}),
            "retry_url": reverse(
                "battycoda_app:auto_segment_recording", kwargs={"recording_id": segmentation.recording.id}
            ),
            "is_processing": segmentation.is_processing,
            "manually_edited": segmentation.manually_edited,
        }


        formatted_jobs.append(formatted_job)

    return JsonResponse({"success": True, "jobs": formatted_jobs})
