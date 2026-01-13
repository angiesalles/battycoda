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
import logging

import librosa
import numpy as np
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.db import transaction
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ....models import Segment, Segmentation
from ....models.clustering import Cluster, ClusteringRun, SegmentCluster
from .algorithms.automatic import (
    AffinityPropagationRunner,
    AutoDBSCANRunner,
    HDBSCANRunner,
    MeanShiftRunner,
    OPTICSRunner,
)
from .algorithms.manual import (
    run_dbscan_clustering,
    run_gmm_clustering,
    run_kmeans_clustering,
    run_spectral_clustering,
)
from .feature_extraction import get_project_segments_features, get_segments_features
from .results import store_clustering_results
from .utils import (
    calculate_cluster_coherence,
    find_representative_segments,
    generate_tsne_visualization,
)

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    time_limit=3600,      # 1 hour hard limit
    soft_time_limit=3300, # 55 min soft limit (allows graceful cleanup)
)
def run_clustering(self, clustering_run_id):
    """
    Main clustering task for manual algorithms (K-means, DBSCAN, Spectral, GMM).

    Supports both single-segmentation and project-level clustering.
    """
    clustering_run = None
    try:
        clustering_run = ClusteringRun.objects.get(id=clustering_run_id)
        clustering_run.status = "in_progress"
        clustering_run.progress = 5.0
        clustering_run.progress_message = "Starting clustering..."
        clustering_run.save()

        # Get algorithm parameters
        algorithm_type = clustering_run.algorithm.algorithm_type
        base_params = clustering_run.algorithm.parameters or {}
        runtime_params = clustering_run.runtime_parameters or {}
        params = {**base_params, **runtime_params}

        # Get feature extraction parameters
        feature_method = clustering_run.feature_extraction_method
        feature_params = clustering_run.feature_parameters or {}

        # Extract features based on clustering scope
        segment_metadata = None
        if clustering_run.scope == "project":
            # Project-level clustering
            if not clustering_run.project:
                raise ValueError("Project is required for project-level clustering")
            if not clustering_run.species:
                raise ValueError("Species is required for project-level clustering")

            clustering_run.progress_message = "Extracting features from project..."
            clustering_run.save(update_fields=['progress_message'])

            def progress_callback(processed, total):
                pct = 5 + (25 * processed / total) if total > 0 else 5
                clustering_run.progress = pct
                clustering_run.progress_message = f"Extracting features: {processed}/{total} segments"
                clustering_run.save(update_fields=['progress', 'progress_message'])

            segment_ids, features, segment_metadata, skipped = get_project_segments_features(
                clustering_run.project.id,
                clustering_run.species.id,
                feature_method,
                feature_params,
                batch_size=clustering_run.batch_size,
                progress_callback=progress_callback
            )

            if skipped:
                logger.info(f"Skipped {len(skipped)} recordings without segmentations")

        else:
            # Single-segmentation clustering
            if not clustering_run.segmentation:
                raise ValueError("Segmentation is required for single-file clustering")

            clustering_run.progress_message = "Extracting features..."
            clustering_run.save(update_fields=['progress_message'])

            segment_ids, features = get_segments_features(
                clustering_run.segmentation.id,
                feature_method,
                feature_params
            )

        if len(segment_ids) == 0:
            raise ValueError("No valid segments found")

        clustering_run.progress = 30.0
        clustering_run.progress_message = f"Extracted features from {len(segment_ids)} segments"
        clustering_run.save(update_fields=['progress', 'progress_message'])

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        clustering_run.progress_message = "Running clustering algorithm..."
        clustering_run.save(update_fields=['progress_message'])

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
        clustering_run.progress_message = "Calculating cluster statistics..."
        clustering_run.save(update_fields=['progress', 'progress_message'])

        # Calculate silhouette score if applicable
        silhouette = None
        unique_labels = np.unique(labels)
        n_clusters_found = len([l for l in unique_labels if l != -1])
        if n_clusters_found > 1 and len(features_scaled) > n_clusters_found:
            try:
                # Filter out noise points for silhouette calculation
                non_noise_mask = labels != -1
                if np.sum(non_noise_mask) > n_clusters_found:
                    silhouette = silhouette_score(
                        features_scaled[non_noise_mask],
                        labels[non_noise_mask]
                    )
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")

        clustering_run.progress = 70.0
        clustering_run.progress_message = "Storing results..."
        clustering_run.save(update_fields=['progress', 'progress_message'])

        # Store results using the batched storage function
        store_clustering_results(
            clustering_run,
            labels,
            features_scaled,
            segment_ids=segment_ids,
            segment_metadata=segment_metadata
        )

        # Update final stats
        if silhouette is not None:
            clustering_run.silhouette_score = silhouette

        clustering_run.progress = 100.0
        clustering_run.progress_message = "Completed"
        clustering_run.status = "completed"
        clustering_run.save()

        return {
            "status": "success",
            "message": f"Clustering completed with {clustering_run.num_clusters_created} clusters",
            "run_id": clustering_run_id
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Clustering run {clustering_run_id} timed out")
        if clustering_run:
            clustering_run.status = "failed"
            clustering_run.error_message = (
                "Task timed out. Try reducing project size or using a simpler algorithm."
            )
            clustering_run.save()
        raise

    except Exception as e:
        logger.exception(f"Clustering run {clustering_run_id} failed: {e}")
        if clustering_run:
            clustering_run.status = "failed"
            clustering_run.error_message = str(e)
            clustering_run.save()
        raise


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