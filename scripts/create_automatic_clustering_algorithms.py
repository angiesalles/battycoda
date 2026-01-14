#!/usr/bin/env python
"""
Script to create automatic clustering algorithms that don't require manual cluster count specification.
"""

import os
import sys

import django

# Setup Django environment
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

from battycoda_app.models.clustering import ClusteringAlgorithm


def create_automatic_clustering_algorithms():
    """Create clustering algorithms that automatically determine the number of clusters."""

    # Get or create a system user for creating algorithms
    system_user, created = User.objects.get_or_create(
        username="system",
        defaults={
            "email": "system@battycoda.com",
            "first_name": "System",
            "last_name": "User",
            "is_staff": False,
            "is_active": True,
        },
    )

    algorithms_to_create = [
        {
            "name": "HDBSCAN (Auto-Clustering)",
            "description": (
                "Hierarchical Density-Based Spatial Clustering. Automatically finds clusters "
                "of varying densities and determines the optimal number of clusters. "
                "Excellent for finding clusters of different shapes and handling noise."
            ),
            "algorithm_type": "custom",
            "parameters": {
                "min_cluster_size": 5,
                "min_samples": 3,
                "cluster_selection_epsilon": 0.0,
                "allow_single_cluster": False,
                "cluster_selection_method": "eom",  # Excess of Mass
            },
            "celery_task": "battycoda_app.audio.task_modules.clustering_tasks.run_hdbscan_clustering",
        },
        {
            "name": "Mean Shift (Auto-Clustering)",
            "description": (
                "Mean Shift clustering automatically finds cluster centers by shifting points "
                "towards the mode of the density function. Determines the number of clusters "
                "automatically based on bandwidth parameter."
            ),
            "algorithm_type": "custom",
            "parameters": {
                "bandwidth": None,  # Will be estimated automatically
                "bin_seeding": True,
                "min_bin_freq": 1,
                "cluster_all": True,
            },
            "celery_task": "battycoda_app.audio.task_modules.clustering_tasks.run_mean_shift_clustering",
        },
        {
            "name": "OPTICS (Auto-Clustering)",
            "description": (
                "Ordering Points To Identify Clustering Structure. Similar to DBSCAN but "
                "handles clusters of varying densities better. Automatically determines "
                "cluster structure without requiring number of clusters."
            ),
            "algorithm_type": "custom",
            "parameters": {
                "min_samples": 5,
                "max_eps": "infinity",  # Will be converted to float('inf') in the task
                "metric": "minkowski",
                "p": 2,
                "cluster_method": "xi",
                "xi": 0.05,
            },
            "celery_task": "battycoda_app.audio.task_modules.clustering_tasks.run_optics_clustering",
        },
        {
            "name": "Affinity Propagation (Auto-Clustering)",
            "description": (
                "Affinity Propagation finds exemplars (representative points) and forms "
                "clusters around them. Automatically determines the number of clusters "
                "based on data structure and preference parameters."
            ),
            "algorithm_type": "custom",
            "parameters": {
                "damping": 0.5,
                "max_iter": 200,
                "convergence_iter": 15,
                "preference": None,  # Will be set to median similarity
                "affinity": "euclidean",
                "random_state": 42,
            },
            "celery_task": "battycoda_app.audio.task_modules.clustering_tasks.run_affinity_propagation_clustering",
        },
        {
            "name": "DBSCAN (Enhanced Auto-Clustering)",
            "description": (
                "Enhanced DBSCAN with automatic parameter estimation using k-distance graphs "
                "to find optimal eps parameter. Automatically determines clusters without "
                "specifying cluster count."
            ),
            "algorithm_type": "dbscan",
            "parameters": {
                "eps": "auto",  # Will be estimated automatically
                "min_samples": 5,
                "metric": "euclidean",
                "auto_eps_percentile": 90,  # Percentile for automatic eps estimation
            },
            "celery_task": "battycoda_app.audio.task_modules.clustering_tasks.run_auto_dbscan_clustering",
        },
    ]

    created_algorithms = []
    updated_algorithms = []

    for alg_data in algorithms_to_create:
        algorithm, created = ClusteringAlgorithm.objects.get_or_create(
            name=alg_data["name"],
            defaults={
                "description": alg_data["description"],
                "algorithm_type": alg_data["algorithm_type"],
                "parameters": alg_data["parameters"],
                "celery_task": alg_data["celery_task"],
                "created_by": system_user,
                "group": None,  # Available to all groups
                "is_active": True,
            },
        )

        if created:
            created_algorithms.append(algorithm)
            print(f"✓ Created: {algorithm.name}")
        else:
            # Update existing algorithm
            algorithm.description = alg_data["description"]
            algorithm.algorithm_type = alg_data["algorithm_type"]
            algorithm.parameters = alg_data["parameters"]
            algorithm.celery_task = alg_data["celery_task"]
            algorithm.is_active = True
            algorithm.save()
            updated_algorithms.append(algorithm)
            print(f"↻ Updated: {algorithm.name}")

    print("\nSummary:")
    print(f"- Created {len(created_algorithms)} new automatic clustering algorithms")
    print(f"- Updated {len(updated_algorithms)} existing algorithms")
    print(f"- Total automatic clustering algorithms: {len(algorithms_to_create)}")

    return created_algorithms + updated_algorithms


if __name__ == "__main__":
    print("Creating automatic clustering algorithms...")
    algorithms = create_automatic_clustering_algorithms()
    print("\nDone!")
