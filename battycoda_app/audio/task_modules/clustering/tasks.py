"""
Celery tasks for clustering.

This module provides Celery task entry points for all clustering algorithms.
The actual clustering logic is delegated to algorithm-specific runners.
"""

# ruff: noqa: I001 (import order is intentional - numba_patch must be first)
# Import numba patch FIRST before any other imports
from . import numba_patch  # noqa: F401

from celery import shared_task

from .algorithms.automatic import (
    AffinityPropagationRunner,
    AutoDBSCANRunner,
    HDBSCANRunner,
    MeanShiftRunner,
    OPTICSRunner,
)
from .algorithms.manual import ManualClusteringRunner


@shared_task(
    bind=True,
    time_limit=3600,  # 1 hour hard limit
    soft_time_limit=3300,  # 55 min soft limit (allows graceful cleanup)
)
def run_clustering(self, clustering_run_id):
    """
    Main clustering task for manual algorithms (K-means, DBSCAN, Spectral, GMM).

    Supports both single-segmentation and project-level clustering.
    """
    runner = ManualClusteringRunner(clustering_run_id)
    return runner.run()


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
