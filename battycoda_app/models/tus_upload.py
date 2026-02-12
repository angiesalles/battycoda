"""TUS resumable upload tracking model."""

import uuid

from django.contrib.auth.models import User
from django.db import models

from .user import Group


class TusUpload(models.Model):
    """Tracks an in-progress TUS resumable upload.

    Each record represents one upload session. Chunks accumulate into
    temp_file_path until upload_offset == upload_length, at which point
    the file is finalized into a Recording and this record is deleted.
    """

    upload_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    upload_length = models.BigIntegerField(help_text="Total file size in bytes declared by client")
    upload_offset = models.BigIntegerField(default=0, help_text="Bytes received so far")
    temp_file_path = models.CharField(max_length=512, help_text="Path to temporary file accumulating chunks")
    filename = models.CharField(max_length=255, help_text="Original filename from Upload-Metadata")
    content_type = models.CharField(max_length=100, default="application/octet-stream")
    metadata_json = models.JSONField(
        default=dict, blank=True, help_text="Recording metadata (species_id, project_id, name, etc.)"
    )
    is_complete = models.BooleanField(default=False)

    # Ownership
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tus_uploads")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="tus_uploads")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TusUpload {self.upload_id} ({self.filename}) - {self.upload_offset}/{self.upload_length}"
