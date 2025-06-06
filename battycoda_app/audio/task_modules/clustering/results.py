"""
Results processing and storage for clustering.
"""

import numpy as np
from django.db import transaction

from ....models import Segment
from ....models.clustering import Cluster, SegmentCluster
from .utils import generate_tsne_visualization, find_representative_segments, calculate_cluster_coherence


def store_clustering_results(clustering_run, cluster_labels, features_scaled):
    """
    Store clustering results to database.
    
    Args:
        clustering_run: ClusteringRun instance
        cluster_labels: Array of cluster labels for each segment
        features_scaled: Scaled feature matrix
    """
    # Get segment IDs from the segmentation
    segments = Segment.objects.filter(segmentation=clustering_run.segmentation)
    segment_ids = [segment.id for segment in segments]
    
    if len(segment_ids) != len(cluster_labels):
        raise ValueError(f"Mismatch between segments ({len(segment_ids)}) and labels ({len(cluster_labels)})")
    
    # Calculate cluster coherence
    coherence_scores = calculate_cluster_coherence(features_scaled, cluster_labels)
    
    # Generate t-SNE visualization
    vis_coords = generate_tsne_visualization(features_scaled, cluster_labels)
    
    # Find representative segments
    representative_segments = find_representative_segments_for_results(
        segment_ids, 
        features_scaled, 
        cluster_labels
    )
    
    # Calculate distances to cluster centers
    distances = calculate_distances_to_centers(features_scaled, cluster_labels)
    
    # Save results to database
    with transaction.atomic():
        # Update main clustering run record
        clustering_run.num_segments_processed = len(segment_ids)
        
        # Create cluster records
        unique_labels = np.unique(cluster_labels)
        for label in unique_labels:
            # Skip noise points in DBSCAN (label = -1)
            if label == -1:
                continue
                
            # Count segments in this cluster
            cluster_size = np.sum(cluster_labels == label)
            
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
            cluster_indices = np.where(cluster_labels == label)[0]
            if len(cluster_indices) > 0:
                cluster_coords = vis_coords[cluster_indices]
                cluster.vis_x = float(np.mean(cluster_coords[:, 0]))
                cluster.vis_y = float(np.mean(cluster_coords[:, 1]))
                cluster.save()
            
            # Create segment-cluster mappings
            for i, segment_id in enumerate(segment_ids):
                if cluster_labels[i] == label:
                    SegmentCluster.objects.create(
                        segment_id=segment_id,
                        cluster=cluster,
                        confidence=1.0 / (1.0 + distances[i]),  # Convert distance to confidence
                        distance_to_center=float(distances[i])
                    )


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
        distances = np.array([
            np.linalg.norm(features[i] - center) for i in cluster_indices
        ])
        
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