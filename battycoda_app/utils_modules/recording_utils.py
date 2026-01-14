"""
Utility functions for working with recordings.
"""

from django.db import transaction

# Set up logging


def create_recording_from_batch(batch, onsets=None, offsets=None, pickle_file=None):
    """Create a recording and segments from a task batch

    Args:
        batch: The TaskBatch object to create a recording from
        onsets: Optional list of onset times in seconds
        offsets: Optional list of offset times in seconds
        pickle_file: Optional pickle file object containing onset/offset data

    Returns:
        tuple: (recording, segments_created) - The Recording object and count of segments created,
               or (None, 0) if creation failed
    """
    from battycoda_app.audio.utils import process_pickle_file

    # Ensure we have a valid batch with a WAV file
    if not batch.wav_file:
        return None, 0

    # Create a new recording using the same WAV file
    recording = _create_recording_from_batch(batch)
    segments_created = 0

    # Process the pickle file if provided
    if pickle_file:
        # Process the pickle file to get onsets and offsets
        try:
            onsets, offsets = process_pickle_file(pickle_file)
        except Exception:
            # If processing the pickle file fails, just return the recording with no segments
            return recording, segments_created

    # Create segments if we have onset/offset data
    if onsets and offsets and len(onsets) == len(offsets):
        segments_created = _create_segments_for_recording(recording, onsets, offsets, batch.created_by)

    return recording, segments_created


def _create_recording_from_batch(batch):
    """Create a Recording object from a TaskBatch

    Args:
        batch: The TaskBatch object to create a recording from

    Returns:
        Recording: The created Recording object
    """
    from battycoda_app.models import Recording

    # Create a new recording using the same WAV file
    recording = Recording(
        name=f"Recording from {batch.name}",
        description=f"Created automatically from task batch {batch.name}",
        wav_file=batch.wav_file,  # Use the same WAV file
        species=batch.species,
        project=batch.project,
        group=batch.group,
        created_by=batch.created_by,
    )
    recording.save()
    return recording


def _create_segments_for_recording(recording, onsets, offsets, user):
    """Create segments for a recording

    Args:
        recording: The Recording object to create segments for
        onsets: List of onset times in seconds
        offsets: List of offset times in seconds
        user: The User object that created the recording

    Returns:
        int: Number of segments created
    """
    from battycoda_app.models import Segment, Segmentation

    segments_created = 0
    with transaction.atomic():
        # First, create the segmentation object
        segmentation = Segmentation(
            recording=recording,
            status="completed",  # Already completed since we have the data
            progress=100,
            created_by=user,
        )
        segmentation.save()

        # Now create the segments
        for i in range(len(onsets)):
            # Create segment name
            segment_name = f"Segment {i + 1}"

            # Convert numpy types to Python native types if needed
            onset_value = float(onsets[i])
            offset_value = float(offsets[i])

            # Create and save the segment
            segment = Segment(
                recording=recording,
                name=segment_name,
                onset=onset_value,
                offset=offset_value,
                created_by=user,
            )
            segment.save()
            segments_created += 1

    return segments_created
