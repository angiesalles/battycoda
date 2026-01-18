"""
File processing utilities for batch upload - handles WAV files and recordings creation.
"""

import os
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

from ..audio.utils import get_audio_duration, process_pickle_file, split_audio_file
from ..models import Recording, Segment, Segmentation
from ..utils_modules.cleanup import safe_remove_file


def process_wav_with_splitting(wav_path, metadata, user, profile):
    """
    Process a WAV file, splitting it into chunks if longer than 60 seconds.

    Args:
        wav_path: Path to the WAV file
        metadata: Dict with keys: species, project, recorded_date, location,
                  equipment, environmental_conditions
        user: The Django user creating the recordings
        profile: User's profile (for group)

    Returns:
        Tuple of (recordings_created_count, was_split)
    """
    file_name = Path(os.path.basename(wav_path)).stem

    try:
        duration = get_audio_duration(wav_path)

        if duration > 60:
            chunk_paths = split_audio_file(wav_path, chunk_duration_seconds=60)
            recordings_created = 0

            for i, chunk_path in enumerate(chunk_paths):
                with open(chunk_path, "rb") as chunk_file_obj:
                    chunk_file_name = os.path.basename(chunk_path)
                    chunk_file = SimpleUploadedFile(chunk_file_name, chunk_file_obj.read(), content_type="audio/wav")

                    with transaction.atomic():
                        chunk_recording_name = f"{file_name} (Part {i + 1}/{len(chunk_paths)})"

                        recording = Recording(
                            name=chunk_recording_name,
                            wav_file=chunk_file,
                            recorded_date=metadata["recorded_date"],
                            location=metadata["location"],
                            equipment=metadata["equipment"],
                            environmental_conditions=metadata["environmental_conditions"],
                            species=metadata["species"],
                            project=metadata["project"],
                            group=profile.group,
                            created_by=user,
                        )
                        recording.save()
                        recording.file_ready = True
                        recording.save(update_fields=["file_ready"])
                        recordings_created += 1

            # Clean up chunk files
            for chunk_path in chunk_paths:
                safe_remove_file(chunk_path, "audio chunk file")

            return recordings_created, True

    except Exception:
        # If we can't check duration or split fails, return None to signal fallback
        pass

    return None, False


def create_recording_from_wav(wav_path, metadata, user, profile):
    """
    Create a single recording from a WAV file.

    Args:
        wav_path: Path to the WAV file
        metadata: Dict with keys: species, project, recorded_date, location,
                  equipment, environmental_conditions
        user: The Django user creating the recording
        profile: User's profile (for group)

    Returns:
        The created Recording object
    """
    wav_file_name = os.path.basename(wav_path)
    file_name = Path(wav_file_name).stem

    with open(wav_path, "rb") as wav_file_obj:
        wav_file = SimpleUploadedFile(wav_file_name, wav_file_obj.read(), content_type="audio/wav")

        with transaction.atomic():
            recording = Recording(
                name=file_name,
                wav_file=wav_file,
                recorded_date=metadata["recorded_date"],
                location=metadata["location"],
                equipment=metadata["equipment"],
                environmental_conditions=metadata["environmental_conditions"],
                species=metadata["species"],
                project=metadata["project"],
                group=profile.group,
                created_by=user,
            )
            recording.save()
            recording.file_ready = True
            recording.save(update_fields=["file_ready"])

    return recording


def create_segmentation_from_pickle(recording, pickle_path, pickle_filename, user):
    """
    Create a segmentation and segments from a pickle file.

    Args:
        recording: The Recording object to attach segments to
        pickle_path: Path to the pickle file
        pickle_filename: Name of the pickle file
        user: The Django user creating the segmentation

    Returns:
        Number of segments created
    """
    with open(pickle_path, "rb") as pickle_file_obj:
        pickle_file = SimpleUploadedFile(
            pickle_filename,
            pickle_file_obj.read(),
            content_type="application/octet-stream",
        )

        onsets, offsets = process_pickle_file(pickle_file)

        segmentation = Segmentation.objects.create(
            recording=recording,
            name="Batch Upload",
            algorithm=None,
            status="completed",
            progress=100,
            manually_edited=False,
            created_by=user,
        )

        segments_created = 0
        for i in range(len(onsets)):
            segment = Segment(
                recording=recording,
                segmentation=segmentation,
                name=f"Segment {i + 1}",
                onset=onsets[i],
                offset=offsets[i],
                created_by=user,
            )
            segment.save(manual_edit=False)
            segments_created += 1

        segmentation.segments_created = segments_created
        segmentation.save()

        return segments_created
