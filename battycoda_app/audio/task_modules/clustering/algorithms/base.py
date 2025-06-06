"""
Base clustering algorithm runner with common patterns.
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from .....models.clustering import ClusteringRun
from ..feature_extraction import extract_features_from_segments
from ..results import store_clustering_results


class BaseClusteringRunner:
    """
    Base class for clustering algorithm runners.
    
    Provides common functionality for all clustering algorithms including:
    - Feature extraction and scaling
    - Progress tracking
    - Results storage
    - Error handling
    """
    
    def __init__(self, clustering_run_id):
        self.clustering_run_id = clustering_run_id
        self.clustering_run = None
    
    def run(self):
        """Main entry point for running clustering algorithm."""
        try:
            self.clustering_run = ClusteringRun.objects.get(id=self.clustering_run_id)
            self._update_progress(10, "in_progress")
            
            # Extract and prepare features
            features = self._extract_features()
            self._update_progress(40)
            
            features_scaled = self._scale_features(features)
            self._update_progress(50)
            
            # Run algorithm-specific clustering
            cluster_labels = self._run_algorithm(features_scaled)
            self._update_progress(80)
            
            # Process and store results
            self._process_results(cluster_labels, features_scaled)
            
            num_clusters = self._count_clusters(cluster_labels)
            self._update_progress(100, "completed")
            
            return {
                "status": "success",
                "message": f"{self.get_algorithm_name()} completed with {num_clusters} clusters",
                "run_id": self.clustering_run_id
            }
            
        except Exception as e:
            self._handle_error(e)
            raise e
    
    def _extract_features(self):
        """Extract features from segments."""
        return extract_features_from_segments(
            self.clustering_run.segmentation,
            self.clustering_run.feature_extraction_method,
            self.clustering_run.feature_parameters
        )
    
    def _scale_features(self, features):
        """Standardize features."""
        scaler = StandardScaler()
        return scaler.fit_transform(features)
    
    def _process_results(self, cluster_labels, features_scaled):
        """Process and store clustering results."""
        num_clusters = self._count_clusters(cluster_labels)
        
        # Store clustering results
        store_clustering_results(self.clustering_run, cluster_labels, features_scaled)
        
        # Calculate silhouette score if applicable
        silhouette = self._calculate_silhouette_score(cluster_labels, features_scaled)
        if silhouette is not None:
            self.clustering_run.silhouette_score = silhouette
        
        self.clustering_run.num_clusters_created = num_clusters
        self.clustering_run.save()
    
    def _calculate_silhouette_score(self, cluster_labels, features_scaled):
        """Calculate silhouette score for clustering quality assessment."""
        unique_labels = set(cluster_labels)
        
        # Remove noise cluster if present
        if -1 in unique_labels:
            unique_labels.discard(-1)
            # Only calculate for non-noise points
            non_noise_mask = cluster_labels != -1
            if len(unique_labels) > 1 and np.sum(non_noise_mask) > 1:
                return silhouette_score(
                    features_scaled[non_noise_mask], 
                    cluster_labels[non_noise_mask]
                )
        elif len(unique_labels) > 1:
            return silhouette_score(features_scaled, cluster_labels)
        
        return None
    
    def _count_clusters(self, cluster_labels):
        """Count the number of clusters (excluding noise)."""
        unique_labels = set(cluster_labels)
        unique_labels.discard(-1)  # Remove noise cluster
        return len(unique_labels)
    
    def _update_progress(self, progress, status=None):
        """Update clustering run progress."""
        self.clustering_run.progress = progress
        if status:
            self.clustering_run.status = status
        self.clustering_run.save()
    
    def _handle_error(self, error):
        """Handle clustering errors."""
        if self.clustering_run:
            self.clustering_run.status = "failed"
            self.clustering_run.error_message = str(error)
            self.clustering_run.save()
    
    def _get_parameters(self):
        """Get merged algorithm parameters."""
        base_params = self.clustering_run.algorithm.parameters or {}
        runtime_params = self.clustering_run.runtime_parameters or {}
        return {**base_params, **runtime_params}
    
    # Abstract methods to be implemented by subclasses
    def _run_algorithm(self, features_scaled):
        """Run the specific clustering algorithm. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _run_algorithm")
    
    def get_algorithm_name(self):
        """Get the algorithm name for logging. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement get_algorithm_name")