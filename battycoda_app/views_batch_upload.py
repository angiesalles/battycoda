"""
Views for handling batch uploads of recordings.
"""

import os
import tempfile
import traceback
import zipfile
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .audio.utils import process_pickle_file
from .forms import RecordingForm
from .models import Recording, Segment, Segmentation, UserProfile

# Set up logging

# Placeholder for future upload progress functionality

@login_required
def batch_upload_recordings_view(request):
    """Handle batch upload of recordings with optional pickle segmentation files from ZIP archives"""

    # Get user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Check if user has a group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to upload recordings")
        return redirect("battycoda_app:recording_list")

    if request.method == "POST":
        # Log the POST request

        # Create a form instance with submitted data
        form = RecordingForm(request.POST, request.FILES, user=request.user)

        # Process form for common metadata
        if form.is_valid():

            # Get common fields from the form but don't save yet
            species = form.cleaned_data.get("species")
            project = form.cleaned_data.get("project")
            description = form.cleaned_data.get("description")
            recorded_date = form.cleaned_data.get("recorded_date")
            location = form.cleaned_data.get("location")
            equipment = form.cleaned_data.get("equipment")
            environmental_conditions = form.cleaned_data.get("environmental_conditions")

            # Get uploaded zip files
            wav_zip = request.FILES.get("wav_zip")
            pickle_zip = request.FILES.get("pickle_zip")

            # Debug log information
            # WAV zip present: {wav_zip is not None}, Pickle zip present: {pickle_zip is not None}

            if not wav_zip:
                messages.error(request, "Please select a ZIP file with WAV recordings to upload")
                return redirect("battycoda_app:batch_upload_recordings")

            success_count = 0
            error_count = 0
            segmented_count = 0

            # Processing uploads

            # Create temporary directories for extracted files
            with tempfile.TemporaryDirectory() as wav_temp_dir, tempfile.TemporaryDirectory() as pickle_temp_dir:
                # Extract WAV files from zip
                wav_files = []
                try:
                    with zipfile.ZipFile(wav_zip, "r") as zip_ref:
                        # Extract all wav files - filtering out directories and duplicate paths
                        processed_files = set()  # Track files to avoid duplicates

                        # Debug: print contents of the ZIP
                        
                        for file_info in zip_ref.infolist():
                            # Skip directories, already processed files, and macOS metadata files
                            if (
                                file_info.filename.endswith("/")
                                or file_info.filename in processed_files
                                or os.path.basename(file_info.filename).startswith("._")
                            ):
                                # Skipping directory, duplicate, or macOS metadata file
                                continue

                            if file_info.filename.lower().endswith(".wav"):

                                zip_ref.extract(file_info, wav_temp_dir)
                                extracted_path = os.path.join(wav_temp_dir, file_info.filename)
                                wav_files.append(extracted_path)
                                processed_files.add(file_info.filename)

                except Exception as e:
                    messages.error(request, f"Failed to extract WAV ZIP file: {str(e)}")

                    return redirect("battycoda_app:batch_upload_recordings")

                # Extract pickle files if available
                pickle_files_dict = {}
                if pickle_zip:
                    try:
                        with zipfile.ZipFile(pickle_zip, "r") as zip_ref:
                            # Extract all pickle files - filtering out directories and duplicate paths
                            processed_files = set()  # Track files to avoid duplicates

                            for file_info in zip_ref.infolist():
                                # Skip directories, already processed files, and macOS metadata files
                                if (
                                    file_info.filename.endswith("/")
                                    or file_info.filename in processed_files
                                    or os.path.basename(file_info.filename).startswith("._")
                                ):
                                    continue

                                if file_info.filename.lower().endswith(".pickle"):
                                    zip_ref.extract(file_info, pickle_temp_dir)
                                    pickle_path = os.path.join(pickle_temp_dir, file_info.filename)
                                    # Store with basename as key for matching
                                    pickle_files_dict[os.path.basename(file_info.filename)] = pickle_path
                                    processed_files.add(file_info.filename)

                    except Exception as e:
                        messages.error(request, f"Failed to extract pickle ZIP file: {str(e)}")

                        # Continue with WAV files even if pickle extraction fails

                # Process each WAV file
                for wav_path in wav_files:
                    # Open the file for Django to save
                    with open(wav_path, "rb") as wav_file_obj:
                        # Create a Django file object
                        wav_file_name = os.path.basename(wav_path)
                        wav_file = SimpleUploadedFile(wav_file_name, wav_file_obj.read(), content_type="audio/wav")

                        with transaction.atomic():
                            # Create a Recording object for this file
                            file_name = Path(wav_file_name).stem  # Get file name without extension

                            # Use the file name directly as the recording name
                            recording_name = file_name

                            # Create the recording model instance
                            recording = Recording(
                                name=recording_name,  # Use file name as recording name
                                description=description,
                                wav_file=wav_file,
                                recorded_date=recorded_date,
                                location=location,
                                equipment=equipment,
                                environmental_conditions=environmental_conditions,
                                species=species,
                                project=project,
                                group=profile.group,
                                created_by=request.user,
                            )

                            # Save the recording
                            recording.save()

                            # Check if there's a matching pickle file
                            pickle_filename = f"{wav_file_name}.pickle"
                            pickle_path = pickle_files_dict.get(pickle_filename)

                            # Process pickle file if found
                            if pickle_path:
                                # Open and process the pickle file
                                with open(pickle_path, "rb") as pickle_file_obj:
                                    # Create a Django file object
                                    pickle_file = SimpleUploadedFile(
                                        pickle_filename,
                                        pickle_file_obj.read(),
                                        content_type="application/octet-stream",
                                    )

                                    # Process the pickle file
                                    onsets, offsets = process_pickle_file(pickle_file)

                                    # Mark all existing segmentations as inactive first
                                    Segmentation.objects.filter(recording=recording, is_active=True).update(
                                        is_active=False
                                    )

                                    # Create a new segmentation for this batch of segments
                                    segmentation = Segmentation.objects.create(
                                        recording=recording,
                                        name=f"Batch Upload {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                        algorithm=None,  # No algorithm for uploaded pickles
                                        status="completed",
                                        progress=100,
                                        is_active=True,
                                        manually_edited=False,
                                        created_by=request.user,
                                    )

                                    # Create segments from the onset/offset pairs
                                    segments_created = 0
                                    for i in range(len(onsets)):
                                        # Create segment name
                                        segment_name = f"Segment {i+1}"

                                        # Create and save the segment - linked to the new segmentation
                                        segment = Segment(
                                            recording=recording,
                                            segmentation=segmentation,
                                            name=segment_name,
                                            onset=onsets[i],
                                            offset=offsets[i],
                                            created_by=request.user,
                                        )
                                        segment.save(
                                            manual_edit=False
                                        )  # Don't mark as manually edited for automated uploads
                                        segments_created += 1

                                    # Update segment count on the segmentation
                                    segmentation.segments_created = segments_created
                                    segmentation.save()

                                    if segments_created > 0:
                                        segmented_count += 1
                            
                            success_count += 1

            # Upload complete

            # Success message
            if success_count > 0:
                success_msg = f"Successfully uploaded {success_count} recordings"
                if segmented_count > 0:
                    success_msg += f" with {segmented_count} segmented automatically from pickle files"
                messages.success(request, success_msg)

            # Error message
            if error_count > 0:
                error_msg = f"Failed to upload {error_count} recordings. See logs for details."
                messages.error(request, error_msg)

            # Redirect to the recordings list
            return redirect("battycoda_app:recording_list")
        else:

            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # GET request - display the form
        form = RecordingForm(user=request.user)

    context = {
        "form": form,
    }

    return render(request, "recordings/batch_upload_recordings.html", context)
