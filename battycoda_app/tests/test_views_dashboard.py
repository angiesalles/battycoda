"""Tests for dashboard views"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models import Group, GroupMembership, UserProfile
from battycoda_app.models.organization import Project, Species
from battycoda_app.models.task import Task, TaskBatch
from battycoda_app.tests.test_base import BattycodaTestCase


class DashboardViewsTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species for tasks
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )

        # Create a project
        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.index_url = reverse("battycoda_app:index")
        self.landing_url = reverse("battycoda_app:landing")

    def test_index_view_unauthenticated_redirects_to_landing(self):
        """Unauthenticated users should be redirected to landing page"""
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.landing_url)

    def test_index_view_authenticated(self):
        """Authenticated users should see the dashboard"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard.html")

    def test_dashboard_shows_projects_with_tasks(self):
        """Dashboard should show projects that have pending tasks"""
        self.client.login(username="testuser", password="password123")

        # Create a task batch
        batch = TaskBatch.objects.create(
            name="Test Batch",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )

        # Create pending tasks
        Task.objects.create(
            project=self.project,
            species=self.species,
            batch=batch,
            is_done=False,
            created_by=self.user,
            group=self.group,
            onset=0.0,
            offset=1.0,
        )

        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        # Check that projects_with_tasks is in context
        self.assertIn("projects_with_tasks", response.context)

    def test_dashboard_shows_my_stats(self):
        """Dashboard should show user's work statistics"""
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        # Check that my_stats is in context
        self.assertIn("my_stats", response.context)
        # Check my_stats has expected keys
        my_stats = response.context["my_stats"]
        self.assertIn("today", my_stats)
        self.assertIn("this_week", my_stats)
        self.assertIn("total", my_stats)
        self.assertIn("streak", my_stats)

    def test_dashboard_shows_leaderboard(self):
        """Dashboard should show leaderboard for group members"""
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        # Check that leaderboard is in context
        self.assertIn("leaderboard", response.context)
        # User should be in the leaderboard
        leaderboard = response.context["leaderboard"]
        self.assertTrue(any(entry["username"] == "testuser" for entry in leaderboard))

    def test_dashboard_counts_completed_tasks(self):
        """Dashboard should correctly count completed tasks"""
        self.client.login(username="testuser", password="password123")

        # Create a task batch
        batch = TaskBatch.objects.create(
            name="Test Batch",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )

        # Create and complete a task
        task = Task.objects.create(
            project=self.project,
            species=self.species,
            batch=batch,
            is_done=True,
            annotated_by=self.user,
            annotated_at=timezone.now(),
            created_by=self.user,
            group=self.group,
            onset=0.0,
            offset=1.0,
        )

        response = self.client.get(self.index_url)
        my_stats = response.context["my_stats"]
        # Should have at least 1 completed task
        self.assertGreaterEqual(my_stats["today"], 1)
        self.assertGreaterEqual(my_stats["this_week"], 1)
        self.assertGreaterEqual(my_stats["total"], 1)


class DashboardStreakCalculationTest(BattycodaTestCase):
    """Test streak calculation logic"""

    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species for tasks
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )

        # Create a project
        self.project = Project.objects.create(
            name="Test Project",
            description="A test project",
            group=self.group,
            created_by=self.user,
        )

        # Create a task batch
        self.batch = TaskBatch.objects.create(
            name="Test Batch",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )

        self.index_url = reverse("battycoda_app:index")

    def test_streak_with_today_activity(self):
        """Streak should count when there's activity today"""
        self.client.login(username="testuser", password="password123")

        # Create a task completed today
        Task.objects.create(
            project=self.project,
            species=self.species,
            batch=self.batch,
            is_done=True,
            annotated_by=self.user,
            annotated_at=timezone.now(),
            created_by=self.user,
            group=self.group,
            onset=0.0,
            offset=1.0,
        )

        response = self.client.get(self.index_url)
        my_stats = response.context["my_stats"]
        self.assertGreaterEqual(my_stats["streak"], 1)

    def test_streak_zero_with_no_activity(self):
        """Streak should be zero when there's no activity"""
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.index_url)
        my_stats = response.context["my_stats"]
        self.assertEqual(my_stats["streak"], 0)

    def test_streak_broken_with_old_activity(self):
        """Streak should be broken when last activity was more than 1 day ago"""
        self.client.login(username="testuser", password="password123")

        # Create a task completed 3 days ago
        Task.objects.create(
            project=self.project,
            species=self.species,
            batch=self.batch,
            is_done=True,
            annotated_by=self.user,
            annotated_at=timezone.now() - timedelta(days=3),
            created_by=self.user,
            group=self.group,
            onset=0.0,
            offset=1.0,
        )

        response = self.client.get(self.index_url)
        my_stats = response.context["my_stats"]
        self.assertEqual(my_stats["streak"], 0)
