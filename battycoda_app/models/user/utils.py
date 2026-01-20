"""User models for BattyCoda application.

IMPORTANT: Email Uniqueness
A database-level unique constraint exists on auth_user.email (migration 0014_auto_20250716_1838).
Use get_user_by_email() utility function for safe email lookups.
"""

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def get_user_by_email(email):
    """
    Safely get a user by email address.

    Args:
        email (str): Email address to search for

    Returns:
        User or None: User object if found, None if not found

    Raises:
        User.MultipleObjectsReturned: If multiple users have the same email
                                     (should not happen with unique constraint)
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile and optionally demo data for new users.

    Set instance._skip_demo_data = True before saving to skip demo data creation.
    This is useful for programmatic user creation (tests, migrations, admin scripts).
    """
    from .group import Group, GroupInvitation, GroupMembership
    from .profile import UserProfile

    if created:
        # Check if the user was invited to a group
        # Look for a pending invitation with the user's email
        invitation = None
        if instance.email:
            invitation = GroupInvitation.objects.filter(
                email=instance.email, accepted=False, expires_at__gt=timezone.now()
            ).first()

        if invitation:
            # This user was invited to join an existing group
            # Create the profile with the invited group
            UserProfile.objects.create(user=instance, group=invitation.group)

            # Create group membership record
            GroupMembership.objects.create(user=instance, group=invitation.group, is_admin=False)
        else:
            # This is a new user creating their own account
            # Create a new group for this user with unique name based on username
            group_name = f"{instance.username}'s Group"
            group = Group.objects.create(
                name=group_name, description="Your personal workspace for projects and recordings"
            )

            # Create profile with the new group and make user an admin
            # Enable management features by default for new users
            UserProfile.objects.create(user=instance, group=group, management_features_enabled=True)

            # Create group membership record
            GroupMembership.objects.create(user=instance, group=group, is_admin=True)

            # Skip demo data creation if flag is set (useful for tests, migrations, etc.)
            if not getattr(instance, "_skip_demo_data", False):
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
                from ...utils_modules.species_utils import import_default_species

                import_default_species(instance)

                # Create a demo task batch with sample bat calls
                from ...utils_modules.demo_utils import create_demo_task_batch

                create_demo_task_batch(instance)

                # Create welcome notification with demo data message
                from django.urls import reverse

                from ..notification import UserNotification

                # Generate welcome message with link to dashboard
                dashboard_link = reverse("battycoda_app:index")

                UserNotification.add_notification(
                    user=instance,
                    title="Welcome to BattyCoda!",
                    message=(
                        "Thanks for joining BattyCoda! We've set up a demo project and sample bat calls "
                        "for you to explore. Check out the dashboard to get started."
                    ),
                    notification_type="system",
                    icon="s7-like",
                    link=dashboard_link,
                )

        # For all users, ensure that system species exist
        from ...utils_modules.species_utils import setup_system_species

        setup_system_species()


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
