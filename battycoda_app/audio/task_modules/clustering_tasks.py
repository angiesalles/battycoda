"""
Clustering task modules for BattyCoda.

This module contains Celery tasks for running unsupervised clustering
algorithms on audio segments.
"""

import os
import sys

# First, set environment variables
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_LEVEL'] = '0'

# Now patch Numba directly before anything imports it
import importlib.util
if importlib.util.find_spec("numba"):
    import numba
    import numba.core.registry
    
    # Replace the actual JIT implementation with a no-op version that just returns the original function
    def no_jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]  # Called as @numba.jit without parentheses
        return decorator
    
    # Replace all JIT variants with our no-op version
    numba.jit = no_jit
    numba.njit = no_jit
    numba.vectorize = no_jit
    numba.guvectorize = no_jit
    numba.cfunc = no_jit
    numba.generated_jit = no_jit
    
    # Also patch the dispatcher registry to avoid caching attempts
    numba.core.registry.CPUDispatcher = no_jit
    
    # Make sure numba.np is also handled
    if hasattr(numba, 'np'):
        if hasattr(numba.np, 'vectorize'):
            numba.np.vectorize = no_jit

# Now import the other libraries
import numpy as np
import pickle
import tempfile
from datetime import datetime
from sklearn.cluster import KMeans, DBSCAN, SpectralClustering
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.manifold import TSNE

# Now we can safely import librosa without caching issues
import librosa

# Import scipy
import scipy

from django.conf import settings
from django.db import transaction
from celery import shared_task

from ...models import Segmentation, Segment
from ...models.clustering import ClusteringRun, Cluster, SegmentCluster


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
    # Set default parameters if none provided
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


def run_kmeans_clustering(features, n_clusters=5, random_state=42):
    """Run K-means clustering on features."""
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    labels = kmeans.fit_predict(features)
    centers = kmeans.cluster_centers_
    
    # Calculate distance of each point to its cluster center
    distances = np.zeros(len(features))
    for i, label in enumerate(labels):
        distances[i] = np.linalg.norm(features[i] - centers[label])
    
    return labels, distances, centers


def run_dbscan_clustering(features, eps=0.5, min_samples=5):
    """Run DBSCAN clustering on features."""
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(features)
    
    # Calculate pseudo-centers for each cluster
    unique_labels = np.unique(labels)
    centers = []
    for label in unique_labels:
        if label == -1:  # Noise points
            centers.append(np.zeros(features.shape[1]))
        else:
            centers.append(np.mean(features[labels == label], axis=0))
    centers = np.array(centers)
    
    # Calculate distance of each point to its cluster center
    distances = np.zeros(len(features))
    for i, label in enumerate(labels):
        if label == -1:  # Noise points
            distances[i] = np.inf
        else:
            center_idx = np.where(unique_labels == label)[0][0]
            distances[i] = np.linalg.norm(features[i] - centers[center_idx])
    
    return labels, distances, centers


def run_spectral_clustering(features, n_clusters=5, random_state=42):
    """Run spectral clustering on features."""
    spectral = SpectralClustering(n_clusters=n_clusters, random_state=random_state)
    labels = spectral.fit_predict(features)
    
    # Calculate pseudo-centers for each cluster
    centers = np.zeros((n_clusters, features.shape[1]))
    for i in range(n_clusters):
        if np.sum(labels == i) > 0:
            centers[i] = np.mean(features[labels == i], axis=0)
    
    # Calculate distance of each point to its cluster center
    distances = np.zeros(len(features))
    for i, label in enumerate(labels):
        distances[i] = np.linalg.norm(features[i] - centers[label])
    
    return labels, distances, centers


def run_gmm_clustering(features, n_components=5, random_state=42):
    """Run Gaussian Mixture Model clustering on features."""
    gmm = GaussianMixture(n_components=n_components, random_state=random_state)
    labels = gmm.fit_predict(features)
    centers = gmm.means_
    
    # Calculate distance of each point to its cluster center
    distances = np.zeros(len(features))
    for i, label in enumerate(labels):
        distances[i] = np.linalg.norm(features[i] - centers[label])
    
    return labels, distances, centers


def calculate_cluster_coherence(features, labels):
    """Calculate coherence scores for each cluster."""
    unique_labels = np.unique(labels)
    coherence_scores = {}
    
    for label in unique_labels:
        if label == -1:  # Noise points in DBSCAN
            coherence_scores[label] = 0.0
            continue
            
        cluster_points = features[labels == label]
        if len(cluster_points) <= 1:
            coherence_scores[label] = 1.0  # Perfect coherence for single-point clusters
            continue
            
        # Calculate average pairwise distance within the cluster
        dists = []
        for i in range(len(cluster_points)):
            for j in range(i+1, len(cluster_points)):
                dists.append(np.linalg.norm(cluster_points[i] - cluster_points[j]))
        
        if dists:
            # Normalize and invert to get coherence (higher is better)
            avg_dist = np.mean(dists)
            max_dist = np.max(features.std(axis=0)) * 2  # Use 2 standard deviations as reference
            coherence = 1.0 - min(avg_dist / max_dist, 1.0)
            coherence_scores[label] = coherence
        else:
            coherence_scores[label] = 0.0
    
    return coherence_scores


def generate_tsne_visualization(features, labels):
    """Generate t-SNE visualization coordinates for the clusters."""
    # Apply t-SNE dimensionality reduction
    tsne = TSNE(n_components=2, random_state=42)
    vis_coords = tsne.fit_transform(features)
    
    return vis_coords


def find_representative_segments(segment_ids, features, labels, centers):
    """Find representative segments for each cluster (closest to center)."""
    unique_labels = np.unique(labels)
    representative_segments = {}
    
    for label in unique_labels:
        if label == -1:  # Noise points in DBSCAN
            continue
            
        # Find the center for this label
        center_idx = np.where(unique_labels == label)[0][0]
        center = centers[center_idx]
        
        # Find points in this cluster
        cluster_indices = np.where(labels == label)[0]
        
        if len(cluster_indices) == 0:
            continue
            
        # Calculate distances to center
        distances = np.array([
            np.linalg.norm(features[i] - center) for i in cluster_indices
        ])
        
        # Find the closest point to the center
        closest_idx = cluster_indices[np.argmin(distances)]
        representative_segments[label] = segment_ids[closest_idx]
    
    return representative_segments


@shared_task
def run_clustering(clustering_run_id):
    """
    Celery task to run a clustering job.
    
    Args:
        clustering_run_id: ID of the ClusteringRun to execute
    """
    try:
        # Get the clustering run
        clustering_run = ClusteringRun.objects.get(id=clustering_run_id)
        
        # Update status
        clustering_run.status = "in_progress"
        clustering_run.progress = 5.0
        clustering_run.save()
        
        # Get algorithm parameters
        algorithm_type = clustering_run.algorithm.algorithm_type
        base_params = clustering_run.algorithm.parameters or {}
        runtime_params = clustering_run.runtime_parameters or {}
        
        # Merge parameters with runtime params taking precedence
        params = {**base_params, **runtime_params}
        
        # Get feature extraction parameters
        feature_method = clustering_run.feature_extraction_method
        feature_params = clustering_run.feature_parameters or {}
        
        # Extract features from segments
        segmentation_id = clustering_run.segmentation.id
        segment_ids, features = get_segments_features(
            segmentation_id, 
            feature_method, 
            feature_params
        )
        
        if len(segment_ids) == 0:
            raise ValueError("No valid segments found in the segmentation")
        
        # Update progress
        clustering_run.progress = 30.0
        clustering_run.save()
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Run the appropriate clustering algorithm
        if algorithm_type == 'kmeans':
            n_clusters = clustering_run.n_clusters or params.get('n_clusters', 5)
            random_state = params.get('random_state', 42)
            labels, distances, centers = run_kmeans_clustering(
                features_scaled, 
                n_clusters=n_clusters, 
                random_state=random_state
            )
            
        elif algorithm_type == 'dbscan':
            eps = params.get('eps', 0.5)
            min_samples = params.get('min_samples', 5)
            labels, distances, centers = run_dbscan_clustering(
                features_scaled, 
                eps=eps, 
                min_samples=min_samples
            )
            
        elif algorithm_type == 'spectral':
            n_clusters = clustering_run.n_clusters or params.get('n_clusters', 5)
            random_state = params.get('random_state', 42)
            labels, distances, centers = run_spectral_clustering(
                features_scaled, 
                n_clusters=n_clusters,
                random_state=random_state
            )
            
        elif algorithm_type == 'gaussian_mixture':
            n_components = clustering_run.n_clusters or params.get('n_components', 5)
            random_state = params.get('random_state', 42)
            labels, distances, centers = run_gmm_clustering(
                features_scaled,
                n_components=n_components,
                random_state=random_state
            )
            
        else:
            raise ValueError(f"Unsupported clustering algorithm: {algorithm_type}")
        
        # Update progress
        clustering_run.progress = 50.0
        clustering_run.save()
        
        # Calculate cluster coherence
        coherence_scores = calculate_cluster_coherence(features_scaled, labels)
        
        # Generate t-SNE visualization
        vis_coords = generate_tsne_visualization(features_scaled, labels)
        
        # Find representative segments
        representative_segments = find_representative_segments(
            segment_ids, 
            features_scaled, 
            labels, 
            centers
        )
        
        # Calculate silhouette score if applicable
        silhouette = None
        unique_labels = np.unique(labels)
        if len(unique_labels) > 1 and not np.any(unique_labels == -1) and len(features_scaled) > len(unique_labels):
            silhouette = silhouette_score(features_scaled, labels)
        
        # Update progress
        clustering_run.progress = 70.0
        clustering_run.save()
        
        # Save results to database
        with transaction.atomic():
            # Update main clustering run record
            clustering_run.num_segments_processed = len(segment_ids)
            clustering_run.num_clusters_created = len(np.unique(labels))
            if silhouette is not None:
                clustering_run.silhouette_score = silhouette
            
            # Create cluster records
            unique_labels = np.unique(labels)
            for label in unique_labels:
                # Skip noise points in DBSCAN (label = -1)
                if label == -1:
                    continue
                    
                # Count segments in this cluster
                cluster_size = np.sum(labels == label)
                
                # Create cluster record
                cluster = Cluster.objects.create(
                    clustering_run=clustering_run,
                    cluster_id=int(label),
                    size=cluster_size,
                    coherence=coherence_scores.get(label, 0.0),
                    vis_x=0.0,  # Will update below
                    vis_y=0.0   # Will update below
                )
                
                # Set representative segment if available
                if label in representative_segments:
                    segment_id = representative_segments[label]
                    segment = Segment.objects.get(id=segment_id)
                    cluster.representative_segment = segment
                    cluster.save()
                
                # Update visualization coordinates
                cluster_indices = np.where(labels == label)[0]
                if len(cluster_indices) > 0:
                    cluster_coords = vis_coords[cluster_indices]
                    cluster.vis_x = float(np.mean(cluster_coords[:, 0]))
                    cluster.vis_y = float(np.mean(cluster_coords[:, 1]))
                    cluster.save()
                
                # Create segment-cluster mappings
                for i, segment_id in enumerate(segment_ids):
                    if labels[i] == label:
                        SegmentCluster.objects.create(
                            segment_id=segment_id,
                            cluster=cluster,
                            confidence=1.0 / (1.0 + distances[i]),  # Convert distance to confidence
                            distance_to_center=float(distances[i])
                        )
            
            # Update progress
            clustering_run.progress = 100.0
            clustering_run.status = "completed"
            clustering_run.save()
        
        return {
            "status": "success",
            "message": f"Clustering completed with {clustering_run.num_clusters_created} clusters",
            "run_id": clustering_run_id
        }
        
    except Exception as e:
        # Handle exceptions
        try:
            if clustering_run:
                clustering_run.status = "failed"
                clustering_run.error_message = str(e)
                clustering_run.save()
        except:
            pass
        
        raise e