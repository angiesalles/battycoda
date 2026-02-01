"""
Views for listing and viewing recording details.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Recording
from .models.organization import Project
from .views_recordings_duplicates import has_duplicate_recordings
from .views_segmentation.spectrogram_data import get_spectrogram_status


@login_required
def recording_list_view(request):
    """Display list of all recordings for the user's group"""
    # Get user profile
    profile = request.user.profile

    # Filter recordings by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all recordings in their group
            recordings = Recording.objects.filter(group=profile.group).order_by("-created_at")

            # Check if there are recordings with missing sample rates
            has_missing_sample_rates = Recording.objects.filter(
                group=profile.group, sample_rate__isnull=True, file_ready=True
            ).exists()

            # Check if there are duplicate recordings
            has_duplicate_recordings_flag = has_duplicate_recordings(profile.group)
        else:
            # Regular user only sees their own recordings
            recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")
            has_missing_sample_rates = False
            has_duplicate_recordings_flag = False
    else:
        # Fallback to showing only user's recordings if no group is assigned
        recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")
        has_missing_sample_rates = False
        has_duplicate_recordings_flag = False

    # Apply project filter if provided
    project_id = request.GET.get("project")
    selected_project_id = None
    if project_id:
        try:
            project_id = int(project_id)
            recordings = recordings.filter(project_id=project_id)
            selected_project_id = project_id
        except (ValueError, TypeError):
            pass

    # Apply segmentation filter if provided
    segmentation_filter = request.GET.get("segmentation", "")
    if segmentation_filter == "yes":
        # Has at least one completed segmentation
        recordings = recordings.filter(segmentations__status="completed").distinct()
    elif segmentation_filter == "no":
        # Has no completed segmentations
        recordings = recordings.exclude(segmentations__status="completed").distinct()

    # Apply task batch filter if provided
    task_filter = request.GET.get("tasks", "")
    if task_filter == "yes":
        # Has at least one task (via segments)
        recordings = recordings.filter(segments__tasks__isnull=False).distinct()
    elif task_filter == "no":
        # Has no tasks
        recordings = recordings.exclude(segments__tasks__isnull=False).distinct()

    # Get available projects for the filter dropdown
    if profile.group:
        available_projects = Project.objects.filter(group=profile.group).order_by("name")
    else:
        available_projects = Project.objects.filter(created_by=request.user).order_by("name")

    context = {
        "recordings": recordings,
        "has_missing_sample_rates": has_missing_sample_rates,
        "has_duplicate_recordings": has_duplicate_recordings_flag,
        "available_projects": available_projects,
        "selected_project_id": selected_project_id,
        "selected_segmentation_filter": segmentation_filter,
        "selected_task_filter": task_filter,
    }

    return render(request, "recordings/recording_list.html", context)


@login_required
def recording_detail_view(request, recording_id):
    """Display details of a specific recording and its segments"""
    # Get the recording by ID
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission to view this recording
    # Either they created it or they're in the same group
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to view this recording.")
        return redirect("battycoda_app:recording_list")

    # Check spectrogram status and jobs
    spectrogram_info = get_spectrogram_status(recording)
    spectrogram_url = spectrogram_info.get("url")

    context = {
        "recording": recording,
        "spectrogram_info": spectrogram_info,
        "spectrogram_url": spectrogram_url,
    }

    return render(request, "recordings/recording_detail.html", context)
