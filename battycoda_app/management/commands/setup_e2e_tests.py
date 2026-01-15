"""
Management command to set up test data for Playwright E2E tests.

This command creates consistent test data that E2E tests can rely on.
Run this before E2E tests to ensure required test entities exist.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from battycoda_app.models import Group, GroupMembership, Project, Species, Call


# Test data constants - these match tests/e2e/fixtures/users.json
E2E_TEST_USER = {
    "username": "e2e_testuser",
    "email": "e2e_test@example.com",
    "password": "e2e_testpass123",
}

E2E_ADMIN_USER = {
    "username": "e2e_adminuser",
    "email": "e2e_admin@example.com",
    "password": "e2e_adminpass123",
}

E2E_GROUP_NAME = "E2E Test Group"
E2E_SPECIES_NAME = "E2E Test Species"
E2E_PROJECT_NAME = "E2E Test Project"


class Command(BaseCommand):
    help = "Set up test data for E2E tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing E2E test data before creating new data",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting E2E test data...")
            self._cleanup_test_data()

        self.stdout.write("Setting up E2E test data...")

        with transaction.atomic():
            # Create test group first (required for users)
            group = self._create_group()

            # Create test users and link to group
            test_user = self._create_user(E2E_TEST_USER, group, is_admin=False)
            admin_user = self._create_user(E2E_ADMIN_USER, group, is_admin=True)

            # Create test species
            species = self._create_species(group, admin_user)

            # Create test project
            project = self._create_project(group, admin_user, species)

        self.stdout.write(self.style.SUCCESS("E2E test data setup complete!"))
        self.stdout.write(f"  Group: {group.name}")
        self.stdout.write(f"  Test User: {test_user.username}")
        self.stdout.write(f"  Admin User: {admin_user.username}")
        self.stdout.write(f"  Species: {species.name}")
        self.stdout.write(f"  Project: {project.name}")

    def _create_group(self):
        """Create the E2E test group."""
        group, created = Group.objects.get_or_create(
            name=E2E_GROUP_NAME,
            defaults={
                "description": "Group for E2E testing - created automatically",
            },
        )
        if created:
            self.stdout.write(f"  Created group: {group.name}")
        else:
            self.stdout.write(f"  Group already exists: {group.name}")
        return group

    def _create_user(self, user_data, group, is_admin=False):
        """Create a test user and their profile."""
        from battycoda_app.models.user import UserProfile

        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "is_active": True,
                "is_staff": is_admin,
            },
        )

        if created:
            user.set_password(user_data["password"])
            user.save()
            self.stdout.write(f"  Created user: {user.username}")

            # The post_save signal creates a personal group and profile
            # We need to clean that up and use our test group instead
            personal_group_name = f"{user_data['username']}'s Group"
            personal_group = Group.objects.filter(name=personal_group_name).first()

            if personal_group:
                # Delete demo project created by signal
                Project.objects.filter(name="Demo Project", created_by=user).delete()

                # Delete membership to personal group
                GroupMembership.objects.filter(user=user, group=personal_group).delete()

                # Update profile to point to our test group
                if hasattr(user, 'profile'):
                    user.profile.group = group
                    user.profile.save()
                else:
                    UserProfile.objects.create(user=user, group=group)

                # Delete the personal group
                personal_group.delete()

            # Create membership to our test group
            GroupMembership.objects.get_or_create(
                user=user,
                group=group,
                defaults={"is_admin": is_admin},
            )
        else:
            # Update password to ensure it matches expected value
            user.set_password(user_data["password"])
            user.save()
            self.stdout.write(f"  User already exists: {user.username}")

            # Ensure user profile exists and is linked to group
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={"group": group},
            )
            if not profile_created and profile.group != group:
                profile.group = group
                profile.save()

            # Create group membership
            membership, membership_created = GroupMembership.objects.get_or_create(
                user=user,
                group=group,
                defaults={"is_admin": is_admin},
            )
            if not membership_created and membership.is_admin != is_admin:
                membership.is_admin = is_admin
                membership.save()

        return user

    def _create_species(self, group, created_by):
        """Create the E2E test species with call types."""
        species, created = Species.objects.get_or_create(
            name=E2E_SPECIES_NAME,
            group=group,
            defaults={
                "description": "Species for E2E testing",
                "created_by": created_by,
            },
        )
        if created:
            self.stdout.write(f"  Created species: {species.name}")

            # Add some call types
            call_types = [
                ("E2E_A", "E2E Call Type A", "Test call type A for E2E testing"),
                ("E2E_B", "E2E Call Type B", "Test call type B for E2E testing"),
                ("E2E_C", "E2E Call Type C", "Test call type C for E2E testing"),
            ]

            for short_name, long_name, description in call_types:
                Call.objects.get_or_create(
                    species=species,
                    short_name=short_name,
                    defaults={
                        "long_name": long_name,
                    },
                )
            self.stdout.write(f"    Created {len(call_types)} call types")
        else:
            self.stdout.write(f"  Species already exists: {species.name}")

        return species

    def _create_project(self, group, created_by, species):
        """Create the E2E test project."""
        project, created = Project.objects.get_or_create(
            name=E2E_PROJECT_NAME,
            group=group,
            defaults={
                "description": "Project for E2E testing",
                "created_by": created_by,
            },
        )
        if created:
            self.stdout.write(f"  Created project: {project.name}")
        else:
            self.stdout.write(f"  Project already exists: {project.name}")

        return project

    def _cleanup_test_data(self):
        """Remove existing E2E test data."""
        # Import models needed for cleanup
        from battycoda_app.models.user import UserProfile

        # Delete in reverse order of dependencies
        # 1. Delete projects (both test project and demo projects)
        Project.objects.filter(name=E2E_PROJECT_NAME).delete()
        Project.objects.filter(name="Demo Project", created_by__username__in=[
            E2E_TEST_USER["username"], E2E_ADMIN_USER["username"]
        ]).delete()

        # 2. Delete species (and their calls via cascade)
        Species.objects.filter(name=E2E_SPECIES_NAME).delete()

        # 3. Delete users and their profiles
        for username in [E2E_TEST_USER["username"], E2E_ADMIN_USER["username"]]:
            UserProfile.objects.filter(user__username=username).delete()
            User.objects.filter(username=username).delete()

        # 4. Delete group (including auto-created personal groups)
        Group.objects.filter(name=E2E_GROUP_NAME).delete()
        # Personal groups are created by the post_save signal
        Group.objects.filter(name=f"{E2E_TEST_USER['username']}'s Group").delete()
        Group.objects.filter(name=f"{E2E_ADMIN_USER['username']}'s Group").delete()

        self.stdout.write("  Cleaned up existing E2E test data")
