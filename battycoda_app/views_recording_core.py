"""
Core views for handling recording CRUD operations.
"""
import logging
import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile

from .audio.utils import get_audio_duration, split_audio_file
from .forms_edit import RecordingEditForm
from .models.organization import Project
from .tasks import calculate_audio_duration
from .utils_modules.cleanup import safe_remove_file
from .views_common import *

logger = logging.getLogger(__name__)

from .views_recordings_duplicates import has_duplicate_recordings

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
                group=profile.group,
                sample_rate__isnull=True,
                file_ready=True
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
        "has_missing_sample_rates": has_missing_sample_rates,
        "has_duplicate_recordings": has_duplicate_recordings_flag,
        "available_projects": available_projects,
        "selected_project_id": selected_project_id,
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

    # Import the spectrogram status function
    from .views_segmentation.segment_management import get_spectrogram_status
    
    # Check spectrogram status and jobs
    spectrogram_info = get_spectrogram_status(recording)
    spectrogram_url = spectrogram_info.get('url')
    
    context = {
        "recording": recording,
        "spectrogram_info": spectrogram_info,
        "spectrogram_url": spectrogram_url,
    }

    return render(request, "recordings/recording_detail.html", context)

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
            split_long_files = request.POST.get('split_long_files') == 'on'

            # Get the uploaded WAV file
            wav_file = request.FILES.get('wav_file')

            # Check duration and split if needed
            if split_long_files and wav_file:
                # Save uploaded file to temporary location to check duration
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
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
                        original_name = form.cleaned_data['name']
                        description = form.cleaned_data.get('description', '')
                        recorded_date = form.cleaned_data.get('recorded_date')
                        location = form.cleaned_data.get('location', '')
                        equipment = form.cleaned_data.get('equipment', '')
                        environmental_conditions = form.cleaned_data.get('environmental_conditions', '')
                        species = form.cleaned_data['species']
                        project = form.cleaned_data['project']

                        # Create a recording for each chunk
                        for i, chunk_path in enumerate(chunk_paths):
                            with open(chunk_path, 'rb') as chunk_file:
                                chunk_file_name = os.path.basename(chunk_path)
                                chunk_django_file = SimpleUploadedFile(
                                    chunk_file_name,
                                    chunk_file.read(),
                                    content_type='audio/wav'
                                )

                                # Create fresh recording for each chunk
                                recording = Recording(
                                    name=f"{original_name} (Part {i+1}/{len(chunk_paths)})",
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
                            f"Successfully created {len(recordings_created)} recordings from split file (original duration: {duration:.1f}s)"
                        )
                        return redirect("battycoda_app:recording_list")

                except (IOError, OSError) as e:
                    # If we can't check duration or split, fall back to normal processing
                    logger.debug(f"File splitting not possible, falling back to normal processing: {e}")
                finally:
                    # Clean up temp file
                    safe_remove_file(temp_file_path, "temporary upload file")

            # Normal processing (file ≤ 60s or splitting disabled or splitting failed)
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

    # Import the task function and run it synchronously
    import os
    import soundfile as sf
    
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
    recordings_to_process = Recording.objects.filter(
        group=profile.group, 
        sample_rate__isnull=True,
        file_ready=True
    )
    
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
