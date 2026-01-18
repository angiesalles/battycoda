"""
CRUD views for creating, editing, and deleting recordings.
"""

import logging
import os
import tempfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .audio.utils import get_audio_duration, split_audio_file
from .forms import RecordingForm
from .forms_edit import RecordingEditForm
from .models import Recording, Segment
from .models.user import UserProfile
from .utils_modules.cleanup import safe_remove_file

logger = logging.getLogger(__name__)


@login_required
def create_recording_view(request):
    """Handle creation of a new recording"""
    if request.method == "POST":
        form = RecordingForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Get user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # Check group
            if not profile.group:
                messages.error(request, "You must be assigned to a group to create a recording")
                return redirect("battycoda_app:create_recording")

            # Check if user wants to split long files
            split_long_files = request.POST.get("split_long_files") == "on"

            # Get the uploaded WAV file
            wav_file = request.FILES.get("wav_file")

            # Check duration and split if needed
            if split_long_files and wav_file:
                # Save uploaded file to temporary location to check duration
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    for chunk in wav_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                try:
                    # Check duration
                    duration = get_audio_duration(temp_file_path)

                    if duration > 60:
                        # Split the file
                        chunk_paths = split_audio_file(temp_file_path, chunk_duration_seconds=60)

                        recordings_created = []

                        # Get form data for creating chunks
                        original_name = form.cleaned_data["name"]
                        description = form.cleaned_data.get("description", "")
                        recorded_date = form.cleaned_data.get("recorded_date")
                        location = form.cleaned_data.get("location", "")
                        equipment = form.cleaned_data.get("equipment", "")
                        environmental_conditions = form.cleaned_data.get("environmental_conditions", "")
                        species = form.cleaned_data["species"]
                        project = form.cleaned_data["project"]

                        # Create a recording for each chunk
                        for i, chunk_path in enumerate(chunk_paths):
                            with open(chunk_path, "rb") as chunk_file:
                                chunk_file_name = os.path.basename(chunk_path)
                                chunk_django_file = SimpleUploadedFile(
                                    chunk_file_name, chunk_file.read(), content_type="audio/wav"
                                )

                                # Create fresh recording for each chunk
                                recording = Recording(
                                    name=f"{original_name} (Part {i + 1}/{len(chunk_paths)})",
                                    wav_file=chunk_django_file,
                                    description=description,
                                    recorded_date=recorded_date,
                                    location=location,
                                    equipment=equipment,
                                    environmental_conditions=environmental_conditions,
                                    species=species,
                                    project=project,
                                    created_by=request.user,
                                    group=profile.group,
                                )
                                recording.save()
                                recording.file_ready = True
                                recording.save(update_fields=["file_ready"])

                                recordings_created.append(recording)

                        # Clean up chunk files
                        for chunk_path in chunk_paths:
                            safe_remove_file(chunk_path, "audio chunk file")

                        # Clean up temp file
                        safe_remove_file(temp_file_path, "temporary upload file")

                        # Return success message
                        messages.success(
                            request,
                            f"Successfully created {len(recordings_created)} recordings from split file (original duration: {duration:.1f}s)",
                        )
                        return redirect("battycoda_app:recording_list")

                except (IOError, OSError) as e:
                    # If we can't check duration or split, fall back to normal processing
                    logger.debug(f"File splitting not possible, falling back to normal processing: {e}")
                finally:
                    # Clean up temp file
                    safe_remove_file(temp_file_path, "temporary upload file")

            # Normal processing (file <= 60s or splitting disabled or splitting failed)
            recording = form.save(commit=False)
            recording.created_by = request.user
            recording.group = profile.group

            # Save the recording first without marking as ready
            recording.save()

            # Now mark as ready for processing and save again
            recording.file_ready = True
            recording.save(update_fields=["file_ready"])

            # Check if AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Successfully created recording: {recording.name}",
                        "redirect_url": reverse(
                            "battycoda_app:recording_detail", kwargs={"recording_id": recording.id}
                        ),
                    }
                )

            messages.success(request, f"Successfully created recording: {recording.name}")
            return redirect("battycoda_app:recording_detail", recording_id=recording.id)
        else:
            # Return JSON response for AJAX requests
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": form.errors})

    else:
        form = RecordingForm(user=request.user)

    context = {
        "form": form,
    }

    return render(request, "recordings/create_recording.html", context)


@login_required
def edit_recording_view(request, recording_id):
    """Edit an existing recording"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission to edit this recording
    profile = request.user.profile
    if recording.created_by != request.user and (
        not profile.group or recording.group != profile.group or not profile.is_current_group_admin
    ):
        messages.error(request, "You don't have permission to edit this recording.")
        return redirect("battycoda_app:recording_list")

    if request.method == "POST":
        form = RecordingEditForm(request.POST, instance=recording, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated recording: {recording.name}")
            return redirect("battycoda_app:recording_detail", recording_id=recording.id)
    else:
        form = RecordingEditForm(instance=recording, user=request.user)

    context = {
        "form": form,
        "recording": recording,
    }

    return render(request, "recordings/edit_recording.html", context)


@login_required
def delete_recording_view(request, recording_id):
    """Delete a recording"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission to delete this recording
    profile = request.user.profile
    if recording.created_by != request.user and (
        not profile.group or recording.group != profile.group or not profile.is_current_group_admin
    ):
        messages.error(request, "You don't have permission to delete this recording.")
        return redirect("battycoda_app:recording_list")

    if request.method == "POST":
        # Delete segments first
        Segment.objects.filter(recording=recording).delete()
        recording_name = recording.name
        recording.delete()
        messages.success(request, f"Successfully deleted recording: {recording_name}")
        return redirect("battycoda_app:recording_list")

    context = {
        "recording": recording,
    }

    return render(request, "recordings/delete_recording.html", context)
