"""
Feature extraction utilities for clustering.
"""

import numpy as np
import librosa
from ....models import Segmentation, Segment


def extract_features(audio_path, start_time, end_time, method='mfcc', params=None):
    """
    Extract audio features from a segment of an audio file.
    
    Args:
        audio_path: Path to the audio file
        start_time: Segment start time in seconds
        end_time: Segment end time in seconds
        method: Feature extraction method ('mfcc', 'melspectrogram', etc.)
        params: Parameters for feature extraction
        
    Returns:
        features: Extracted features as a numpy array
    """
    if params is None:
        params = {}
    
    # Load audio segment
    y, sr = librosa.load(
        audio_path, 
        offset=start_time, 
        duration=(end_time - start_time), 
        sr=None
    )
    
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