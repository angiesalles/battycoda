"""
Core views for handling recording CRUD operations.
"""
from .views_common import *
from .tasks import calculate_audio_duration
from .forms_edit import RecordingEditForm
from .models.organization import Project

# Set up logging

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
    
    context = {
        "recording": recording,
        "spectrogram_info": spectrogram_info,
    }

    return render(request, "recordings/recording_detail.html", context)

@login_required
def create_recording_view(request):
    """Handle creation of a new recording"""
    if request.method == "POST":
        form = RecordingForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Create the recording but don't save yet
            recording = form.save(commit=False)
            recording.created_by = request.user

            # Get user profile
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # Set group to user's current active group
            if profile.group:
                recording.group = profile.group
            else:
                # This is a critical issue - user must have a group
                messages.error(request, "You must be assigned to a group to create a recording")
                return redirect("battycoda_app:create_recording")

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
