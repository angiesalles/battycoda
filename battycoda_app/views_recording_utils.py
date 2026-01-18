"""
Utility views for recording operations (audio info recalculation, batch processing).
"""

import os

import soundfile as sf
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import Recording
from .tasks import calculate_audio_duration


@login_required
def recalculate_audio_info_view(request, recording_id):
    """Recalculate audio duration and sample rate for a recording (synchronously)"""
    # Get the recording by ID
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission to edit this recording
    profile = request.user.profile
    if recording.created_by != request.user and (
        not profile.group or recording.group != profile.group or not profile.is_current_group_admin
    ):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect("battycoda_app:recording_list")

    # Reset audio info fields and ensure file_ready is True
    recording.duration = None
    recording.sample_rate = None
    recording.file_ready = True
    recording.save(update_fields=["duration", "sample_rate", "file_ready"])

    try:
        # Check if file exists
        if not os.path.exists(recording.wav_file.path):
            messages.error(request, "Recording file not found.")
            return redirect("battycoda_app:recording_detail", recording_id=recording.id)

        # Extract audio information from file
        info = sf.info(recording.wav_file.path)

        # Update the recording
        recording.duration = info.duration
        recording.sample_rate = info.samplerate
        recording.save(update_fields=["duration", "sample_rate"])

        messages.success(request, "Audio information has been recalculated successfully.")
    except Exception as e:
        messages.error(request, f"Failed to recalculate audio information: {str(e)}")

    return redirect("battycoda_app:recording_detail", recording_id=recording.id)


@login_required
def process_missing_sample_rates(request):
    """Trigger sample rate calculation for all recordings missing this information"""
    # Check if user is an admin
    profile = request.user.profile
    if not profile.is_current_group_admin:
        messages.error(request, "Only administrators can perform this action.")
        return redirect("battycoda_app:recording_list")

    # Get user's group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to perform this action.")
        return redirect("battycoda_app:recording_list")

    # Find recordings without sample rates in user's group
    recordings_to_process = Recording.objects.filter(group=profile.group, sample_rate__isnull=True, file_ready=True)

    # Count how many were found
    count = recordings_to_process.count()

    if count == 0:
        messages.info(request, "No recordings need sample rate measurement.")
        return redirect("battycoda_app:recording_list")

    # Process each recording
    for recording in recordings_to_process:
        # Trigger the calculation task
        calculate_audio_duration.delay(recording.id)

    messages.success(request, f"Sample rate calculation started for {count} recordings. This may take a few moments.")
    return redirect("battycoda_app:recording_list")
