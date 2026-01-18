"""
Views for selecting recordings for segmentation.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse

from battycoda_app.models import Recording


@login_required
def select_recording_for_segmentation_view(request):
    """Display a page for selecting a recording to segment"""
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

    # Transform recordings to match the generalized template's expected format
    items = []
    for recording in recordings:
        items.append(
            {
                "id": recording.id,
                "name": recording.name,
                "type_name": f"{recording.species.name if recording.species else 'Unknown'} Recording",
                "created_at": recording.created_at,
                "detail_url": reverse("battycoda_app:recording_detail", kwargs={"recording_id": recording.id}),
                "action_url": reverse("battycoda_app:auto_segment_recording", kwargs={"recording_id": recording.id}),
            }
        )

    context = {
        "title": "Select Recording for Segmentation",
        "list_title": "Available Recordings",
        "info_message": "Select a recording to create a new segmentation.",
        "items": items,
        "th1": "Recording Name",
        "th2": "Species",
        "action_text": "Segment This Recording",
        "action_icon": "cut",
        "parent_url": "battycoda_app:batch_segmentation",
        "parent_name": "Segmentation Overview",
        "empty_message": "No recordings available. Upload a recording first.",
        "create_url": "battycoda_app:create_recording",
    }

    return render(request, "classification/select_entity.html", context)
