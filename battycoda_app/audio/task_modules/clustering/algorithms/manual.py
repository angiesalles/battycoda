"""
Manual clustering algorithms that require specifying the number of clusters.
"""

import numpy as np
from sklearn.cluster import DBSCAN, KMeans, SpectralClustering
from sklearn.mixture import GaussianMixture

from .base import BaseClusteringRunner


class ManualClusteringRunner(BaseClusteringRunner):
    """
    Runner for manual clustering algorithms (K-means, DBSCAN, Spectral, GMM).

    These algorithms typically require the user to specify the number of clusters
    or other key parameters.
    """

    # Map algorithm types to their runner methods
    ALGORITHM_RUNNERS = {
        "kmeans": "_run_kmeans",
        "dbscan": "_run_dbscan",
        "spectral": "_run_spectral",
        "gaussian_mixture": "_run_gmm",
    }

    def _run_algorithm(self, features_scaled):
        """Dispatch to the appropriate manual algorithm."""
        algorithm_type = self.clustering_run.algorithm.algorithm_type

        if algorithm_type not in self.ALGORITHM_RUNNERS:
            raise ValueError(f"Unsupported manual clustering algorithm: {algorithm_type}")

        runner_method = getattr(self, self.ALGORITHM_RUNNERS[algorithm_type])
        return runner_method(features_scaled)

    def _run_kmeans(self, features_scaled):
        """Run K-means clustering."""
        params = self._get_parameters()
        n_clusters = self.clustering_run.n_clusters or params.get("n_clusters", 5)
        random_state = params.get("random_state", 42)

        labels, _, _ = run_kmeans_clustering(features_scaled, n_clusters=n_clusters, random_state=random_state)
        return labels

    def _run_dbscan(self, features_scaled):
        """Run DBSCAN clustering."""
        params = self._get_parameters()
        eps = params.get("eps", 0.5)
        min_samples = params.get("min_samples", 5)

        labels, _, _ = run_dbscan_clustering(features_scaled, eps=eps, min_samples=min_samples)
        return labels

    def _run_spectral(self, features_scaled):
        """Run Spectral clustering."""
        params = self._get_parameters()
        n_clusters = self.clustering_run.n_clusters or params.get("n_clusters", 5)
        random_state = params.get("random_state", 42)

        labels, _, _ = run_spectral_clustering(features_scaled, n_clusters=n_clusters, random_state=random_state)
        return labels

    def _run_gmm(self, features_scaled):
        """Run Gaussian Mixture Model clustering."""
        params = self._get_parameters()
        n_components = self.clustering_run.n_clusters or params.get("n_components", 5)
        random_state = params.get("random_state", 42)

        labels, _, _ = run_gmm_clustering(features_scaled, n_components=n_components, random_state=random_state)
        return labels

    def get_algorithm_name(self):
        """Return the algorithm name for logging."""
        algorithm_type = self.clustering_run.algorithm.algorithm_type
        return {
            "kmeans": "K-means",
            "dbscan": "DBSCAN",
            "spectral": "Spectral",
            "gaussian_mixture": "Gaussian Mixture",
        }.get(algorithm_type, algorithm_type)


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
