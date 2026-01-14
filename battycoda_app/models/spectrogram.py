"""
Spectrogram generation job models for BattyCoda.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .recording import Recording
from .user import Group


class SpectrogramJob(models.Model):
    """Model for tracking spectrogram generation jobs"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    # Basic job information
    name = models.CharField(max_length=255, help_text="Display name for the spectrogram job")
    recording = models.ForeignKey(
        Recording,
        on_delete=models.CASCADE,
        related_name="spectrogram_jobs",
        help_text="Recording to generate spectrogram for",
    )

    # Job status and tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of the spectrogram generation job",
    )
    celery_task_id = models.CharField(
        max_length=255, blank=True, null=True, help_text="Celery task ID for tracking the background job"
    )
    progress = models.IntegerField(default=0, help_text="Progress percentage (0-100)")

    # Job metadata
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="spectrogram_jobs", help_text="User who created this job"
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="spectrogram_jobs", help_text="Group this job belongs to"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Job results
    output_file_path = models.CharField(
        max_length=500, blank=True, null=True, help_text="Path to the generated spectrogram file"
    )
    output_file_url = models.CharField(
        max_length=500, blank=True, null=True, help_text="URL to access the generated spectrogram"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if the job failed")

    # Job configuration
    parameters = models.JSONField(
        default=dict, blank=True, help_text="Spectrogram generation parameters (sample rate, window size, etc.)"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Spectrogram Job"
        verbose_name_plural = "Spectrogram Jobs"

    def __str__(self):
        return f"Spectrogram: {self.recording.name} ({self.status})"

    @property
    def duration_seconds(self):
        """Calculate job duration in seconds"""
        if self.status == "completed" and self.updated_at:
            return (self.updated_at - self.created_at).total_seconds()
        elif self.status in ["in_progress", "pending"]:
            return (timezone.now() - self.created_at).total_seconds()
        return None

    @property
    def is_active(self):
        """Check if the job is still active (pending or in progress)"""
        return self.status in ["pending", "in_progress"]

    @property
    def is_complete(self):
        """Check if the job completed successfully"""
        return self.status == "completed"

    @property
    def has_output_file(self):
        """Check if the job has generated an output file"""
        return bool(self.output_file_path and self.output_file_url)

    def mark_started(self, celery_task_id=None):
        """Mark the job as started"""
        self.status = "in_progress"
        if celery_task_id:
            self.celery_task_id = celery_task_id
        self.save(update_fields=["status", "celery_task_id", "updated_at"])

    def mark_completed(self, output_file_path=None, output_file_url=None):
        """Mark the job as completed"""
        self.status = "completed"
        self.progress = 100
        if output_file_path:
            self.output_file_path = output_file_path
        if output_file_url:
            self.output_file_url = output_file_url
        self.save(update_fields=["status", "progress", "output_file_path", "output_file_url", "updated_at"])

    def mark_failed(self, error_message=None):
        """Mark the job as failed"""
        self.status = "failed"
        if error_message:
            self.error_message = error_message
        self.save(update_fields=["status", "error_message", "updated_at"])

    def mark_cancelled(self):
        """Mark the job as cancelled"""
        self.status = "cancelled"
        self.save(update_fields=["status", "updated_at"])

    def update_progress(self, progress):
        """Update the job progress"""
        self.progress = max(0, min(100, progress))
        self.save(update_fields=["progress", "updated_at"])
