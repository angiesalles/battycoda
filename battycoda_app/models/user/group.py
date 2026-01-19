"""Group-related models."""

from django.contrib.auth.models import User
from django.db import models


class Group(models.Model):
    """Group model for user grouping and permissions."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def admin_count(self):
        """Count of admin members in this group."""
        return self.group_memberships.filter(is_admin=True).count()

    def is_last_admin(self, user):
        """Check if user is the only admin of this group."""
        membership = self.group_memberships.filter(user=user, is_admin=True).first()
        return membership is not None and self.admin_count == 1

    def can_remove_member(self, user):
        """Check if a member can be removed from this group.

        Returns (can_remove, error_message) tuple.
        """
        if self.is_last_admin(user):
            return False, "Cannot remove the last admin from the group."
        return True, None

    def can_demote_admin(self, user):
        """Check if an admin can be demoted to regular member.

        Returns (can_demote, error_message) tuple.
        """
        if self.is_last_admin(user):
            return False, "Cannot remove admin status from the last admin."
        return True, None


class GroupInvitation(models.Model):
    """Group invitation model for inviting users via email."""

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invitations")
    token = models.CharField(max_length=255, unique=True, help_text="Unique token for invitation link")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation to {self.group.name} for {self.email}"

    @property
    def is_expired(self):
        from django.utils import timezone

        return self.expires_at < timezone.now()


class GroupMembership(models.Model):
    """Model for user membership in groups."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_memberships")
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "group")

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({'Admin' if self.is_admin else 'Member'})"
