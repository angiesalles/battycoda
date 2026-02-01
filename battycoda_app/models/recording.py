"""Recording models for BattyCoda application."""

from django.contrib.auth.models import User
from django.db import models

from .organization import Project, Species
from .user import Group

PROCESSING_STATUS_CHOICES = [
    ("processing", "Processing"),
    ("ready", "Ready"),
]


class RecordingManager(models.Manager):
    """Manager that excludes hidden recordings by default"""

    def get_queryset(self):
        return super().get_queryset().filter(hidden=False)


class AllRecordingManager(models.Manager):
    """Manager that includes all recordings, including hidden ones"""

    pass


class Recording(models.Model):
    """Recording model for storing full audio recordings."""

    # Recording file
    name = models.CharField(max_length=255, help_text="Name of the recording")
    description = models.TextField(blank=True, default="", help_text="Description of the recording")
    wav_file = models.FileField(upload_to="recordings/", help_text="WAV file for the recording")
    duration = models.FloatField(blank=True, null=True, help_text="Duration of the recording in seconds")
    sample_rate = models.IntegerField(blank=True, null=True, help_text="Sample rate of the recording in Hz")
    file_ready = models.BooleanField(
        default=False, help_text="Flag indicating if the file is fully uploaded and ready for processing"
    )
    spectrogram_file = models.CharField(
        max_length=255, blank=True, default="", help_text="Filename of the generated spectrogram PNG"
    )
    hidden = models.BooleanField(
        default=False, help_text="Hidden recordings are temporary previews that don't appear in normal lists"
    )
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default="processing",
        help_text="Processing status: 'processing' while spectrogram is being generated, 'ready' when complete",
    )

    # Recording metadata
    recorded_date = models.DateField(blank=True, null=True, help_text="Date when the recording was made")
    location = models.CharField(
        max_length=255, blank=True, default="", help_text="Location where the recording was made"
    )
    equipment = models.CharField(max_length=255, blank=True, default="", help_text="Equipment used for recording")
    environmental_conditions = models.TextField(
        blank=True, default="", help_text="Environmental conditions during recording"
    )

    # Organization and permissions
    species = models.ForeignKey(
        Species, on_delete=models.CASCADE, related_name="recordings", help_text="Species associated with this recording"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="recordings", help_text="Project this recording belongs to"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="recordings",
        null=True,
        help_text="Group that owns this recording",
    )

    # Creation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recordings")

    # Managers
    objects = RecordingManager()  # Default manager excludes hidden recordings
    all_objects = AllRecordingManager()  # Includes all recordings including hidden

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Recording"
        verbose_name_plural = "Recordings"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Standard save method - duration is calculated via post-save signal"""
        super().save(*args, **kwargs)

    def get_segments(self):
        """Get all segments for this recording, sorted by onset time"""
        from .segmentation import Segment

        return Segment.objects.filter(recording=self).order_by("onset")
