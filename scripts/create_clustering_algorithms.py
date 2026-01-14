#!/usr/bin/env python
"""
Script to create default clustering algorithms for BattyCoda.
"""

import os
import sys

import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

from battycoda_app.models.clustering import ClusteringAlgorithm


def create_default_algorithms():
    """Create default clustering algorithms for BattyCoda."""
    # Find the first admin user
    admin_user = User.objects.filter(is_staff=True).first()

    if not admin_user:
        print("No admin user found. Please create an admin user first.")
        return

    # Check if we already have clustering algorithms
    if ClusteringAlgorithm.objects.exists():
        print("Clustering algorithms already exist. Skipping creation.")
        return

    # Create K-means algorithm
    kmeans = ClusteringAlgorithm.objects.create(
        name="K-means Clustering",
        description=(
            "K-means clustering partitions the data into k clusters in which each "
            "observation belongs to the cluster with the nearest mean."
        ),
        algorithm_type="kmeans",
        parameters={"n_clusters": 5, "random_state": 42, "n_init": 10},
        celery_task="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
        created_by=admin_user,
        is_active=True,
    )

    # Create DBSCAN algorithm
    dbscan = ClusteringAlgorithm.objects.create(
        name="DBSCAN Clustering",
        description=(
            "Density-Based Spatial Clustering of Applications with Noise. "
            "Finds core samples of high density and expands clusters from them."
        ),
        algorithm_type="dbscan",
        parameters={"eps": 0.5, "min_samples": 5},
        celery_task="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
        created_by=admin_user,
        is_active=True,
    )

    # Create Gaussian mixture model
    gmm = ClusteringAlgorithm.objects.create(
        name="Gaussian Mixture Model",
        description=(
            "A probabilistic model that assumes all the data points are generated "
            "from a mixture of a finite number of Gaussian distributions."
        ),
        algorithm_type="gaussian_mixture",
        parameters={"n_components": 5, "random_state": 42},
        celery_task="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
        created_by=admin_user,
        is_active=True,
    )

    # Create Spectral clustering
    spectral = ClusteringAlgorithm.objects.create(
        name="Spectral Clustering",
        description=(
            "Spectral Clustering performs dimensionality reduction before clustering. "
            "Good for finding non-convex clusters."
        ),
        algorithm_type="spectral",
        parameters={"n_clusters": 5, "random_state": 42},
        celery_task="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
        created_by=admin_user,
        is_active=True,
    )

    print(f"Created {ClusteringAlgorithm.objects.count()} clustering algorithms:")
    for algo in ClusteringAlgorithm.objects.all():
        print(f"- {algo.name} ({algo.algorithm_type})")


if __name__ == "__main__":
    create_default_algorithms()
