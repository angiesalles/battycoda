"""Cluster to call type mapping model."""

from django.contrib.auth.models import User
from django.db import models

from ..organization import Call
from .cluster import Cluster


class ClusterCallMapping(models.Model):
    """Maps clusters to species-specific call types."""

    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        related_name="call_mappings",
        help_text="The cluster being mapped to a call type",
    )
    call = models.ForeignKey(
        Call,
        on_delete=models.CASCADE,
        related_name="cluster_mappings",
        help_text="The call type this cluster is mapped to",
    )
    confidence = models.FloatField(help_text="Confidence score (0-1) for the mapping between cluster and call type")
    notes = models.TextField(blank=True, default="", help_text="Notes about this mapping")

    # Creation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cluster_mappings", help_text="User who created this mapping"
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
