"""Task models for BattyCoda application."""

from django.contrib.auth.models import User
from django.db import models

from .organization import Project, Species
from .user import Group

# Task lock timeout in minutes
TASK_LOCK_TIMEOUT_MINUTES = 30


class TaskBatch(models.Model):
    """Task Batch for grouping tasks that were created together."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_batches")
    wav_file_name = models.CharField(max_length=255)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="task_batches")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="task_batches")
    wav_file = models.FileField(upload_to="task_batches/", null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="task_batches", null=True)
    # Reference to the source classification run if this batch was created from classification results
    classification_run = models.ForeignKey(
        "battycoda_app.ClassificationRun", on_delete=models.SET_NULL, related_name="task_batches", null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    """Task model for storing bat vocalization analysis tasks."""

    # File information
    wav_file_name = models.CharField(max_length=255)

    # Segment information
    onset = models.FloatField(help_text="Start time of the segment in seconds")
    offset = models.FloatField(help_text="End time of the segment in seconds")

    # Classification information
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="tasks")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")

    # Link to batch
    batch = models.ForeignKey(TaskBatch, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)

    # Link to source segment (if task was created from a segment)
    source_segment = models.ForeignKey(
        "battycoda_app.Segment",
        on_delete=models.SET_NULL,
        related_name="tasks",
        null=True,
        blank=True,
        help_text="The segment this task was created from",
    )

    # Task metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="tasks", null=True)

    # Task status and completion
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_done = models.BooleanField(
        default=False, help_text="Indicates that the task has been fully reviewed and labeled"
    )

    # Classification and labeling
    classification_result = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    label = models.CharField(
        max_length=255, blank=True, null=True, help_text="Final expert label assigned to this task"
    )

    # Notes and comments
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or observations about this task")

    # Annotation tracking
    annotated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="annotated_tasks",
        null=True,
        blank=True,
        help_text="User who provided the annotation/label",
    )
    annotated_at = models.DateTimeField(null=True, blank=True, help_text="When the annotation was completed")

    # In-progress tracking (who is currently working on this task)
    in_progress_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="tasks_in_progress",
        null=True,
        blank=True,
        help_text="User currently working on this task",
    )
    in_progress_since = models.DateTimeField(
        null=True, blank=True, help_text="When the user started working on this task"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.wav_file_name} ({self.onset:.2f}s - {self.offset:.2f}s)"

    def save(self, *args, **kwargs):
        # Automatically set is_done flag when status is 'done'
        if self.status == "done":
            self.is_done = True

        # If is_done is True but status isn't 'done', set status to 'done'
        if self.is_done and self.status != "done":
            self.status = "done"

        super().save(*args, **kwargs)

    def get_sample_rate(self):
        """Get sample rate by walking the relationship chain to the recording.

        Returns:
            int: Sample rate in Hz, or None if not found
        """
        if self.batch and self.batch.classification_run:
            classification_run = self.batch.classification_run
            if classification_run.segmentation and classification_run.segmentation.recording:
                return classification_run.segmentation.recording.sample_rate
        return None
