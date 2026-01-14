"""
Views for managing individual recording segments (CRUD operations).
"""

import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.forms import SegmentForm
from battycoda_app.models import Recording, Segment, Segmentation, SpectrogramJob


def get_spectrogram_status(recording):
    """
    Get comprehensive spectrogram status for a recording.

    Returns:
        dict: Contains 'status', 'url', 'job', 'progress' information
    """
    try:
        # Check if recording has spectrogram file stored in database
        if recording.spectrogram_file:
            spectrogram_path = os.path.join(
                settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file
            )

            # Check if spectrogram file actually exists
            if os.path.exists(spectrogram_path) and os.path.getsize(spectrogram_path) > 0:
                return {
                    "status": "available",
                    "url": f"/media/spectrograms/recordings/{recording.spectrogram_file}",
                    "job": None,
                    "progress": 100,
                }

        # Check for existing jobs
        active_job = SpectrogramJob.objects.filter(recording=recording, status__in=["pending", "in_progress"]).first()

        if active_job:
            return {"status": "generating", "url": None, "job": active_job, "progress": active_job.progress}

        # Check for completed jobs with file
        completed_job = (
            SpectrogramJob.objects.filter(recording=recording, status="completed").order_by("-created_at").first()
        )

        if completed_job and completed_job.output_file_path and os.path.exists(completed_job.output_file_path):
            # Extract the relative URL from the full path
            relative_path = str(completed_job.output_file_path).replace(settings.MEDIA_ROOT, "").lstrip("/")
            return {"status": "available", "url": f"/media/{relative_path}", "job": completed_job, "progress": 100}

        # No spectrogram available, no active jobs
        return {"status": "not_available", "url": None, "job": None, "progress": 0}

    except Exception as e:
        return {"status": "error", "url": None, "job": None, "progress": 0, "error": str(e)}


@login_required
def segment_recording_view(request, segmentation_id=None):
    """View for segmenting - handles list, create, and detail views"""
    profile = request.user.profile

    # Handle different URL patterns
    if segmentation_id is None:
        # /segmentations/ - list view
        if request.path == "/segmentations/":
            return segmentation_list_view(request)
        # /segmentations/create/ - create view
        elif request.path == "/segmentations/create/":
            return create_segmentation_view(request)
        else:
            # Fallback for old recording-based URLs - extract recording_id from kwargs
            recording_id = request.resolver_match.kwargs.get("recording_id")
            if recording_id:
                return segment_recording_legacy_view(request, recording_id)
            else:
                return redirect("battycoda_app:segmentation_list")
    else:
        # /segmentations/<segmentation_id>/ - detail view
        return segmentation_detail_view(request, segmentation_id)


@login_required
def segment_recording_legacy_view(request, recording_id):
    """Legacy view for segmenting a recording (marking regions) - redirects to new URL"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Find most recent segmentation or create one
    active_segmentation = Segmentation.objects.filter(recording=recording).order_by("-created_at").first()

    if not active_segmentation:
        # No segmentation exists - redirect to create one
        return redirect("battycoda_app:create_segmentation", recording=recording.id)

    # Redirect to the new URL structure
    return redirect("battycoda_app:segmentation_detail", segmentation_id=active_segmentation.id)


@login_required
def segmentation_list_view(request):
    """List all segmentations available to the user"""
    profile = request.user.profile

    # Filter segmentations by user's permissions (exclude hidden recordings)
    if profile.group and profile.is_current_group_admin:
        segmentations = Segmentation.objects.filter(
            recording__group=profile.group,
            recording__hidden=False,  # Exclude hidden recordings
        ).order_by("-created_at")
    else:
        segmentations = Segmentation.objects.filter(
            recording__created_by=request.user,
            recording__hidden=False,  # Exclude hidden recordings
        ).order_by("-created_at")

    context = {
        "segmentations": segmentations,
    }
    return render(request, "segmentations/segmentation_list.html", context)


@login_required
def create_segmentation_view(request):
    """Create a new segmentation for a recording"""
    recording_id = request.GET.get("recording")
    if not recording_id:
        messages.error(request, "No recording specified for segmentation.")
        return redirect("battycoda_app:recording_list")

    recording = get_object_or_404(Recording, id=recording_id)

    # Check permissions
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to create segmentations for this recording.")
        return redirect("battycoda_app:recording_list")

    # For now, just create a default empty segmentation and redirect to it
    # TODO: Add a proper creation form later
    segmentation = Segmentation.objects.create(
        recording=recording, name=f"Segmentation for {recording.name}", created_by=request.user
    )

    messages.success(request, f"Created new segmentation for {recording.name}")
    return redirect("battycoda_app:segmentation_detail", segmentation_id=segmentation.id)


@login_required
def segmentation_detail_view(request, segmentation_id):
    """View for editing a specific segmentation (marking regions)"""
    segmentation = get_object_or_404(Segmentation, id=segmentation_id)
    recording = segmentation.recording  # This works through FK even if recording is hidden

    # Check if the user has permission to edit this segmentation
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to edit this segmentation.")
        return redirect("battycoda_app:segmentation_list")

    # No need to manage is_active field anymore - just use the current segmentation

    # Use this specific segmentation
    active_segmentation = segmentation
    segments_queryset = Segment.objects.filter(segmentation=active_segmentation).order_by("onset")

    # Add segmentation info to context
    segmentation_info = {
        "id": active_segmentation.id,
        "name": active_segmentation.name,
        "algorithm": active_segmentation.algorithm.name if active_segmentation.algorithm else "Manual",
        "created_at": active_segmentation.created_at,
        "manually_edited": active_segmentation.manually_edited,
    }

    # Load all segments for JavaScript (frontend handles filtering/pagination)
    # For very large segmentations, we limit to first 10000 segments to avoid memory issues
    all_segments = segments_queryset[:10000]
    segments_json = []
    for segment in all_segments:
        segments_json.append({"id": segment.id, "onset": segment.onset, "offset": segment.offset})

    # Get total segment count for context
    total_segments_count = segments_queryset.count()

    # Get all segmentations for the dropdown
    all_segmentations = Segmentation.objects.filter(recording=recording).order_by("-created_at")

    context = {
        "recording": recording,
        "segments_json": json.dumps(segments_json),
        "total_segments_count": total_segments_count,
        "active_segmentation": segmentation_info,
        "segmentation": segmentation,
        "all_segmentations": all_segmentations,
    }

    return render(request, "segmentations/segmentation_detail.html", context)


@login_required
def delete_segmentation_view(request, segmentation_id):
    """Delete a segmentation and all its segments"""
    segmentation = get_object_or_404(Segmentation, id=segmentation_id)
    recording = segmentation.recording

    # Check if the user has permission to delete this segmentation
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to delete this segmentation.")
        return redirect("battycoda_app:segmentation_list")

    if request.method == "POST":
        segmentation_name = segmentation.name
        recording_id = recording.id

        # Delete the segmentation (segments will be deleted via CASCADE)
        segmentation.delete()

        messages.success(request, f'Segmentation "{segmentation_name}" has been deleted.')
        return redirect("battycoda_app:recording_detail", recording_id=recording_id)

    # If GET request, show confirmation page (though we'll use JS confirmation instead)
    return redirect("battycoda_app:segmentation_detail", segmentation_id=segmentation_id)


@login_required
def add_segment_view(request, segmentation_id):
    """Add a segment to a segmentation via AJAX"""
    segmentation = get_object_or_404(Segmentation, id=segmentation_id)
    recording = segmentation.recording

    # Check if the user has permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = SegmentForm(request.POST, recording=recording)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.recording = recording
            segment.segmentation = segmentation
            segment.created_by = request.user
            segment.save(manual_edit=True)  # Mark as manually edited

            return JsonResponse({"success": True, "segment": segment.to_dict()})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


@login_required
def edit_segment_view(request, segmentation_id, segment_id):
    """Edit a segment via AJAX"""
    segment = get_object_or_404(Segment, id=segment_id)
    recording = segment.recording

    # Check if the user has permission
    profile = request.user.profile
    if segment.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = SegmentForm(request.POST, instance=segment, recording=recording)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.save(manual_edit=True)  # Mark as manually edited

            return JsonResponse({"success": True, "segment": segment.to_dict()})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)


@login_required
def delete_segment_view(request, segmentation_id, segment_id):
    """Delete a segment via AJAX"""
    segment = get_object_or_404(Segment, id=segment_id)
    recording = segment.recording

    # Check if the user has permission
    profile = request.user.profile
    if segment.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        # Get the segmentation to mark as manually edited
        segmentation = segment.segmentation
        if segmentation:
            segmentation.manually_edited = True
            segmentation.save()

        segment_id = segment.id
        segment.delete()
        return JsonResponse({"success": True, "segment_id": segment_id})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
