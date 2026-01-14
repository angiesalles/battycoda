import hashlib
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models.task import Task
from .utils_modules.path_utils import convert_path_to_os_specific


@login_required
def task_annotation_view(request, task_id):
    """Show the annotation interface for a specific task"""
    # Get the task - allow group members to access tasks from the same group
    task = get_object_or_404(Task, id=task_id)

    # Check if user has permission to view this task
    if task.created_by != request.user and (not request.user.profile.group or task.group != request.user.profile.group):
        messages.error(request, "You don't have permission to view this task.")
        return redirect("battycoda_app:task_batch_list")

    # Check if someone else is working on this task
    if task.in_progress_by and task.in_progress_by != request.user and task.status == "in_progress":
        # Check if the task has been in progress for more than 30 minutes (stale lock)
        from datetime import timedelta

        if task.in_progress_since and timezone.now() - task.in_progress_since > timedelta(minutes=30):
            # Lock is stale, allow taking over
            messages.warning(
                request,
                f"User {task.in_progress_by.username} was working on this task but their session appears to be stale. "
                f"You can now work on it.",
            )
        else:
            messages.warning(
                request,
                f"User {task.in_progress_by.username} is currently working on this task (started {task.in_progress_since.strftime('%H:%M')}). "
                f"Your changes may conflict with theirs.",
            )

    # Handle task update if form submitted
    if request.method == "POST":
        # Check if the "mark as done" button was clicked
        if "mark_done" in request.POST:
            label = request.POST.get("type_call", "")
            # "Other" option has been removed

            # Update the task
            task.label = label
            task.is_done = True
            task.status = "done"
            task.annotated_by = request.user
            task.annotated_at = timezone.now()
            # Clear in-progress tracking
            task.in_progress_by = None
            task.in_progress_since = None
            task.save()

            # We don't need to show a success message for every task completion
            # - it creates too many notifications

            # Redirect to the next task
            return redirect("battycoda_app:get_next_task")

    # Mark task as in progress when user opens it (for GET requests)
    if task.status == "pending" or (task.in_progress_by != request.user and task.status == "in_progress"):
        task.status = "in_progress"
        task.in_progress_by = request.user
        task.in_progress_since = timezone.now()
        task.save()

    # Get hash of the wav file for validation
    # Extract the wav file information from the task
    wav_file_name = task.wav_file_name
    species = task.species

    # Path to the WAV file - check if it's in the media directory (uploaded file)
    if task.batch and task.batch.wav_file:
        # Get the path from the uploaded file in the batch
        wav_url = task.batch.wav_file.url
        full_path = task.batch.wav_file.path
        os_path = full_path
    else:
        # Assume the path is based on the project structure (old way)
        full_path = os.path.join("home", request.user.username, species, task.project, wav_file_name)
        os_path = convert_path_to_os_specific(full_path)
        wav_url = f"/{full_path}"

    # Create hash
    file_hash = hashlib.md5(os_path.encode()).hexdigest()

    # Set up onset and offset as a "call"
    # In our case, we'll treat each task as one "call"
    total_calls = 1

    # Get call types from the database (preferred) or fall back to text file
    call_types = []
    call_descriptions = {}  # To store full descriptions for tooltips

    # First, get the species object directly from the task's species field
    species_obj = task.species

    # If the task has a pre-selected label from classification, put it first in the list
    if task.label:
        call_types.append(task.label)
        call_descriptions[task.label] = "Automatic classification result"

    # Get call types from the species
    # Get calls from the database
    calls = species_obj.calls.all()
    if calls.exists():
        for call in calls:
            # Skip if this call type was already added from the task label
            if call.short_name in call_types:
                continue

            call_types.append(call.short_name)
            # Use long_name as the description if available
            description = call.long_name if call.long_name else ""
            call_descriptions[call.short_name] = description

    # If no call types were loaded from the database
    if not call_types:
        # Add a default "Unknown" call type to ensure the interface has at least one option
        call_types.append("Unknown")
        call_descriptions["Unknown"] = "Unspecified call type"

    # Check if HDF5 spectrogram file exists for the recording
    from .models.recording import Recording

    try:
        recording = Recording.objects.get(wav_file=task.wav_file_name)
        if not recording.spectrogram_file:
            messages.error(
                request,
                "Spectrogram file is missing for this recording. Please contact an administrator to generate it.",
            )
            return redirect("battycoda_app:task_batch_list")

        # Check if HDF5 file exists on disk
        base_name = recording.spectrogram_file.replace(".png", "").replace(".h5", "")
        spectrogram_filename = f"{base_name}.h5"
        output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
        h5_path = os.path.join(output_dir, spectrogram_filename)

        if not os.path.exists(h5_path):
            messages.error(request, f"Spectrogram HDF5 file does not exist on disk. Expected at: {h5_path}")
            return redirect("battycoda_app:task_batch_list")
    except Recording.DoesNotExist:
        messages.error(request, f"Recording not found for task. WAV file: {task.wav_file_name}")
        return redirect("battycoda_app:task_batch_list")

    # Get pre-generated spectrogram URLs

    # Create cache paths for spectrograms
    spectrogram_urls = {}
    for channel in [0, 1]:
        for is_overview in [True, False]:
            # Create args for the spectrogram
            spectrogram_args = {
                "call": "0",
                "channel": str(channel),
                "numcalls": "1",
                "hash": file_hash,
                "overview": "1" if is_overview else "0",
                "contrast": "4.0",
            }

            # Add onset/offset to args
            spectrogram_args["onset"] = str(task.onset)
            spectrogram_args["offset"] = str(task.offset)

            # Create a URL for the spectrogram (that will be handled by spectrogram_view)
            spectrogram_url = f"/spectrogram/?wav_path={full_path}&call=0&channel={channel}&numcalls=1&hash={file_hash}&overview={'1' if is_overview else '0'}&contrast=4.0&onset={task.onset}&offset={task.offset}"

            # Store in the dictionary with a descriptive key
            key = f"channel_{channel}_{'overview' if is_overview else 'detail'}"
            spectrogram_urls[key] = spectrogram_url

    # Calculate midpoint time for axis
    midpoint_time = (task.onset + task.offset) / 2

    # Get window sizes for the spectrogram
    from .audio.utils import get_spectrogram_ticks, normal_hwin, overview_hwin

    normal_window_size = normal_hwin(task.species)
    overview_window_size = overview_hwin(task.species)

    # Get sample rate from the task
    sample_rate = task.get_sample_rate()

    # Generate tick marks for the spectrogram using our utility function
    tick_data = get_spectrogram_ticks(
        task, sample_rate=sample_rate, normal_window_size=normal_window_size, overview_window_size=overview_window_size
    )

    # Extract the tick data
    x_ticks_detail = tick_data["x_ticks_detail"]
    x_ticks_overview = tick_data["x_ticks_overview"]
    y_ticks = tick_data["y_ticks"]

    # Check if there's batch switch data in the session (only when coming from a different batch)
    batch_switch_data = None
    if "batch_switch" in request.session:
        batch_switch_data = request.session.pop("batch_switch")

    # Create context for the template
    context = {
        "task": task,
        "username": request.user.username,
        "species": species,
        "species_obj": species_obj,  # Add the species object to the context
        "wav_path": wav_file_name,
        "full_path": full_path,
        "wav_url": wav_url,
        "file_hash": file_hash,
        "total_calls": total_calls,
        "call_types": call_types,
        "call_descriptions": call_descriptions,
        "onset": task.onset,
        "offset": task.offset,
        "midpoint_time": midpoint_time,  # Add midpoint time for x-axis
        "spectrogram_urls": spectrogram_urls,  # Add pre-generated spectrogram URLs
        "normal_hwin": normal_window_size,  # Add window size for time axis in milliseconds
        "overview_hwin": overview_window_size,  # Add overview window size
        # Add tick mark data
        "x_ticks_detail": x_ticks_detail,
        "x_ticks_overview": x_ticks_overview,
        "y_ticks": y_ticks,
        # Add batch switch data for notification
        "batch_switch_data": batch_switch_data,
    }

    # Return the annotation interface
    return render(request, "tasks/annotate_task.html", context)
