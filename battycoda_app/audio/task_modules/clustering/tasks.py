"""
Celery tasks for clustering.

This module provides simplified entry points for all clustering algorithms.
The actual clustering logic is delegated to algorithm-specific runners.
"""

import os
import sys

# Environment setup for Numba and librosa
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['LIBROSA_CACHE_LEVEL'] = '0'
os.environ['LIBROSA_CACHE_DIR'] = '/tmp/librosa_cache'

# Patch Numba before any imports
import importlib.util
if importlib.util.find_spec("numba"):
    import numba
    import numba.core.registry
    
    def no_jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    
    numba.jit = no_jit
    numba.njit = no_jit
    numba.vectorize = no_jit
    numba.guvectorize = no_jit
    numba.cfunc = no_jit
    numba.generated_jit = no_jit
    numba.core.registry.CPUDispatcher = no_jit
    
    if hasattr(numba, 'np') and hasattr(numba.np, 'vectorize'):
        numba.np.vectorize = no_jit

# Now safe to import other modules
import numpy as np
import librosa
from celery import shared_task
from django.db import transaction
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from ....models import Segmentation, Segment
from ....models.clustering import ClusteringRun, Cluster, SegmentCluster
from .feature_extraction import get_segments_features
from .algorithms.manual import (
    run_kmeans_clustering, 
    run_dbscan_clustering, 
    run_spectral_clustering, 
    run_gmm_clustering
)
from .algorithms.automatic import (
    HDBSCANRunner,
    MeanShiftRunner, 
    OPTICSRunner,
    AffinityPropagationRunner,
    AutoDBSCANRunner
)
from .utils import calculate_cluster_coherence, generate_tsne_visualization, find_representative_segments


@shared_task
def run_clustering(clustering_run_id):
    """
    Main clustering task for manual algorithms (K-means, DBSCAN, Spectral, GMM).
    """
    try:
        clustering_run = ClusteringRun.objects.get(id=clustering_run_id)
        clustering_run.status = "in_progress"
        clustering_run.progress = 5.0
        clustering_run.save()
        
        # Get algorithm parameters
        algorithm_type = clustering_run.algorithm.algorithm_type
        base_params = clustering_run.algorithm.parameters or {}
        runtime_params = clustering_run.runtime_parameters or {}
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
        
        clustering_run.progress = 70.0
        clustering_run.save()
        
        # Save results to database
        with transaction.atomic():
            clustering_run.num_segments_processed = len(segment_ids)
            clustering_run.num_clusters_created = len(np.unique(labels))
            if silhouette is not None:
                clustering_run.silhouette_score = silhouette
            
            # Create cluster records
            unique_labels = np.unique(labels)
            for label in unique_labels:
                if label == -1:
                    continue
                    
                cluster_size = np.sum(labels == label)
                
                cluster = Cluster.objects.create(
                    clustering_run=clustering_run,
                    cluster_id=int(label),
                    size=cluster_size,
                    coherence=coherence_scores.get(label, 0.0),
                    vis_x=0.0,
                    vis_y=0.0
                )
                
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
                            confidence=1.0 / (1.0 + distances[i]),
                            distance_to_center=float(distances[i])
                        )
            
            clustering_run.progress = 100.0
            clustering_run.status = "completed"
            clustering_run.save()
        
        return {
            "status": "success",
            "message": f"Clustering completed with {clustering_run.num_clusters_created} clusters",
            "run_id": clustering_run_id
        }
        
    except Exception as e:
        try:
            if clustering_run:
                clustering_run.status = "failed"
                clustering_run.error_message = str(e)
                clustering_run.save()
        except:
            pass
        raise e


# Automatic clustering algorithm tasks
@shared_task(bind=True, name="battycoda_app.audio.task_modules.clustering_tasks.run_hdbscan_clustering")
def run_hdbscan_clustering(self, clustering_run_id):
    """Run HDBSCAN clustering."""
    runner = HDBSCANRunner(clustering_run_id)
    return runner.run()


@shared_task(bind=True, name="battycoda_app.audio.task_modules.clustering_tasks.run_mean_shift_clustering")
def run_mean_shift_clustering(self, clustering_run_id):
    """Run Mean Shift clustering."""
    runner = MeanShiftRunner(clustering_run_id)
    return runner.run()


@shared_task(bind=True, name="battycoda_app.audio.task_modules.clustering_tasks.run_optics_clustering")
def run_optics_clustering(self, clustering_run_id):
    """Run OPTICS clustering."""
    runner = OPTICSRunner(clustering_run_id)
    return runner.run()


@shared_task(bind=True, name="battycoda_app.audio.task_modules.clustering_tasks.run_affinity_propagation_clustering")
def run_affinity_propagation_clustering(self, clustering_run_id):
    """Run Affinity Propagation clustering."""
    runner = AffinityPropagationRunner(clustering_run_id)
    return runner.run()


@shared_task(bind=True, name="battycoda_app.audio.task_modules.clustering_tasks.run_auto_dbscan_clustering")
def run_auto_dbscan_clustering(self, clustering_run_id):
    """Run Auto-DBSCAN clustering."""
    runner = AutoDBSCANRunner(clustering_run_id)
    return runner.run()