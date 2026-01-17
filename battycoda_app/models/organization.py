"""Organization models for BattyCoda application."""

import os
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from .user import Group


def get_species_image_path(instance, filename):
    """
    Generate a unique path for species images.
    Format: species_images/user_<user_id>/species_<species_id>/<timestamp>_<filename>
    This ensures:
    1. Separation by user
    2. Separation by species
    3. Timestamp to avoid name collisions
    4. Original filename preserved for reference
    """
    # Extract file extension
    ext = os.path.splitext(filename)[1].lower()

    # Generate a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Use the user ID and create a timestamp-based filename
    user_id = instance.created_by.id if instance.created_by else "unknown"
    species_id = instance.id if instance.id else "new"

    # Create a clean filename (remove special characters)
    clean_filename = "".join(c for c in os.path.splitext(filename)[0] if c.isalnum() or c in "_- ")
    clean_filename = clean_filename.replace(" ", "_")

    # Format: user_<id>/species_<id>/<timestamp>_<clean_filename><ext>
    return f"species_images/user_{user_id}/species_{species_id}/{timestamp}_{clean_filename}{ext}"


class Project(models.Model):
    """Project model for research projects."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="projects", null=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("name", "group")]

    def __str__(self):
        return self.name


class Species(models.Model):
    """Species model for bat species."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to=get_species_image_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="species", null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="species", null=True, blank=True)
    is_system = models.BooleanField(
        default=False, help_text="Designates whether this is a system-wide species available to all users"
    )

    detail_padding_start_ms = models.IntegerField(
        default=8, help_text="Padding in milliseconds before the call in detail view spectrograms"
    )
    detail_padding_end_ms = models.IntegerField(
        default=8, help_text="Padding in milliseconds after the call in detail view spectrograms"
    )
    overview_padding_start_ms = models.IntegerField(
        default=500, help_text="Padding in milliseconds before the call in overview spectrograms"
    )
    overview_padding_end_ms = models.IntegerField(
        default=500, help_text="Padding in milliseconds after the call in overview spectrograms"
    )

    class Meta:
        verbose_name_plural = "Species"
        ordering = ["name"]
        unique_together = [("name", "group")]

    def __str__(self):
        if self.is_system:
            return f"{self.name} (System)"
        return self.name

    def can_modify_calls(self):
        """
        Check if this species' call types can be modified.
        Returns False if there are classifiers linked to this species or if it's a system species.
        """
        # System species can't be modified
        if self.is_system:
            return False

        # Import here to avoid circular imports
        from .classification import Classifier

        return not Classifier.objects.filter(species=self).exists()

    @classmethod
    def get_available_for_user(cls, user):
        """
        Get all species available to a user, including system species
        and those belonging to the user's group.
        """
        if not user or not hasattr(user, "profile"):
            return cls.objects.none()

        # Get system species and species for the user's group
        if user.profile.group:
            return cls.objects.filter(models.Q(is_system=True) | models.Q(group=user.profile.group)).order_by("name")
        else:
            return cls.objects.filter(
                models.Q(is_system=True) | models.Q(created_by=user, group__isnull=True)
            ).order_by("name")


class Call(models.Model):
    """Call types for species."""

    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="calls")
    short_name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["short_name"]
        unique_together = ["species", "short_name"]

    def __str__(self):
        return f"{self.species.name} - {self.short_name}"

    def can_be_deleted(self):
        """
        Check if this call type can be safely deleted.
        Returns False if it belongs to a species that has classifiers.
        """
        # Check if the species is linked to any classifiers
        return self.species.can_modify_calls()
