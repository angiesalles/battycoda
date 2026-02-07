"""
Views for detecting and managing duplicate recordings.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from .models.recording import Recording


@login_required
def detect_duplicate_recordings_view(request):
    """Show list of duplicate recordings for review"""
    # Check if user is an admin
    profile = request.user.profile
    if not profile.is_current_group_admin:
        messages.error(request, "Only administrators can perform this action.")
        return redirect("battycoda_app:recording_list")

    # Get user's group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to perform this action.")
        return redirect("battycoda_app:recording_list")

    # Get all recordings in the group
    recordings = Recording.objects.filter(group=profile.group)

    # Find duplicates based on recording name and duration
    # First, we'll group them by name and duration and count occurrences
    duplicate_groups = (
        recordings.exclude(duration__isnull=True)  # Skip recordings without duration
        .values("name", "duration")  # Group by name and duration
        .annotate(count=Count("id"))  # Count occurrences
        .filter(count__gt=1)  # Keep only groups with more than one recording
    )

    # Get the actual recording objects for each duplicate group
    duplicate_recordings = []
    for group in duplicate_groups:
        recordings_in_group = Recording.objects.filter(
            group=profile.group, name=group["name"], duration=group["duration"]
        ).order_by("-created_at")  # Most recent first

        duplicate_recordings.append(
            {
                "name": group["name"],
                "duration": group["duration"],
                "count": group["count"],
                "recordings": recordings_in_group,
            }
        )

    context = {
        "duplicate_recordings": duplicate_recordings,
        "total_duplicate_count": sum(group["count"] - 1 for group in duplicate_groups),
    }

    return render(request, "recordings/duplicate_recordings.html", context)


@login_required
def remove_duplicate_recordings(request):
    """Remove duplicate recordings, keeping only the most recent version"""
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("battycoda_app:recording_list")

    # Check if user is an admin
    profile = request.user.profile
    if not profile.is_current_group_admin:
        messages.error(request, "Only administrators can perform this action.")
        return redirect("battycoda_app:recording_list")

    # Get user's group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to perform this action.")
        return redirect("battycoda_app:recording_list")

    # Queue the background task
    from .tasks import remove_duplicate_recordings_task

    remove_duplicate_recordings_task.delay(profile.group.id, request.user.id)

    messages.info(
        request,
        "Duplicate removal has been started in the background. "
        "You will receive a notification when it completes.",
    )

    return redirect("battycoda_app:recording_list")


def has_duplicate_recordings(group):
    """Check if a group has any duplicate recordings"""
    duplicates_exist = (
        Recording.objects.filter(group=group)
        .exclude(duration__isnull=True)
        .values("name", "duration")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
        .exists()
    )

    return duplicates_exist
