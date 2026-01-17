"""Clustering run models for tracking clustering jobs."""

from django.contrib.auth.models import User
from django.db import models

from ..organization import Project, Species
from ..recording import Recording
from ..segmentation import Segmentation
from ..user import Group
from .algorithm import ClusteringAlgorithm


class ClusteringRun(models.Model):
    """Tracks a clustering job on segments."""

    name = models.CharField(max_length=255, help_text="Name for this clustering run")
    description = models.TextField(blank=True, default="", help_text="Description of this clustering run")

    # Link to segmentation containing segments to cluster (for single-file mode)
    segmentation = models.ForeignKey(
        Segmentation,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="The segmentation containing segments to cluster (single-file mode)",
    )

    # Link to project for project-level clustering
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="The project containing recordings to cluster (project-wide mode)",
    )

    # Clustering scope
    SCOPE_CHOICES = (
        ("segmentation", "Single Segmentation"),
        ("project", "Entire Project"),
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="segmentation",
        help_text="Whether clustering is for a single segmentation or entire project",
    )

    # Batch size for memory management
    batch_size = models.IntegerField(
        default=500, help_text="Number of segments to process per batch for memory management"
    )

    # Species filter for project-level clustering
    species = models.ForeignKey(
        Species,
        on_delete=models.SET_NULL,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="Species to include (required for project-level clustering)",
    )

    # Link to the clustering algorithm
    algorithm = models.ForeignKey(
        ClusteringAlgorithm,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        help_text="The clustering algorithm used for this run",
    )

    # Runtime parameters (can override algorithm defaults)
    runtime_parameters = models.JSONField(
        blank=True, null=True, help_text="JSON with runtime parameters that override algorithm defaults"
    )

    # Number of clusters (for algorithms that need predefined clusters)
    n_clusters = models.IntegerField(
        null=True, blank=True, help_text="Number of clusters to create (for algorithms that need this specified)"
    )

    # Feature extraction parameters
    feature_extraction_method = models.CharField(
        max_length=100, default="mfcc", help_text="Method used to extract features from audio (e.g., mfcc, spectrogram)"
    )
    feature_parameters = models.JSONField(
        blank=True, null=True, help_text="JSON with parameters for feature extraction"
    )

    # Job status tracking
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", help_text="Current status of the clustering run"
    )
    progress = models.FloatField(default=0.0, help_text="Progress percentage from 0-100")
    progress_message = models.CharField(
        max_length=255, blank=True, default="", help_text="Detailed progress message for UI feedback"
    )
    error_message = models.TextField(blank=True, default="", help_text="Error message if the run failed")

    # Celery task ID for tracking
    task_id = models.CharField(
        max_length=100, blank=True, default="", help_text="Celery task ID for this clustering run"
    )

    # Results summary
    num_segments_processed = models.IntegerField(default=0, help_text="Number of segments processed in this run")
    num_clusters_created = models.IntegerField(default=0, help_text="Number of clusters created in this run")
    silhouette_score = models.FloatField(
        null=True, blank=True, help_text="Silhouette score for clustering quality (-1 to 1, higher is better)"
    )

    # Organization and permissions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="clustering_runs", help_text="User who created this clustering run"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        null=True,
        help_text="Group that owns this clustering run",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Clustering Run"
        verbose_name_plural = "Clustering Runs"

    def __str__(self):
        if self.scope == "project" and self.project:
            return f"{self.name} - Project: {self.project.name}"
        elif self.segmentation:
            return f"{self.name} - {self.segmentation.recording.name}"
        return self.name

    @property
    def is_processing(self):
        """Return True if the clustering run is currently being processed."""
        return self.status in ("pending", "in_progress")

    @property
    def recording(self):
        """Return recording for single-file mode, None for project mode."""
        if self.segmentation:
            return self.segmentation.recording
        return None

    @property
    def recordings(self):
        """Return all recordings involved in this clustering run."""
        if self.scope == "project" and self.project:
            if self.species:
                return self.project.recordings.filter(species=self.species)
            return self.project.recordings.all()
        elif self.segmentation:
            return Recording.objects.filter(id=self.segmentation.recording_id)
        return Recording.objects.none()


class ClusteringRunSegmentation(models.Model):
    """Junction table to track which segmentations were included in a clustering run."""

    clustering_run = models.ForeignKey(
        ClusteringRun,
        on_delete=models.CASCADE,
        related_name="included_segmentations",
        help_text="The clustering run this segmentation was included in",
    )
    segmentation = models.ForeignKey(
        Segmentation,
        on_delete=models.CASCADE,
        related_name="included_in_clustering_runs",
        help_text="The segmentation included in the clustering run",
    )
    segments_count = models.IntegerField(
        default=0, help_text="Number of segments from this segmentation included in the run"
    )

    # Status for tracking
    STATUS_CHOICES = (
        ("included", "Included"),
        ("skipped", "Skipped"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="included",
        help_text="Whether this segmentation was included or skipped",
    )

    class Meta:
        unique_together = [("clustering_run", "segmentation")]
        verbose_name = "Clustering Run Segmentation"
        verbose_name_plural = "Clustering Run Segmentations"

    def __str__(self):
        return f"{self.clustering_run.name} - {self.segmentation.recording.name} ({self.segments_count} segments)"
