"""User models for BattyCoda application."""

import secrets
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Group(models.Model):
    """Group model for user grouping and permissions."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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

class UserProfile(models.Model):
    """User profile extension model."""

    # Theme choices
    THEME_CHOICES = (
        ("default", "Default Green"),
        ("blue-sky", "Blue Sky"),
        ("little-fox", "Little Fox"),
        ("night-city", "Night City"),
        ("orange-juice", "Orange Juice"),
        ("passion", "Passion"),
        ("pink-love", "Pink Love"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name="members", 
        null=False,  # Group is required for all users
        help_text="Every user must belong to a group"
    )
    # User preferences
    theme = models.CharField(
        max_length=20, choices=THEME_CHOICES, default="default", help_text="Color theme preference"
    )
    # Profile image
    profile_image = models.ImageField(
        upload_to="profile_images/", 
        blank=True, 
        null=True,
        help_text="Profile image"
    )
    # API access
    api_key = models.CharField(
        max_length=40, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="API key for programmatic access"
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
        self.save(update_fields=['api_key'])
        return self.api_key

    def is_admin_of_group(self, group=None):
        """Check if user is admin of the specified group (defaults to current group)"""
        target_group = group if group else self.group
        if not target_group:
            return False
        return GroupMembership.objects.filter(
            user=self.user, 
            group=target_group, 
            is_admin=True
        ).exists()

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
        from django.db.models import Sum
        
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
        total_gb = total_bytes / (1024 ** 3)
        return round(total_gb, 2)
    
    @property
    def storage_limit_gb(self):
        """Get storage limit for this user in GB"""
        # Default storage limit - can be made configurable per user/group in the future
        return 10.0  # 10 GB default limit
    
    @property
    def available_storage_gb(self):
        """Calculate remaining available storage in GB"""
        used = self.total_storage_gb
        limit = self.storage_limit_gb
        available = limit - used
        return round(max(0, available), 2)  # Ensure non-negative
    
    @property
    def storage_usage_percentage(self):
        """Calculate storage usage as a percentage"""
        used = self.total_storage_gb
        limit = self.storage_limit_gb
        if limit <= 0:
            return 0
        percentage = (used / limit) * 100
        return round(min(100, percentage), 1)  # Cap at 100%

# Create user profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    from django.db.models import Q

    if created:
        # Check if the user was invited to a group
        # Look for a pending invitation with the user's email
        from .user import GroupInvitation
        invitation = None
        if instance.email:
            invitation = GroupInvitation.objects.filter(
                email=instance.email,
                accepted=False,
                expires_at__gt=timezone.now()
            ).first()
        
        if invitation:
            # This user was invited to join an existing group
            # Create the profile with the invited group
            profile = UserProfile.objects.create(
                user=instance,
                group=invitation.group
            )
            
            # Create group membership record
            GroupMembership.objects.create(
                user=instance, 
                group=invitation.group, 
                is_admin=False
            )
        else:
            # This is a new user creating their own account
            # Create a new group for this user with unique name based on username
            group_name = f"{instance.username}'s Group"
            group = Group.objects.create(
                name=group_name, 
                description="Your personal workspace for projects and recordings"
            )

            # Create profile with the new group and make user an admin
            profile = UserProfile.objects.create(
                user=instance,
                group=group
            )
            
            # Create group membership record
            GroupMembership.objects.create(
                user=instance, 
                group=group, 
                is_admin=True
            )

            # Create a demo project for the user
            # Import here to avoid circular imports
            Project = sender.objects.model._meta.apps.get_model("battycoda_app", "Project")

            # Create a standard demo project
            project_name = "Demo Project"

            Project.objects.create(
                name=project_name,
                description="Sample project for demonstration and practice",
                created_by=instance,
                group=group,
            )

            # Import default species
            from ..utils_modules.species_utils import import_default_species
            created_species = import_default_species(instance)

            # Create a demo task batch with sample bat calls
            from ..utils_modules.demo_utils import create_demo_task_batch
            batch = create_demo_task_batch(instance)
            
            # Create welcome notification with demo data message
            from .notification import UserNotification
            from django.urls import reverse
            
            # Generate welcome message with link to dashboard
            dashboard_link = reverse('battycoda_app:index')
            
            UserNotification.add_notification(
                user=instance,
                title="Welcome to BattyCoda!",
                message=(
                    "Thanks for joining BattyCoda! We've set up a demo project and sample bat calls "
                    "for you to explore. Check out the dashboard to get started."
                ),
                notification_type="system",
                icon="s7-like",
                link=dashboard_link
            )
        
        # For all users, ensure that system species exist
        from ..utils_modules.species_utils import setup_system_species
        setup_system_species()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class LoginCode(models.Model):
    """One-time login code for passwordless login"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_codes')
    code = models.CharField(max_length=10, unique=True)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
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
        return cls.objects.create(
            user=user,
            code=code,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if the code is still valid"""
        return not self.used and self.expires_at > timezone.now()


class PasswordResetToken(models.Model):
    """Token for password reset"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    @classmethod
    def generate_token(cls, user, expiry_hours=24):
        """Generate a new password reset token for a user"""
        # Create a token for the reset link
        token = secrets.token_urlsafe(48)
        
        # Set expiry time
        expires_at = timezone.now() + timezone.timedelta(hours=expiry_hours)
        
        # Create and return the token
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Check if the token is still valid"""
        return not self.used and self.expires_at > timezone.now()
