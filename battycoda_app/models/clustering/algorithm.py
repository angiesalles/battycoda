"""Clustering algorithm model."""

from django.contrib.auth.models import User
from django.db import models

from ..user import Group


class ClusteringAlgorithm(models.Model):
    """Model for unsupervised clustering algorithms."""

    name = models.CharField(max_length=255, help_text="Name of the clustering algorithm")
    description = models.TextField(blank=True, default="", help_text="Description of how the algorithm works")

    # Algorithm type choices
    ALGORITHM_TYPE_CHOICES = (
        ("kmeans", "K-Means Clustering"),
        ("dbscan", "DBSCAN Density-Based Clustering"),
        ("hierarchical", "Hierarchical Clustering"),
        ("gaussian_mixture", "Gaussian Mixture Model"),
        ("spectral", "Spectral Clustering"),
        ("custom", "Custom Algorithm"),
    )
    algorithm_type = models.CharField(
        max_length=50, choices=ALGORITHM_TYPE_CHOICES, help_text="Type of clustering algorithm to use"
    )

    # Algorithm parameters stored as JSON
    parameters = models.JSONField(
        blank=True, null=True, help_text="JSON with algorithm parameters (e.g., {'n_clusters': 5, 'random_state': 42})"
    )

    # Celery task to call
    celery_task = models.CharField(
        max_length=255,
        help_text="Fully qualified Celery task name to execute this algorithm",
        default="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
    )

    # External service parameters (for custom algorithms)
    service_url = models.CharField(
        max_length=255, blank=True, default="", help_text="URL of the external service, if applicable"
    )
    endpoint = models.CharField(max_length=255, blank=True, default="", help_text="Endpoint path for the service")

    # Organization and permissions
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_clustering_algorithms",
        help_text="User who created this algorithm",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="clustering_algorithms",
        null=True,
        blank=True,
        help_text="Group that owns this algorithm. If null, it's available to all groups",
    )
    is_active = models.BooleanField(default=True, help_text="Whether this algorithm is currently active")

    class Meta:
        ordering = ["name"]
        verbose_name = "Clustering Algorithm"
        verbose_name_plural = "Clustering Algorithms"

    def __str__(self):
        return self.name
