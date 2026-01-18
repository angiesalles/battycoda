"""
AJAX views for individual segment CRUD operations (create, edit, delete).
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.forms import SegmentForm
from battycoda_app.models import Segment, Segmentation


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
