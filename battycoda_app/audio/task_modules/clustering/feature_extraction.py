"""
Feature extraction utilities for clustering.
"""

import gc
import logging
import os

import librosa
import numpy as np

from ....models import Project, Segmentation, Segment

# Configure librosa cache to avoid permission issues
os.environ['LIBROSA_CACHE_DIR'] = '/tmp/librosa_cache'

logger = logging.getLogger(__name__)

# Standard sample rate for project-level clustering (ensures feature comparability)
STANDARD_SAMPLE_RATE = 22050


def extract_features(audio_path, start_time, end_time, method='mfcc', params=None, sr=None):
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
    if params is None:
        params = {}

    # Load audio segment (sr=None preserves original, sr=int resamples)
    y, actual_sr = librosa.load(
        audio_path,
        offset=start_time,
        duration=(end_time - start_time),
        sr=sr  # Will resample to this rate if specified
    )

    # Use the actual sample rate for feature extraction
    sr = actual_sr
    
    # Extract features based on the method
    if method == 'mfcc':
        n_mfcc = params.get('n_mfcc', 13)
        features = librosa.feature.mfcc(
            y=y, 
            sr=sr, 
            n_mfcc=n_mfcc
        )
        # Calculate mean of each coefficient over time
        features = np.mean(features, axis=1)
        
    elif method == 'melspectrogram':
        n_mels = params.get('n_mels', 128)
        features = librosa.feature.melspectrogram(
            y=y, 
            sr=sr, 
            n_mels=n_mels
        )
        # Convert to log scale
        features = librosa.power_to_db(features, ref=np.max)
        # Calculate mean over time
        features = np.mean(features, axis=1)
        
    elif method == 'chroma':
        n_chroma = params.get('n_chroma', 12)
        features = librosa.feature.chroma_stft(
            y=y, 
            sr=sr, 
            n_chroma=n_chroma
        )
        # Calculate mean over time
        features = np.mean(features, axis=1)
        
    else:
        raise ValueError(f"Unsupported feature extraction method: {method}")
    
    return features


def get_segments_features(segmentation_id, feature_method='mfcc', feature_params=None):
    """
    Extract features from all segments in a segmentation.
    
    Args:
        segmentation_id: ID of the segmentation containing segments
        feature_method: Method to use for feature extraction
        feature_params: Parameters for feature extraction
        
    Returns:
        segment_ids: List of segment IDs
        features: Matrix of features (n_segments x n_features)
    """
    segmentation = Segmentation.objects.get(id=segmentation_id)
    recording = segmentation.recording
    audio_path = recording.wav_file.path
    
    # Get all segments
    segments = Segment.objects.filter(segmentation=segmentation)
    
    segment_ids = []
    features_list = []
    
    # Extract features for each segment
    for segment in segments:
        try:
            features = extract_features(
                audio_path,
                segment.onset,
                segment.offset,
                method=feature_method,
                params=feature_params
            )
            
            segment_ids.append(segment.id)
            features_list.append(features)
        except Exception as e:
            print(f"Error extracting features for segment {segment.id}: {str(e)}")
    
    # Convert to numpy array
    if features_list:
        features = np.vstack(features_list)
        return segment_ids, features
    else:
        return [], np.array([])


def extract_features_from_segments(segmentation, feature_method='mfcc', feature_params=None):
    """
    Extract features from all segments in a segmentation (alternative interface).

    This function was missing from the original clustering_tasks.py and was being called
    by automatic clustering algorithms.

    Args:
        segmentation: Segmentation object
        feature_method: Method to use for feature extraction
        feature_params: Parameters for feature extraction

    Returns:
        features: Matrix of features (n_segments x n_features)
    """
    _, features = get_segments_features(
        segmentation.id,
        feature_method,
        feature_params
    )
    return features


def get_project_segments_features(
    project_id,
    species_id,
    feature_method='mfcc',
    feature_params=None,
    batch_size=500,
    progress_callback=None
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
        segment_ids: List of segment IDs
        features: Matrix of features (n_segments x n_features)
        segment_metadata: Dict mapping segment_id -> {recording_id, recording_name, segmentation_id}
        skipped_recordings: List of recording names that were skipped (no completed segmentation)
    """
    project = Project.objects.get(id=project_id)

    # Filter recordings by species
    recordings = project.recordings.filter(species_id=species_id)

    all_segment_ids = []
    all_features = []
    segment_metadata = {}
    skipped_recordings = []

    # Count total segments first (for progress reporting)
    total_segments = Segment.objects.filter(
        segmentation__recording__in=recordings,
        segmentation__status='completed'
    ).count()

    if total_segments == 0:
        raise ValueError(
            f"No completed segmentations found in project '{project.name}' "
            f"for the selected species."
        )

    processed = 0
    logger.info(
        f"Starting project feature extraction: {recordings.count()} recordings, "
        f"{total_segments} segments"
    )

    for recording in recordings:
        # Get the latest completed segmentation for this recording
        segmentation = recording.segmentations.filter(
            status='completed'
        ).order_by('-created_at').first()

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
                    sr=STANDARD_SAMPLE_RATE  # Force resample for consistency
                )

                all_segment_ids.append(segment.id)
                all_features.append(features)
                segment_metadata[segment.id] = {
                    'recording_id': recording.id,
                    'recording_name': recording.name,
                    'segmentation_id': segmentation.id,
                    'onset': segment.onset,
                    'offset': segment.offset,
                }
                processed += 1

                # Update progress and garbage collect periodically
                if processed % batch_size == 0:
                    if progress_callback:
                        progress_callback(processed, total_segments)
                    gc.collect()  # Memory management
                    logger.debug(f"Processed {processed}/{total_segments} segments")

            except Exception as e:
                logger.warning(f"Skipping segment {segment.id}: {e}")
                continue

    # Final progress update
    if progress_callback:
        progress_callback(processed, total_segments)

    logger.info(
        f"Feature extraction complete: {len(all_segment_ids)} segments processed, "
        f"{len(skipped_recordings)} recordings skipped"
    )

    if all_features:
        features = np.vstack(all_features)
        return all_segment_ids, features, segment_metadata, skipped_recordings
    else:
        return [], np.array([]), {}, skipped_recordings