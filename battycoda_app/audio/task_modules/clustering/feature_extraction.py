"""
Feature extraction utilities for clustering.
"""

import gc
import logging
import os

import librosa
import numpy as np

from ....models import Project, Segment, Segmentation

logger = logging.getLogger(__name__)

# Flag to track if librosa cache has been configured
_librosa_cache_configured = False


def _configure_librosa_cache():
    """Configure librosa cache directory on first use (avoids module-level side effects)."""
    global _librosa_cache_configured
    if not _librosa_cache_configured:
        os.environ["LIBROSA_CACHE_DIR"] = "/tmp/librosa_cache"
        _librosa_cache_configured = True


# Standard sample rate for project-level clustering (ensures feature comparability)
STANDARD_SAMPLE_RATE = 22050


def extract_features(audio_path, start_time, end_time, method="mfcc", params=None, sr=None):
    """
    Extract audio features from a segment of an audio file.

    Args:
        audio_path: Path to the audio file
        start_time: Segment start time in seconds
        end_time: Segment end time in seconds
        method: Feature extraction method ('mfcc', 'melspectrogram', etc.)
        params: Parameters for feature extraction
        sr: Target sample rate (None to preserve original, or int to resample)

    Returns:
        features: Extracted features as a numpy array
    """
    _configure_librosa_cache()

    if params is None:
        params = {}

    # Load audio segment (sr=None preserves original, sr=int resamples)
    y, actual_sr = librosa.load(
        audio_path,
        offset=start_time,
        duration=(end_time - start_time),
        sr=sr,  # Will resample to this rate if specified
    )

    # Use the actual sample rate for feature extraction
    sr = actual_sr

    # Extract features based on the method
    if method == "mfcc":
        n_mfcc = params.get("n_mfcc", 13)
        features = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        # Calculate mean of each coefficient over time
        features = np.mean(features, axis=1)

    elif method == "melspectrogram":
        n_mels = params.get("n_mels", 128)
        features = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
        # Convert to log scale
        features = librosa.power_to_db(features, ref=np.max)
        # Calculate mean over time
        features = np.mean(features, axis=1)

    elif method == "chroma":
        n_chroma = params.get("n_chroma", 12)
        features = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=n_chroma)
        # Calculate mean over time
        features = np.mean(features, axis=1)

    else:
        raise ValueError(f"Unsupported feature extraction method: {method}")

    return features


def get_segments_features(segmentation_id, feature_method="mfcc", feature_params=None):
    """
    Extract features from all segments in a segmentation.

    Args:
        segmentation_id: ID of the segmentation containing segments
        feature_method: Method to use for feature extraction
        feature_params: Parameters for feature extraction

    Returns:
        segment_ids: List of segment IDs that were successfully processed
        features: Matrix of features (n_segments x n_features)
        failed_segments: List of (segment_id, error_message) tuples for segments that failed
    """
    segmentation = Segmentation.objects.get(id=segmentation_id)
    recording = segmentation.recording
    audio_path = recording.wav_file.path

    # Get all segments
    segments = Segment.objects.filter(segmentation=segmentation)
    total_segments = segments.count()

    segment_ids = []
    features_list = []
    failed_segments = []

    # Extract features for each segment
    for segment in segments:
        try:
            features = extract_features(
                audio_path, segment.onset, segment.offset, method=feature_method, params=feature_params
            )

            segment_ids.append(segment.id)
            features_list.append(features)
        except Exception as e:
            error_msg = str(e)
            failed_segments.append((segment.id, error_msg))
            logger.warning(f"Error extracting features for segment {segment.id}: {e}")

    # Log summary if there were failures
    if failed_segments:
        logger.warning(
            f"Feature extraction completed with {len(failed_segments)}/{total_segments} failures "
            f"for segmentation {segmentation_id}"
        )

    # Convert to numpy array
    if features_list:
        features = np.vstack(features_list)
        return segment_ids, features, failed_segments
    else:
        return [], np.array([]), failed_segments


def get_project_segments_features(
    project_id, species_id, feature_method="mfcc", feature_params=None, batch_size=500, progress_callback=None
):
    """
    Extract features from ALL segments across ALL recordings in a project.

    IMPORTANT:
    - Filters by species (required parameter to avoid mixing different species)
    - Resamples all audio to 22050 Hz for feature comparability across recordings

    Args:
        project_id: ID of the project
        species_id: ID of the species to include (required)
        feature_method: Method to use for feature extraction
        feature_params: Parameters for feature extraction
        batch_size: Number of segments to process before garbage collection
        progress_callback: Optional callback function(processed, total) for progress updates

    Returns:
        segment_ids: List of segment IDs that were successfully processed
        features: Matrix of features (n_segments x n_features)
        segment_metadata: Dict mapping segment_id -> {recording_id, recording_name, segmentation_id}
        skipped_recordings: List of recording names that were skipped (no completed segmentation)
        failed_segments: List of (segment_id, recording_name, error_message) tuples for failures
    """
    project = Project.objects.get(id=project_id)

    # Filter recordings by species
    recordings = project.recordings.filter(species_id=species_id)

    all_segment_ids = []
    all_features = []
    segment_metadata = {}
    skipped_recordings = []
    failed_segments = []

    # Count total segments first (for progress reporting)
    total_segments = Segment.objects.filter(
        segmentation__recording__in=recordings, segmentation__status="completed"
    ).count()

    if total_segments == 0:
        raise ValueError(f"No completed segmentations found in project '{project.name}' for the selected species.")

    processed = 0
    logger.info(f"Starting project feature extraction: {recordings.count()} recordings, {total_segments} segments")

    for recording in recordings:
        # Get the latest completed segmentation for this recording
        segmentation = recording.segmentations.filter(status="completed").order_by("-created_at").first()

        if not segmentation:
            skipped_recordings.append(recording.name)
            logger.info(f"Skipping recording '{recording.name}': no completed segmentation")
            continue

        audio_path = recording.wav_file.path
        segments = segmentation.segments.all()

        for segment in segments:
            try:
                # Extract features with normalized sample rate
                features = extract_features(
                    audio_path,
                    segment.onset,
                    segment.offset,
                    method=feature_method,
                    params=feature_params,
                    sr=STANDARD_SAMPLE_RATE,  # Force resample for consistency
                )

                all_segment_ids.append(segment.id)
                all_features.append(features)
                segment_metadata[segment.id] = {
                    "recording_id": recording.id,
                    "recording_name": recording.name,
                    "segmentation_id": segmentation.id,
                    "onset": segment.onset,
                    "offset": segment.offset,
                }
                processed += 1

                # Update progress and garbage collect periodically
                if processed % batch_size == 0:
                    if progress_callback:
                        progress_callback(processed, total_segments)
                    gc.collect()  # Memory management
                    logger.debug(f"Processed {processed}/{total_segments} segments")

            except Exception as e:
                error_msg = str(e)
                failed_segments.append((segment.id, recording.name, error_msg))
                logger.warning(f"Skipping segment {segment.id} from '{recording.name}': {e}")
                continue

    # Final progress update
    if progress_callback:
        progress_callback(processed, total_segments)

    # Log summary with failure info
    log_msg = f"Feature extraction complete: {len(all_segment_ids)} segments processed"
    if skipped_recordings:
        log_msg += f", {len(skipped_recordings)} recordings skipped (no segmentation)"
    if failed_segments:
        log_msg += f", {len(failed_segments)} segments failed"
        logger.warning(
            f"Feature extraction had {len(failed_segments)}/{total_segments} segment failures in project {project_id}"
        )
    logger.info(log_msg)

    if all_features:
        features = np.vstack(all_features)
        return all_segment_ids, features, segment_metadata, skipped_recordings, failed_segments
    else:
        return [], np.array([]), {}, skipped_recordings, failed_segments
