"""
Results processing and storage for clustering.
"""

import logging
from collections import Counter

import numpy as np
from django.db import transaction

from ....models import Segment
from ....models.clustering import Cluster, ClusteringRunSegmentation, SegmentCluster
from .utils import calculate_cluster_coherence, generate_tsne_visualization

logger = logging.getLogger(__name__)

# Batch size for bulk_create operations
BATCH_SIZE = 500


def store_clustering_results(clustering_run, cluster_labels, features_scaled, segment_ids=None, segment_metadata=None):
    """
    Store clustering results to database with batched writes for efficiency.

    Args:
        clustering_run: ClusteringRun instance
        cluster_labels: Array of cluster labels for each segment
        features_scaled: Scaled feature matrix
        segment_ids: List of segment IDs (required for project-level clustering)
        segment_metadata: Dict mapping segment_id -> {recording_id, segmentation_id, ...}
                         (optional, for project-level clustering)
    """
    # For single-segmentation mode, get segment IDs from the segmentation
    if segment_ids is None:
        if clustering_run.segmentation is None:
            raise ValueError("segment_ids required for project-level clustering")
        segments = Segment.objects.filter(segmentation=clustering_run.segmentation)
        segment_ids = [segment.id for segment in segments]

    if len(segment_ids) != len(cluster_labels):
        raise ValueError(f"Mismatch between segments ({len(segment_ids)}) and labels ({len(cluster_labels)})")

    logger.info(f"Storing results for {len(segment_ids)} segments")

    # Calculate cluster coherence
    coherence_scores = calculate_cluster_coherence(features_scaled, cluster_labels)

    # Generate visualization coordinates (uses PCA for large datasets)
    vis_coords = generate_tsne_visualization(features_scaled, cluster_labels)

    # Find representative segments
    representative_segments = find_representative_segments_for_results(segment_ids, features_scaled, cluster_labels)

    # Calculate distances to cluster centers
    distances = calculate_distances_to_centers(features_scaled, cluster_labels)

    # Save results to database
    with transaction.atomic():
        # Update main clustering run record
        clustering_run.num_segments_processed = len(segment_ids)

        # Create cluster records first (small number of records)
        unique_labels = np.unique(cluster_labels)
        cluster_objects = {}  # Map label -> Cluster object

        for label in unique_labels:
            # Skip noise points in DBSCAN (label = -1)
            if label == -1:
                continue

            # Count segments in this cluster
            cluster_size = int(np.sum(cluster_labels == label))

            # Calculate visualization coordinates (cluster center)
            cluster_indices = np.where(cluster_labels == label)[0]
            if len(cluster_indices) > 0:
                cluster_coords = vis_coords[cluster_indices]
                vis_x = float(np.mean(cluster_coords[:, 0]))
                vis_y = float(np.mean(cluster_coords[:, 1]))
            else:
                vis_x = 0.0
                vis_y = 0.0

            # Create cluster record
            cluster = Cluster.objects.create(
                clustering_run=clustering_run,
                cluster_id=int(label),
                size=cluster_size,
                coherence=coherence_scores.get(label, 0.0),
                vis_x=vis_x,
                vis_y=vis_y,
            )

            # Set representative segment if available
            if label in representative_segments:
                rep_segment_id = representative_segments[label]
                try:
                    cluster.representative_segment_id = rep_segment_id
                    cluster.save(update_fields=["representative_segment"])
                except Exception as e:
                    logger.warning(f"Could not set representative segment: {e}")

            cluster_objects[label] = cluster

        clustering_run.num_clusters_created = len(cluster_objects)
        clustering_run.save(update_fields=["num_segments_processed", "num_clusters_created"])

        # Create segment-cluster mappings in batches
        segment_clusters_to_create = []
        for i, segment_id in enumerate(segment_ids):
            label = cluster_labels[i]
            if label == -1:  # Skip noise points
                continue

            cluster = cluster_objects.get(label)
            if cluster is None:
                continue

            segment_clusters_to_create.append(
                SegmentCluster(
                    segment_id=segment_id,
                    cluster=cluster,
                    confidence=1.0 / (1.0 + distances[i]),  # Convert distance to confidence
                    distance_to_center=float(distances[i]),
                )
            )

            # Batch insert
            if len(segment_clusters_to_create) >= BATCH_SIZE:
                SegmentCluster.objects.bulk_create(segment_clusters_to_create)
                logger.debug(f"Bulk created {BATCH_SIZE} SegmentCluster records")
                segment_clusters_to_create = []

        # Insert remaining records
        if segment_clusters_to_create:
            SegmentCluster.objects.bulk_create(segment_clusters_to_create)
            logger.debug(f"Bulk created {len(segment_clusters_to_create)} SegmentCluster records")

        # For project-level clustering, record which segmentations were included
        if segment_metadata and clustering_run.scope == "project":
            _record_included_segmentations(clustering_run, segment_metadata)

    logger.info(
        f"Results stored: {clustering_run.num_clusters_created} clusters, "
        f"{clustering_run.num_segments_processed} segments"
    )


def _record_included_segmentations(clustering_run, segment_metadata):
    """Record which segmentations were included in a project-level clustering run."""
    # Count segments per segmentation
    segmentation_counts = Counter()
    for seg_id, meta in segment_metadata.items():
        segmentation_counts[meta["segmentation_id"]] += 1

    # Create ClusteringRunSegmentation records
    for seg_id, count in segmentation_counts.items():
        ClusteringRunSegmentation.objects.create(
            clustering_run=clustering_run, segmentation_id=seg_id, segments_count=count, status="included"
        )

    logger.info(f"Recorded {len(segmentation_counts)} included segmentations")


def find_representative_segments_for_results(segment_ids, features, cluster_labels):
    """
    Find representative segments for each cluster (closest to center).

    This is a simplified version that works with the results storage format.
    """
    unique_labels = np.unique(cluster_labels)
    representative_segments = {}

    for label in unique_labels:
        if label == -1:  # Noise points
            continue

        # Find points in this cluster
        cluster_indices = np.where(cluster_labels == label)[0]

        if len(cluster_indices) == 0:
            continue

        # Calculate cluster center
        cluster_features = features[cluster_indices]
        center = np.mean(cluster_features, axis=0)

        # Calculate distances to center
        distances = np.array([np.linalg.norm(features[i] - center) for i in cluster_indices])

        # Find the closest point to the center
        closest_idx = cluster_indices[np.argmin(distances)]
        representative_segments[label] = segment_ids[closest_idx]

    return representative_segments


def calculate_distances_to_centers(features, cluster_labels):
    """Calculate distance of each point to its cluster center."""
    distances = np.zeros(len(features))
    unique_labels = np.unique(cluster_labels)

    for label in unique_labels:
        if label == -1:  # Noise points
            cluster_indices = np.where(cluster_labels == label)[0]
            distances[cluster_indices] = np.inf
            continue

        # Calculate cluster center
        cluster_indices = np.where(cluster_labels == label)[0]
        if len(cluster_indices) > 0:
            cluster_features = features[cluster_indices]
            center = np.mean(cluster_features, axis=0)

            # Calculate distances for all points in this cluster
            for i in cluster_indices:
                distances[i] = np.linalg.norm(features[i] - center)

    return distances
