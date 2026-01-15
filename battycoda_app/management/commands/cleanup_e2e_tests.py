"""
Management command to clean up test data created for Playwright E2E tests.

This command removes all test data created by setup_e2e_tests.
Run this after E2E tests to clean up the database.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from battycoda_app.models import Group, Project, Recording, Species

# Import constants from setup command
from .setup_e2e_tests import (
    E2E_ADMIN_USER,
    E2E_GROUP_NAME,
    E2E_PROJECT_NAME,
    E2E_SPECIES_NAME,
    E2E_TEST_USER,
)


class Command(BaseCommand):
    help = "Clean up test data created for E2E tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force cleanup even if there are recordings (will delete them)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        if dry_run:
            self.stdout.write("DRY RUN - no data will be deleted")

        self.stdout.write("Cleaning up E2E test data...")

        with transaction.atomic():
            # Check for recordings first
            recordings_count = self._count_test_recordings()
            if recordings_count > 0:
                if force:
                    self.stdout.write(
                        self.style.WARNING(f"  Found {recordings_count} recordings - will delete")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Found {recordings_count} recordings associated with test data. "
                            "Use --force to delete them."
                        )
                    )
                    if not dry_run:
                        return

            # Delete in reverse order of dependencies
            self._delete_recordings(dry_run, force)
            self._delete_projects(dry_run)
            self._delete_species(dry_run)
            self._delete_users(dry_run)
            self._delete_group(dry_run)

        if dry_run:
            self.stdout.write(self.style.SUCCESS("DRY RUN complete - no data was deleted"))
        else:
            self.stdout.write(self.style.SUCCESS("E2E test data cleanup complete!"))

    def _count_test_recordings(self):
        """Count recordings associated with test data."""
        count = 0

        # Count recordings in test project
        project = Project.objects.filter(name=E2E_PROJECT_NAME).first()
        if project:
            count += Recording.objects.filter(project=project).count()

        # Count recordings by test users
        for username in [E2E_TEST_USER["username"], E2E_ADMIN_USER["username"]]:
            user = User.objects.filter(username=username).first()
            if user:
                count += Recording.objects.filter(created_by=user).count()

        return count

    def _delete_recordings(self, dry_run, force):
        """Delete recordings associated with test data."""
        if not force:
            return

        # Delete recordings in test project
        project = Project.objects.filter(name=E2E_PROJECT_NAME).first()
        if project:
            recordings = Recording.objects.filter(project=project)
            count = recordings.count()
            if count > 0:
                if dry_run:
                    self.stdout.write(f"  Would delete {count} recordings from test project")
                else:
                    recordings.delete()
                    self.stdout.write(f"  Deleted {count} recordings from test project")

        # Delete recordings by test users
        for username in [E2E_TEST_USER["username"], E2E_ADMIN_USER["username"]]:
            user = User.objects.filter(username=username).first()
            if user:
                recordings = Recording.objects.filter(created_by=user)
                count = recordings.count()
                if count > 0:
                    if dry_run:
                        self.stdout.write(f"  Would delete {count} recordings by {username}")
                    else:
                        recordings.delete()
                        self.stdout.write(f"  Deleted {count} recordings by {username}")

    def _delete_projects(self, dry_run):
        """Delete E2E test projects."""
        projects = Project.objects.filter(name=E2E_PROJECT_NAME)
        count = projects.count()
        if count > 0:
            if dry_run:
                self.stdout.write(f"  Would delete {count} project(s): {E2E_PROJECT_NAME}")
            else:
                projects.delete()
                self.stdout.write(f"  Deleted {count} project(s): {E2E_PROJECT_NAME}")
        else:
            self.stdout.write(f"  No projects found: {E2E_PROJECT_NAME}")

    def _delete_species(self, dry_run):
        """Delete E2E test species (and their calls via cascade)."""
        species = Species.objects.filter(name=E2E_SPECIES_NAME)
        count = species.count()
        if count > 0:
            if dry_run:
                # Count calls too
                call_count = sum(s.calls.count() for s in species)
                self.stdout.write(
                    f"  Would delete {count} species: {E2E_SPECIES_NAME} "
                    f"(with {call_count} call types)"
                )
            else:
                species.delete()
                self.stdout.write(f"  Deleted {count} species: {E2E_SPECIES_NAME}")
        else:
            self.stdout.write(f"  No species found: {E2E_SPECIES_NAME}")

    def _delete_users(self, dry_run):
        """Delete E2E test users and their profiles."""
        from battycoda_app.models.user import UserProfile

        for user_data in [E2E_TEST_USER, E2E_ADMIN_USER]:
            username = user_data["username"]
            user = User.objects.filter(username=username).first()

            if user:
                # Delete profile first
                profile = UserProfile.objects.filter(user=user).first()
                if profile:
                    if dry_run:
                        self.stdout.write(f"  Would delete profile for: {username}")
                    else:
                        profile.delete()
                        self.stdout.write(f"  Deleted profile for: {username}")

                if dry_run:
                    self.stdout.write(f"  Would delete user: {username}")
                else:
                    user.delete()
                    self.stdout.write(f"  Deleted user: {username}")
            else:
                self.stdout.write(f"  No user found: {username}")

    def _delete_group(self, dry_run):
        """Delete E2E test group and auto-created personal groups."""
        # Delete the main E2E test group
        groups = Group.objects.filter(name=E2E_GROUP_NAME)
        count = groups.count()
        if count > 0:
            if dry_run:
                self.stdout.write(f"  Would delete {count} group(s): {E2E_GROUP_NAME}")
            else:
                groups.delete()
                self.stdout.write(f"  Deleted {count} group(s): {E2E_GROUP_NAME}")
        else:
            self.stdout.write(f"  No groups found: {E2E_GROUP_NAME}")

        # Also delete auto-created personal groups for test users
        # These are created by the post_save signal when users are created
        personal_group_names = [
            f"{E2E_TEST_USER['username']}'s Group",
            f"{E2E_ADMIN_USER['username']}'s Group",
        ]
        for group_name in personal_group_names:
            personal_groups = Group.objects.filter(name=group_name)
            count = personal_groups.count()
            if count > 0:
                if dry_run:
                    self.stdout.write(f"  Would delete auto-created group: {group_name}")
                else:
                    personal_groups.delete()
                    self.stdout.write(f"  Deleted auto-created group: {group_name}")
