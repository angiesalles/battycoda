"""Cluster and segment membership models."""

from django.db import models

from ..segmentation import Segment
from .run import ClusteringRun


class Cluster(models.Model):
    """Represents a discovered pattern/cluster in the data."""

    clustering_run = models.ForeignKey(
        ClusteringRun,
        on_delete=models.CASCADE,
        related_name="clusters",
        help_text="The clustering run that created this cluster",
    )

    # Internal cluster identifier
    cluster_id = models.IntegerField(help_text="Internal numeric ID of the cluster (0, 1, 2...)")

    # Expert annotations
    label = models.CharField(max_length=255, blank=True, default="", help_text="Expert-assigned label for this cluster")
    description = models.TextField(
        blank=True, default="", help_text="Description of the acoustic pattern in this cluster"
    )
    is_labeled = models.BooleanField(default=False, help_text="Whether an expert has assigned a label to this cluster")

    # Cluster statistics
    size = models.IntegerField(default=0, help_text="Number of segments in this cluster")
    coherence = models.FloatField(
        null=True, blank=True, help_text="Measure of cluster coherence (higher is more coherent)"
    )

    # Visualization coordinates (e.g., from t-SNE or UMAP)
    vis_x = models.FloatField(null=True, blank=True, help_text="X-coordinate for 2D visualization")
    vis_y = models.FloatField(null=True, blank=True, help_text="Y-coordinate for 2D visualization")

    # Representative segment (most central to the cluster)
    representative_segment = models.ForeignKey(
        Segment,
        on_delete=models.SET_NULL,
        related_name="representing_clusters",
        null=True,
        blank=True,
        help_text="Segment that best represents this cluster",
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
        return Segment.objects.filter(segment_clusters__cluster=self).order_by("-segment_clusters__confidence")[:limit]


class SegmentCluster(models.Model):
    """Maps segments to clusters with confidence scores."""

    segment = models.ForeignKey(
        Segment,
        on_delete=models.CASCADE,
        related_name="segment_clusters",
        help_text="The segment that belongs to a cluster",
    )
    cluster = models.ForeignKey(
        Cluster, on_delete=models.CASCADE, related_name="members", help_text="The cluster this segment belongs to"
    )
    confidence = models.FloatField(
        default=1.0, help_text="Confidence score (0-1) for this segment's membership in the cluster"
    )
    distance_to_center = models.FloatField(
        null=True, blank=True, help_text="Distance of this segment to the cluster center"
    )

    class Meta:
        unique_together = [("segment", "cluster")]
        ordering = ["-confidence"]
        verbose_name = "Segment Cluster Membership"
        verbose_name_plural = "Segment Cluster Memberships"

    def __str__(self):
        return f"{self.segment} in {self.cluster} (conf: {self.confidence:.2f})"
