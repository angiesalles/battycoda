"""Authentication token models."""

import secrets

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class LoginCode(models.Model):
    """One-time login code for passwordless login"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_codes")
    code = models.CharField(max_length=10, unique=True)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"LoginCode for {self.user.username} ({self.code})"

    @classmethod
    def generate_code(cls, user, expiry_hours=24):
        """Generate a new login code for a user"""
        # Create a secure random code (for manual entry)
        code = secrets.token_urlsafe(6)[:6].upper()

        # Create a longer token for the login link
        token = secrets.token_urlsafe(48)

        # Set expiry time
        expires_at = timezone.now() + timezone.timedelta(hours=expiry_hours)

        # Create and return the login code
        return cls.objects.create(user=user, code=code, token=token, expires_at=expires_at)

    def is_valid(self):
        """Check if the code is still valid"""
        return not self.used and self.expires_at > timezone.now()


class PasswordResetToken(models.Model):
    """Token for password reset"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"PasswordResetToken for {self.user.username}"

    @classmethod
    def generate_token(cls, user, expiry_hours=24):
        """Generate a new password reset token for a user"""
        # Create a token for the reset link
        token = secrets.token_urlsafe(48)

        # Set expiry time
        expires_at = timezone.now() + timezone.timedelta(hours=expiry_hours)

        # Create and return the token
        return cls.objects.create(user=user, token=token, expires_at=expires_at)

    def is_valid(self):
        """Check if the token is still valid"""
        return not self.used and self.expires_at > timezone.now()
