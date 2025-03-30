"""
Utility functions for batch audio processing in BattyCoda.
"""

import os
import tempfile
import traceback
import zipfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.utils import timezone

from .utils import process_pickle_file

# Configure logging

def process_batch_upload(wav_zip, pickle_zip, form_data, user, group):
    """
    Process a batch upload of WAV files and optional pickle files

    Args:
        wav_zip: ZIP file containing WAV files
        pickle_zip: ZIP file containing pickle files (optional)
        form_data: Form data with metadata for recordings
        user: User object creating the recordings
        group: Group object to assign recordings to

    Returns:
        dict: Results of the batch upload process
    """
    # Import here to avoid circular imports
    from battycoda_app.models import Recording, Segment, Segmentation

    success_count = 0
    error_count = 0
    segmented_count = 0

    # Get metadata from form data
    species = form_data.get("species")
    project = form_data.get("project")
    description = form_data.get("description")
    recorded_date = form_data.get("recorded_date")
    location = form_data.get("location")
    equipment = form_data.get("equipment")
    environmental_conditions = form_data.get("environmental_conditions")

    # Create temporary directories for extracted files
    with tempfile.TemporaryDirectory() as wav_temp_dir, tempfile.TemporaryDirectory() as pickle_temp_dir:
        # Extract WAV files from zip
        wav_files = []
        try:
            with zipfile.ZipFile(wav_zip, "r") as zip_ref:
                # Extract all wav files
                for file_info in zip_ref.infolist():
                    if file_info.filename.lower().endswith(".wav"):
                        zip_ref.extract(file_info, wav_temp_dir)
                        wav_files.append(os.path.join(wav_temp_dir, file_info.filename))

        except Exception as e:

            return {
                "success_count": 0,
                "error_count": 1,
                "segmented_count": 0,
                "error": f"Failed to extract WAV ZIP file: {str(e)}",
            }

        # Extract pickle files if available
        pickle_files_dict = {}
        if pickle_zip:
            with zipfile.ZipFile(pickle_zip, "r") as zip_ref:
                # Extract all pickle files
                for file_info in zip_ref.infolist():
                    if file_info.filename.lower().endswith(".pickle"):
                        zip_ref.extract(file_info, pickle_temp_dir)
                        pickle_path = os.path.join(pickle_temp_dir, file_info.filename)
                        # Store with basename as key for matching
                        pickle_files_dict[os.path.basename(file_info.filename)] = pickle_path

        # Process each WAV file
        for wav_path in wav_files:
            try:
                # Open the file for Django to save
                with open(wav_path, "rb") as wav_file_obj:
                    # Create a Django file object
                    wav_file_name = os.path.basename(wav_path)
                    wav_file = SimpleUploadedFile(wav_file_name, wav_file_obj.read(), content_type="audio/wav")

                    with transaction.atomic():

                        # Create a Recording object for this file
                        file_name = Path(wav_file_name).stem  # Get file name without extension
                        recording = Recording(
                            name=file_name,  # Use file name as recording name
                            description=description,
                            wav_file=wav_file,
                            recorded_date=recorded_date,
                            location=location,
                            equipment=equipment,
                            environmental_conditions=environmental_conditions,
                            species=species,
                            project=project,
                            group=group,
                            created_by=user,
                        )

                        # Save the recording
                        recording.save()

                        # Check if there's a matching pickle file
                        pickle_filename = f"{wav_file_name}.pickle"
                        pickle_path = pickle_files_dict.get(pickle_filename)

                        # Process pickle file if found
                        if pickle_path:
                            try:

                                # Open and process the pickle file
                                with open(pickle_path, "rb") as pickle_file_obj:
                                    # Create a Django file object
                                    pickle_file = SimpleUploadedFile(
                                        pickle_filename, pickle_file_obj.read(), content_type="application/octet-stream"
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
                                        created_by=user,
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
                                            created_by=user,
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
                                        # Created segments for recording
                            except Exception:
                                # Exception during pickle processing or segment creation
                                segmented_count = segmented_count

                        success_count += 1
            except Exception:
                # Exception during WAV processing
                error_count += 1

    # Return the results
    result = {"success_count": success_count, "error_count": error_count, "segmented_count": segmented_count}

    return result
