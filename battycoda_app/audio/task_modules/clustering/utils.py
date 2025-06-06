"""
Utility functions for clustering visualization and analysis.
"""

import numpy as np
from sklearn.manifold import TSNE


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