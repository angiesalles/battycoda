from django.contrib.auth.models import User
from django.db import models

from .user import Group


class SegmentationAlgorithm(models.Model):
    """Model for storing different segmentation algorithms."""

    name = models.CharField(max_length=255, help_text="Name of the segmentation algorithm")
    description = models.TextField(blank=True, default="", help_text="Description of how the algorithm works")

    # Algorithm type choices
    ALGORITHM_TYPE_CHOICES = (
        ("threshold", "Threshold-based Detection"),
        ("energy", "Energy-based Detection"),
        ("ml", "Machine Learning Detection"),
        ("external", "External Service"),
    )
    algorithm_type = models.CharField(
        max_length=20, choices=ALGORITHM_TYPE_CHOICES, default="threshold", help_text="Type of segmentation algorithm"
    )

    # Celery task to call
    celery_task = models.CharField(
        max_length=255,
        help_text="Fully qualified Celery task name to execute this algorithm",
        default="battycoda_app.audio.task_modules.segmentation_tasks.auto_segment_recording_task",
    )

    # External service parameters (for external algorithms)
    service_url = models.CharField(
        max_length=255, blank=True, default="", help_text="URL of the external service, if applicable"
    )
    endpoint = models.CharField(max_length=255, blank=True, default="", help_text="Endpoint path for the service")

    # Default parameters
    default_min_duration_ms = models.IntegerField(default=10, help_text="Default minimum duration in milliseconds")
    default_smooth_window = models.IntegerField(default=3, help_text="Default smoothing window size")
    default_threshold_factor = models.FloatField(default=0.5, help_text="Default threshold factor (0-10)")

    # Admin only flag
    is_active = models.BooleanField(default=True, help_text="Whether this algorithm is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="segmentation_algorithms",
        null=True,
        blank=True,
        help_text="Group that owns this algorithm. If null, it's available to all groups",
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Segmentation(models.Model):
    """Track segmentation for a recording. Each recording can have multiple segmentations."""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    recording = models.ForeignKey(
        "battycoda_app.Recording",
        on_delete=models.CASCADE,
        related_name="segmentations",
        help_text="The recording this segmentation belongs to",
    )
    name = models.CharField(
        max_length=255, default="Default Segmentation", help_text="Descriptive name for this segmentation run"
    )
    algorithm = models.ForeignKey(
        SegmentationAlgorithm,
        on_delete=models.SET_NULL,
        related_name="segmentations",
        null=True,
        blank=True,
        help_text="The algorithm used for this segmentation, if any",
    )
    task_id = models.CharField(
        max_length=100, blank=True, default="", help_text="Celery task ID for automated segmentation"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    progress = models.FloatField(default=100, help_text="Progress percentage (0-100)")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, default="")

    # Store segmentation parameters
    min_duration_ms = models.IntegerField(default=10)
    smooth_window = models.IntegerField(default=3)
    threshold_factor = models.FloatField(default=0.5)

    # Store results
    segments_created = models.IntegerField(default=0)

    # Track if this segmentation has been manually edited
    manually_edited = models.BooleanField(
        default=False, help_text="Indicates if this segmentation was manually edited after initial creation"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""
        return f"Segmentation job {self.id} - {self.recording.name} ({self.status})"

    @property
    def is_processing(self):
        """Return True if the segmentation is currently being processed."""
        return self.status in ("pending", "in_progress")


class Segment(models.Model):
    """Segment model for marking regions in recordings."""

    # Link to recording
    recording = models.ForeignKey(
        "battycoda_app.Recording",
        on_delete=models.CASCADE,
        related_name="segments",
        help_text="Recording this segment belongs to",
    )

    # Link to the segmentation that created or manages this segment
    segmentation = models.ForeignKey(
        Segmentation,
        on_delete=models.CASCADE,
        related_name="segments",
        help_text="Segmentation that manages this segment",
    )

    # Segment information
    name = models.CharField(max_length=255, blank=True, default="", help_text="Optional name for this segment")
    onset = models.FloatField(help_text="Start time of the segment in seconds")
    offset = models.FloatField(help_text="End time of the segment in seconds")

    # Creation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="segments")

    # Notes
    notes = models.TextField(blank=True, default="", help_text="Notes about this segment")

    class Meta:
        ordering = ["onset"]

    def __str__(self):
        return f"{self.recording.name} ({self.onset:.2f}s - {self.offset:.2f}s)"

    @property
    def duration(self):
        """Calculate segment duration"""
        return self.offset - self.onset

    @property
    def duration_ms(self):
        """Calculate segment duration in milliseconds"""
        return (self.offset - self.onset) * 1000

    def to_dict(self):
        """Return segment data as a dictionary for JSON responses"""
        return {
            "id": self.id,
            "name": self.name or f"Segment {self.id}",
            "onset": self.onset,
            "offset": self.offset,
            "duration": self.duration,
            "notes": self.notes,
        }

    def save(self, *args, **kwargs):
        """Override save to handle segmentation relationship"""
        manual_edit = kwargs.pop("manual_edit", True)

        if not self.segmentation_id:
            raise ValueError("Segment must be explicitly assigned to a segmentation")

        super().save(*args, **kwargs)

        if manual_edit and self.segmentation_id:
            self.segmentation.manually_edited = True
            self.segmentation.save()

    def delete(self, *args, **kwargs):
        """Override delete to mark segmentation as manually edited before deletion"""
        if self.segmentation_id:
            self.segmentation.manually_edited = True
            self.segmentation.save()

        super().delete(*args, **kwargs)
