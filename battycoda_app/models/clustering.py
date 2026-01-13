"""Clustering models for unsupervised classification in BattyCoda."""

from django.contrib.auth.models import User
from django.db import models

from .organization import Call, Project, Species
from .recording import Recording
from .segmentation import Segment, Segmentation
from .user import Group


class ClusteringAlgorithm(models.Model):
    """Model for unsupervised clustering algorithms."""

    name = models.CharField(max_length=255, help_text="Name of the clustering algorithm")
    description = models.TextField(blank=True, null=True, help_text="Description of how the algorithm works")
    
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
        max_length=50, 
        choices=ALGORITHM_TYPE_CHOICES,
        help_text="Type of clustering algorithm to use"
    )
    
    # Algorithm parameters stored as JSON
    parameters = models.JSONField(
        blank=True, 
        null=True, 
        help_text="JSON with algorithm parameters (e.g., {'n_clusters': 5, 'random_state': 42})"
    )
    
    # Celery task to call
    celery_task = models.CharField(
        max_length=255,
        help_text="Fully qualified Celery task name to execute this algorithm",
        default="battycoda_app.audio.task_modules.clustering_tasks.run_clustering",
    )

    # External service parameters (for custom algorithms)
    service_url = models.CharField(
        max_length=255, blank=True, null=True, help_text="URL of the external service, if applicable"
    )
    endpoint = models.CharField(max_length=255, blank=True, null=True, help_text="Endpoint path for the service")

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


class ClusteringRun(models.Model):
    """Tracks a clustering job on segments."""

    name = models.CharField(max_length=255, help_text="Name for this clustering run")
    description = models.TextField(blank=True, null=True, help_text="Description of this clustering run")
    
    # Link to segmentation containing segments to cluster (for single-file mode)
    segmentation = models.ForeignKey(
        Segmentation,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="The segmentation containing segments to cluster (single-file mode)"
    )

    # Link to project for project-level clustering
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="The project containing recordings to cluster (project-wide mode)"
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
        help_text="Whether clustering is for a single segmentation or entire project"
    )

    # Batch size for memory management
    batch_size = models.IntegerField(
        default=500,
        help_text="Number of segments to process per batch for memory management"
    )

    # Species filter for project-level clustering
    species = models.ForeignKey(
        Species,
        on_delete=models.SET_NULL,
        related_name="clustering_runs",
        null=True,
        blank=True,
        help_text="Species to include (required for project-level clustering)"
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
        blank=True, 
        null=True, 
        help_text="JSON with runtime parameters that override algorithm defaults"
    )
    
    # Number of clusters (for algorithms that need predefined clusters)
    n_clusters = models.IntegerField(
        null=True, 
        blank=True, 
        help_text="Number of clusters to create (for algorithms that need this specified)"
    )
    
    # Feature extraction parameters
    feature_extraction_method = models.CharField(
        max_length=100, 
        default="mfcc",
        help_text="Method used to extract features from audio (e.g., mfcc, spectrogram)"
    )
    feature_parameters = models.JSONField(
        blank=True, 
        null=True, 
        help_text="JSON with parameters for feature extraction"
    )
    
    # Job status tracking
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        help_text="Current status of the clustering run"
    )
    progress = models.FloatField(
        default=0.0,
        help_text="Progress percentage from 0-100"
    )
    progress_message = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Detailed progress message for UI feedback"
    )
    error_message = models.TextField(
        blank=True, 
        null=True,
        help_text="Error message if the run failed"
    )
    
    # Celery task ID for tracking
    task_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Celery task ID for this clustering run"
    )
    
    # Results summary
    num_segments_processed = models.IntegerField(
        default=0, 
        help_text="Number of segments processed in this run"
    )
    num_clusters_created = models.IntegerField(
        default=0, 
        help_text="Number of clusters created in this run"
    )
    silhouette_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Silhouette score for clustering quality (-1 to 1, higher is better)"
    )
    
    # Organization and permissions
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="clustering_runs",
        help_text="User who created this clustering run"
    )
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name="clustering_runs", 
        null=True,
        help_text="Group that owns this clustering run"
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
        help_text="The clustering run this segmentation was included in"
    )
    segmentation = models.ForeignKey(
        Segmentation,
        on_delete=models.CASCADE,
        related_name="included_in_clustering_runs",
        help_text="The segmentation included in the clustering run"
    )
    segments_count = models.IntegerField(
        default=0,
        help_text="Number of segments from this segmentation included in the run"
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
        help_text="Whether this segmentation was included or skipped"
    )

    class Meta:
        unique_together = [("clustering_run", "segmentation")]
        verbose_name = "Clustering Run Segmentation"
        verbose_name_plural = "Clustering Run Segmentations"

    def __str__(self):
        return f"{self.clustering_run.name} - {self.segmentation.recording.name} ({self.segments_count} segments)"


class Cluster(models.Model):
    """Represents a discovered pattern/cluster in the data."""

    clustering_run = models.ForeignKey(
        ClusteringRun, 
        on_delete=models.CASCADE, 
        related_name="clusters",
        help_text="The clustering run that created this cluster"
    )
    
    # Internal cluster identifier
    cluster_id = models.IntegerField(
        help_text="Internal numeric ID of the cluster (0, 1, 2...)"
    )
    
    # Expert annotations
    label = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Expert-assigned label for this cluster"
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text="Description of the acoustic pattern in this cluster"
    )
    is_labeled = models.BooleanField(
        default=False, 
        help_text="Whether an expert has assigned a label to this cluster"
    )
    
    # Cluster statistics
    size = models.IntegerField(
        default=0, 
        help_text="Number of segments in this cluster"
    )
    coherence = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Measure of cluster coherence (higher is more coherent)"
    )
    
    # Visualization coordinates (e.g., from t-SNE or UMAP)
    vis_x = models.FloatField(
        null=True, 
        blank=True, 
        help_text="X-coordinate for 2D visualization"
    )
    vis_y = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Y-coordinate for 2D visualization"
    )
    
    # Representative segment (most central to the cluster)
    representative_segment = models.ForeignKey(
        Segment,
        on_delete=models.SET_NULL,
        related_name="representing_clusters",
        null=True,
        blank=True,
        help_text="Segment that best represents this cluster"
    )
    
    # Creation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("clustering_run", "cluster_id")]
        ordering = ["clustering_run", "cluster_id"]
        verbose_name = "Cluster"
        verbose_name_plural = "Clusters"

    def __str__(self):
        if self.label:
            return f"Cluster {self.cluster_id}: {self.label}"
        return f"Cluster {self.cluster_id}"
    
    def get_members(self):
        """Get all segments that belong to this cluster."""
        return Segment.objects.filter(segment_clusters__cluster=self)
    
    def get_top_members(self, limit=5):
        """Get top segments that most strongly belong to this cluster."""
        return Segment.objects.filter(
            segment_clusters__cluster=self
        ).order_by('-segment_clusters__confidence')[:limit]


class SegmentCluster(models.Model):
    """Maps segments to clusters with confidence scores."""

    segment = models.ForeignKey(
        Segment, 
        on_delete=models.CASCADE, 
        related_name="segment_clusters",
        help_text="The segment that belongs to a cluster"
    )
    cluster = models.ForeignKey(
        Cluster, 
        on_delete=models.CASCADE, 
        related_name="members",
        help_text="The cluster this segment belongs to"
    )
    confidence = models.FloatField(
        default=1.0, 
        help_text="Confidence score (0-1) for this segment's membership in the cluster"
    )
    distance_to_center = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Distance of this segment to the cluster center"
    )

    class Meta:
        unique_together = [("segment", "cluster")]
        ordering = ["-confidence"]
        verbose_name = "Segment Cluster Membership"
        verbose_name_plural = "Segment Cluster Memberships"

    def __str__(self):
        return f"{self.segment} in {self.cluster} (conf: {self.confidence:.2f})"


class ClusterCallMapping(models.Model):
    """Maps clusters to species-specific call types."""

    cluster = models.ForeignKey(
        Cluster, 
        on_delete=models.CASCADE, 
        related_name="call_mappings",
        help_text="The cluster being mapped to a call type"
    )
    call = models.ForeignKey(
        Call, 
        on_delete=models.CASCADE, 
        related_name="cluster_mappings",
        help_text="The call type this cluster is mapped to"
    )
    confidence = models.FloatField(
        help_text="Confidence score (0-1) for the mapping between cluster and call type"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Notes about this mapping"
    )
    
    # Creation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="cluster_mappings",
        help_text="User who created this mapping"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("cluster", "call")]
        ordering = ["-confidence"]
        verbose_name = "Cluster-Call Mapping"
        verbose_name_plural = "Cluster-Call Mappings"

    def __str__(self):
        return f"{self.cluster} → {self.call} (conf: {self.confidence:.2f})"
    
    @property
    def species(self):
        """Return the species associated with the call type."""
        return self.call.species