"""
Manual clustering algorithms that require specifying the number of clusters.
"""

import numpy as np
from sklearn.cluster import KMeans, DBSCAN, SpectralClustering
from sklearn.mixture import GaussianMixture


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