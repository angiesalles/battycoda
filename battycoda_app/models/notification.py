"""Notification models for BattyCoda application."""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class UserNotification(models.Model):
    """
    Model for storing user notifications in the navbar notification area
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who will receive this notification",
    )
    title = models.CharField(max_length=255, help_text="Title of the notification")
    message = models.TextField(help_text="Notification message content")

    # Notification type
    TYPE_CHOICES = (
        ("segmentation", "Segmentation Notification"),
        ("classification", "Classification Notification"),
        ("training", "Classifier Training Notification"),
        ("system", "System Notification"),
        ("info", "Information"),
    )
    notification_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="info", help_text="Type of notification"
    )

    # Status/icon for the notification
    ICON_CHOICES = (
        ("s7-check", "Success"),
        ("s7-close", "Error"),
        ("s7-info", "Info"),
        ("s7-attention", "Warning"),
        ("s7-bell", "Notification"),
    )
    icon = models.CharField(
        max_length=20, choices=ICON_CHOICES, default="s7-bell", help_text="Icon to display with notification"
    )

    # Optional link to related item
    link = models.CharField(max_length=512, blank=True, null=True, help_text="Optional link to view related content")

    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, help_text="Whether the notification has been read")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title} ({self.user.username})"

    @classmethod
    def add_notification(cls, user, title, message, notification_type="info", icon="s7-bell", link=None):
        """
        Create a new notification for a user
        """
        notification = cls.objects.create(
            user=user, title=title, message=message, notification_type=notification_type, icon=icon, link=link
        )
        return notification

    @classmethod
    def add_segmentation_notification(cls, user, segmentation, success=True):
        """
        Create a notification for a completed segmentation
        """
        recording_name = segmentation.recording.name

        if success:
            title = "Segmentation Complete"
            message = f"Segmentation for '{recording_name}' has been completed successfully."
            icon = "s7-check"
        else:
            title = "Segmentation Failed"
            message = f"Segmentation for '{recording_name}' has failed."
            icon = "s7-close"

        # Generate link to the recording detail page
        link = reverse("battycoda_app:recording_detail", kwargs={"recording_id": segmentation.recording.id})

        return cls.add_notification(
            user=user, title=title, message=message, notification_type="segmentation", icon=icon, link=link
        )

    @classmethod
    def add_classification_notification(cls, user, classification_run, success=True):
        """
        Create a notification for a completed classification run
        """
        recording_name = classification_run.segmentation.recording.name

        if success:
            title = "Classification Complete"
            message = (
                f"Classification run '{classification_run.name}' for '{recording_name}' has completed successfully."
            )
            icon = "s7-check"
        else:
            title = "Classification Failed"
            message = f"Classification run '{classification_run.name}' for '{recording_name}' has failed."
            icon = "s7-close"

        # Generate link to the dashboard (classification run detail page doesn't exist yet)
        link = reverse("battycoda_app:index")

        return cls.add_notification(
            user=user, title=title, message=message, notification_type="classification", icon=icon, link=link
        )

    @classmethod
    def add_training_notification(cls, user, training_job, success=True):
        """
        Create a notification for a completed classifier training job
        """
        if success:
            title = "Classifier Training Complete"
            message = f"Training job '{training_job.name}' has completed successfully."
            icon = "s7-check"
        else:
            title = "Classifier Training Failed"
            message = f"Training job '{training_job.name}' has failed."
            icon = "s7-close"

        # Generate link to the classifier training job detail page
        link = reverse("battycoda_app:classifier_training_job_detail", kwargs={"job_id": training_job.id})

        return cls.add_notification(
            user=user, title=title, message=message, notification_type="training", icon=icon, link=link
        )
