"""User profile model."""

import secrets

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .group import Group, GroupMembership


class UserProfile(models.Model):
    """User profile extension model."""

    # Theme choices
    THEME_CHOICES = (
        ("light", "Light"),
        ("dark", "Dark"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="members",
        null=False,  # Group is required for all users
        help_text="Every user must belong to a group",
    )
    # User preferences
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default="light", help_text="Color theme preference")

    # Activity tracking
    last_activity = models.DateTimeField(
        null=True, blank=True, help_text="Last time the user performed any significant action"
    )

    # Management features toggle
    management_features_enabled = models.BooleanField(
        default=False, help_text="Enable access to management and administrative features"
    )
    # Profile image
    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True, help_text="Profile image")
    # API access
    api_key = models.CharField(
        max_length=40, unique=True, blank=True, null=True, help_text="API key for programmatic access"
    )

    # Authentication fields (previously Cloudflare fields, kept for data compatibility)
    cloudflare_id = models.CharField(
        max_length=255, blank=True, null=True, help_text="Deprecated - kept for data compatibility"
    )
    is_cloudflare_user = models.BooleanField(default=False, help_text="Deprecated - kept for data compatibility")
    cloudflare_email = models.EmailField(blank=True, null=True, help_text="Deprecated - kept for data compatibility")
    last_cloudflare_login = models.DateTimeField(
        blank=True, null=True, help_text="Deprecated - kept for data compatibility"
    )

    def __str__(self):
        return self.user.username

    def generate_api_key(self):
        """Generate a new API key for this user"""
        self.api_key = secrets.token_urlsafe(30)[:40]  # Generate a 40-character key
        self.save(update_fields=["api_key"])
        return self.api_key

    def update_last_activity(self):
        """Update the last activity timestamp for this user"""
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    def is_admin_of_group(self, group=None):
        """Check if user is admin of the specified group (defaults to current group)"""
        target_group = group if group else self.group
        if not target_group:
            return False
        return GroupMembership.objects.filter(user=self.user, group=target_group, is_admin=True).exists()

    @property
    def is_current_group_admin(self):
        """Check if user is admin of their current group"""
        return self.is_admin_of_group()

    @property
    def available_groups(self):
        """Get all groups the user is a member of through GroupMembership"""
        # Get groups from memberships
        membership_groups = Group.objects.filter(group_memberships__user=self.user).order_by("name")

        # Move current group to the front if it exists
        if self.group:
            result = list(membership_groups)
            if self.group in result:
                result.remove(self.group)
            return [self.group] + result

        return membership_groups

    @property
    def total_storage_gb(self):
        """Calculate total storage used by user's recordings in GB"""
        import os

        # Get all recordings uploaded by this user
        recordings = self.user.recordings.all()

        total_bytes = 0
        for recording in recordings:
            if recording.wav_file and os.path.exists(recording.wav_file.path):
                try:
                    total_bytes += os.path.getsize(recording.wav_file.path)
                except (OSError, IOError):
                    # File might not exist or be accessible
                    continue

        # Convert bytes to GB (1 GB = 1024^3 bytes)
        total_gb = total_bytes / (1024**3)
        return round(total_gb, 3)  # Use 3 decimal places for better precision

    @property
    def total_storage_display(self):
        """Get a user-friendly display of total storage used"""
        import os

        # Get all recordings uploaded by this user
        recordings = self.user.recordings.all()

        total_bytes = 0
        for recording in recordings:
            if recording.wav_file and os.path.exists(recording.wav_file.path):
                try:
                    total_bytes += os.path.getsize(recording.wav_file.path)
                except (OSError, IOError):
                    continue

        # Convert to appropriate unit
        if total_bytes == 0:
            return "0 MB"
        elif total_bytes < 1024**3:  # Less than 1 GB, show in MB
            total_mb = total_bytes / (1024**2)
            return f"{total_mb:.1f} MB"
        else:  # 1 GB or more, show in GB
            total_gb = total_bytes / (1024**3)
            return f"{total_gb:.2f} GB"

    @property
    def storage_limit_gb(self):
        """Get storage limit based on available disk space on media drive"""
        import shutil

        from django.conf import settings

        try:
            # Get disk usage statistics for the media drive
            total, used, free = shutil.disk_usage(settings.MEDIA_ROOT)

            # Convert bytes to GB and return total available space
            total_gb = total / (1024**3)
            return round(total_gb, 1)

        except Exception:
            # Fallback to a reasonable default if we can't get disk info
            return 100.0  # 100 GB fallback

    @property
    def available_storage_gb(self):
        """Calculate remaining available storage in GB based on actual disk space"""
        import shutil

        from django.conf import settings

        try:
            # Get disk usage statistics for the media drive
            total, used, free = shutil.disk_usage(settings.MEDIA_ROOT)

            # Convert bytes to GB and return actual free space
            free_gb = free / (1024**3)
            return round(free_gb, 1)

        except Exception:
            # Fallback calculation using the old method
            used = self.total_storage_gb
            limit = self.storage_limit_gb
            available = limit - used
            return round(max(0, available), 2)

    @property
    def storage_usage_percentage(self):
        """Calculate storage usage as a percentage of total disk space"""
        import shutil

        from django.conf import settings

        try:
            # Get disk usage statistics for the media drive
            total, used_disk, free = shutil.disk_usage(settings.MEDIA_ROOT)

            # Calculate percentage of total disk that is used (not just by this user)
            if total <= 0:
                return 0
            percentage = (used_disk / total) * 100
            return round(min(100, percentage), 1)  # Cap at 100%

        except Exception:
            # Fallback calculation using user's storage vs limit
            used = self.total_storage_gb
            limit = self.storage_limit_gb
            if limit <= 0:
                return 0
            percentage = (used / limit) * 100
            return round(min(100, percentage), 1)


# Create user profile when user is created
