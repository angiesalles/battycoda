"""
Automatic clustering algorithms that determine the number of clusters automatically.
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics import euclidean_distances

from .base import BaseClusteringRunner


class HDBSCANRunner(BaseClusteringRunner):
    """HDBSCAN clustering runner."""

    def _run_algorithm(self, features_scaled):
        try:
            from sklearn.cluster import HDBSCAN
        except ImportError:
            try:
                import hdbscan

                HDBSCAN = hdbscan.HDBSCAN
            except ImportError:
                raise ImportError("HDBSCAN is not available. Install with: pip install hdbscan")

        params = self._get_parameters()

        clusterer = HDBSCAN(
            min_cluster_size=params.get("min_cluster_size", 5),
            min_samples=params.get("min_samples", 3),
            cluster_selection_epsilon=params.get("cluster_selection_epsilon", 0.0),
            allow_single_cluster=params.get("allow_single_cluster", False),
            cluster_selection_method=params.get("cluster_selection_method", "eom"),
        )

        return clusterer.fit_predict(features_scaled)

    def get_algorithm_name(self):
        return "HDBSCAN"


class MeanShiftRunner(BaseClusteringRunner):
    """Mean Shift clustering runner."""

    def _run_algorithm(self, features_scaled):
        from sklearn.cluster import MeanShift, estimate_bandwidth

        params = self._get_parameters()
        bandwidth = params.get("bandwidth")

        # Estimate bandwidth if not provided
        if bandwidth is None:
            bandwidth = estimate_bandwidth(features_scaled, quantile=0.3, n_samples=min(500, len(features_scaled)))

        clusterer = MeanShift(
            bandwidth=bandwidth,
            bin_seeding=params.get("bin_seeding", True),
            min_bin_freq=params.get("min_bin_freq", 1),
            cluster_all=params.get("cluster_all", True),
        )

        return clusterer.fit_predict(features_scaled)

    def get_algorithm_name(self):
        return "Mean Shift"


class OPTICSRunner(BaseClusteringRunner):
    """OPTICS clustering runner."""

    def _run_algorithm(self, features_scaled):
        from sklearn.cluster import OPTICS

        params = self._get_parameters()

        # Get max_eps parameter and handle string 'infinity'
        max_eps = params.get("max_eps", float("inf"))
        if max_eps == "infinity":
            max_eps = float("inf")

        clusterer = OPTICS(
            min_samples=params.get("min_samples", 5),
            max_eps=max_eps,
            metric=params.get("metric", "minkowski"),
            p=params.get("p", 2),
            cluster_method=params.get("cluster_method", "xi"),
            xi=params.get("xi", 0.05),
        )

        return clusterer.fit_predict(features_scaled)

    def get_algorithm_name(self):
        return "OPTICS"


class AffinityPropagationRunner(BaseClusteringRunner):
    """Affinity Propagation clustering runner."""

    def _run_algorithm(self, features_scaled):
        from sklearn.cluster import AffinityPropagation

        params = self._get_parameters()
        preference = params.get("preference")

        # Set preference to median similarity if not provided
        if preference is None:
            distances = euclidean_distances(features_scaled)
            preference = np.median(-distances)

        clusterer = AffinityPropagation(
            damping=params.get("damping", 0.5),
            max_iter=params.get("max_iter", 200),
            convergence_iter=params.get("convergence_iter", 15),
            preference=preference,
            affinity=params.get("affinity", "euclidean"),
            random_state=params.get("random_state", 42),
        )

        return clusterer.fit_predict(features_scaled)

    def get_algorithm_name(self):
        return "Affinity Propagation"


class AutoDBSCANRunner(BaseClusteringRunner):
    """Auto-DBSCAN clustering runner with automatic eps estimation."""

    def _run_algorithm(self, features_scaled):
        params = self._get_parameters()
        min_samples = params.get("min_samples", 5)
        eps = params.get("eps", "auto")

        # Estimate eps automatically if needed
        if eps == "auto":
            from sklearn.neighbors import NearestNeighbors

            # Use k-distance graph to estimate eps
            k = min_samples
            neighbors = NearestNeighbors(n_neighbors=k)
            neighbors_fit = neighbors.fit(features_scaled)
            distances, indices = neighbors_fit.kneighbors(features_scaled)

            # Sort distances and use percentile to find eps
            k_distances = np.sort(distances[:, k - 1], axis=0)
            percentile = params.get("auto_eps_percentile", 90)
            eps = np.percentile(k_distances, percentile)

        # Update progress to show eps estimation completed
        self._update_progress(60)

        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric=params.get("metric", "euclidean"))

        cluster_labels = clusterer.fit_predict(features_scaled)

        # Store the estimated eps for reporting
        if hasattr(self.clustering_run, "runtime_parameters"):
            if self.clustering_run.runtime_parameters is None:
                self.clustering_run.runtime_parameters = {}
            self.clustering_run.runtime_parameters["estimated_eps"] = float(eps)
            self.clustering_run.save()

        return cluster_labels

    def get_algorithm_name(self):
        return "Auto-DBSCAN"
