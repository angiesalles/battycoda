from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models import Group, GroupMembership, Project, Species, Task, TaskBatch, UserProfile
from battycoda_app.tests.test_base import BattycodaTestCase


class TaskViewsTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test users
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create another test user
        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")
        self.profile2 = UserProfile.objects.get(user=self.user2)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user1 to the group as admin
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group for user1
        self.profile.group = self.group
        self.profile.save()

        # Create test species
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )

        # Create test project
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )

        # Create test batch
        self.batch = TaskBatch.objects.create(
            name="Test Batch",
            description="A test batch",
            created_by=self.user,
            wav_file_name="test.wav",
            species=self.species,
            project=self.project,
            group=self.group,
        )

        # Create test tasks
        self.task = Task.objects.create(
            wav_file_name="test.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project,
            batch=self.batch,
            created_by=self.user,
            group=self.group,
            status="pending",
        )

        self.task2 = Task.objects.create(
            wav_file_name="test.wav",
            onset=3.0,
            offset=4.0,
            species=self.species,
            project=self.project,
            batch=self.batch,
            created_by=self.user,
            group=self.group,
            status="in_progress",
        )

        # URL paths
        self.task_list_url = reverse("battycoda_app:task_list")
        self.task_detail_url = reverse("battycoda_app:task_detail", args=[self.task.id])
        self.batch_list_url = reverse("battycoda_app:task_batch_list")
        self.batch_detail_url = reverse("battycoda_app:task_batch_detail", args=[self.batch.id])

    def test_task_list_view_authenticated(self):
        # Login
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_list.html")

        # Admin should see both tasks
        self.assertEqual(len(response.context["tasks"]), 2)

    def test_task_list_view_non_admin(self):
        # Make user not an admin by updating the membership
        self.membership.is_admin = False
        self.membership.save()

        # Create a task for user2
        Task.objects.create(
            wav_file_name="user2.wav",
            onset=5.0,
            offset=6.0,
            species=self.species,
            project=self.project,
            created_by=self.user2,
            group=self.group,
            status="pending",
        )

        # Login as non-admin
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.task_list_url)
        self.assertEqual(response.status_code, 200)

        # Non-admin should only see their own tasks
        self.assertEqual(len(response.context["tasks"]), 2)

    def test_task_detail_view_own_task(self):
        # Login
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.task_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_detail.html")

        # Check context
        self.assertEqual(response.context["task"], self.task)
        self.assertTrue(response.context["can_edit"])

    def test_task_detail_view_update(self):
        # Login
        self.client.login(username="testuser", password="password123")

        # Update task - status must be a valid choice: pending, in_progress, or done
        update_data = {"status": "done", "is_done": True, "label": "Test Label", "notes": "Test notes"}

        response = self.client.post(self.task_detail_url, update_data)
        self.assertEqual(response.status_code, 302)  # Redirects to task detail
        self.assertRedirects(response, self.task_detail_url)

        # Check that task was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "done")
        self.assertTrue(self.task.is_done)
        self.assertEqual(self.task.label, "Test Label")
        self.assertEqual(self.task.notes, "Test notes")

    def test_batch_list_view(self):
        # Login
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.batch_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/batch_list.html")

        # Check that batch is in context
        self.assertIn(self.batch, response.context["batches"])

    def test_batch_detail_view(self):
        # Login
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.batch_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/batch_detail.html")

        # Check context
        self.assertEqual(response.context["batch"], self.batch)
        self.assertEqual(len(response.context["tasks"]), 2)


class SkipToNextBatchViewTest(BattycodaTestCase):
    """Tests for the skip_to_next_batch_view cycling behavior."""

    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        self.profile.save()

        # Create test species
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )

        # Create test project
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )

        # Create three batches (A, B, C) to test cycling
        self.batch_a = TaskBatch.objects.create(
            name="Batch A",
            created_by=self.user,
            wav_file_name="a.wav",
            species=self.species,
            project=self.project,
            group=self.group,
        )
        self.batch_b = TaskBatch.objects.create(
            name="Batch B",
            created_by=self.user,
            wav_file_name="b.wav",
            species=self.species,
            project=self.project,
            group=self.group,
        )
        self.batch_c = TaskBatch.objects.create(
            name="Batch C",
            created_by=self.user,
            wav_file_name="c.wav",
            species=self.species,
            project=self.project,
            group=self.group,
        )

        # Create one undone task in each batch
        self.task_a = Task.objects.create(
            wav_file_name="a.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project,
            batch=self.batch_a,
            created_by=self.user,
            group=self.group,
            status="pending",
        )
        self.task_b = Task.objects.create(
            wav_file_name="b.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project,
            batch=self.batch_b,
            created_by=self.user,
            group=self.group,
            status="pending",
        )
        self.task_c = Task.objects.create(
            wav_file_name="c.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project,
            batch=self.batch_c,
            created_by=self.user,
            group=self.group,
            status="pending",
        )

    def test_skip_batch_cycles_through_all_batches(self):
        """Test that skip_to_next_batch cycles through all batches in order."""
        self.client.login(username="testuser", password="password123")

        # Starting from batch A, should go to batch B
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_b.id}/", response.url)

        # From batch B, should go to batch C
        url_b = reverse("battycoda_app:skip_to_next_batch", args=[self.task_b.id])
        response = self.client.get(url_b)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_c.id}/", response.url)

        # From batch C, should wrap around to batch A
        url_c = reverse("battycoda_app:skip_to_next_batch", args=[self.task_c.id])
        response = self.client.get(url_c)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_a.id}/", response.url)

    def test_skip_batch_skips_completed_batches(self):
        """Test that skip_to_next_batch skips batches with no undone tasks."""
        self.client.login(username="testuser", password="password123")

        # Mark all tasks in batch B as done
        self.task_b.is_done = True
        self.task_b.status = "done"
        self.task_b.save()

        # From batch A, should skip B and go to C
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_c.id}/", response.url)

    def test_skip_batch_stays_when_no_other_batches(self):
        """Test that skip_to_next_batch stays on current task when no other batches."""
        self.client.login(username="testuser", password="password123")

        # Mark all tasks in batches B and C as done
        self.task_b.is_done = True
        self.task_b.status = "done"
        self.task_b.save()
        self.task_c.is_done = True
        self.task_c.status = "done"
        self.task_c.save()

        # From batch A, should stay on current task
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_a.id}/", response.url)

    def test_skip_batch_with_two_batches_cycles_correctly(self):
        """Test cycling between exactly 2 batches works (edge case for wrap-around)."""
        self.client.login(username="testuser", password="password123")

        # Mark batch C as done so we only have A and B
        self.task_c.is_done = True
        self.task_c.status = "done"
        self.task_c.save()

        # From A, should go to B
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_b.id}/", response.url)

        # From B, should wrap back to A
        url_b = reverse("battycoda_app:skip_to_next_batch", args=[self.task_b.id])
        response = self.client.get(url_b)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_a.id}/", response.url)

    def test_skip_batch_skips_locked_tasks(self):
        """Test that skip_to_next_batch skips batches where all tasks are locked by others."""
        # Create another user to lock tasks
        other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="password123")
        other_profile = UserProfile.objects.get(user=other_user)
        GroupMembership.objects.create(user=other_user, group=self.group, is_admin=False)
        other_profile.group = self.group
        other_profile.save()

        self.client.login(username="testuser", password="password123")

        # Lock all tasks in batch B by another user (recent lock, not stale)
        self.task_b.status = "in_progress"
        self.task_b.in_progress_by = other_user
        self.task_b.in_progress_since = timezone.now()
        self.task_b.save()

        # From A, should skip B (locked) and go to C
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_c.id}/", response.url)

    def test_skip_batch_allows_stale_locked_tasks(self):
        """Test that skip_to_next_batch allows tasks with stale locks (>30 min)."""
        from datetime import timedelta

        # Create another user to lock tasks
        other_user = User.objects.create_user(username="otheruser", email="other@example.com", password="password123")
        other_profile = UserProfile.objects.get(user=other_user)
        GroupMembership.objects.create(user=other_user, group=self.group, is_admin=False)
        other_profile.group = self.group
        other_profile.save()

        self.client.login(username="testuser", password="password123")

        # Mark C as done so we only have A and B
        self.task_c.is_done = True
        self.task_c.status = "done"
        self.task_c.save()

        # Lock task B by another user but with a STALE lock (>30 minutes ago)
        self.task_b.status = "in_progress"
        self.task_b.in_progress_by = other_user
        self.task_b.in_progress_since = timezone.now() - timedelta(minutes=35)
        self.task_b.save()

        # From A, should be able to go to B (stale lock is available)
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_b.id}/", response.url)


class SkipToNextBatchCrossProjectTest(BattycodaTestCase):
    """Tests for skip_to_next_batch when dealing with multiple projects."""

    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        # Create test species
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )

        # Create two projects
        self.project1 = Project.objects.create(
            name="Project 1", description="First project", created_by=self.user, group=self.group
        )
        self.project2 = Project.objects.create(
            name="Project 2", description="Second project", created_by=self.user, group=self.group
        )

        # Create batches: A, B in project1; C in project2
        self.batch_a = TaskBatch.objects.create(
            name="Batch A",
            created_by=self.user,
            wav_file_name="a.wav",
            species=self.species,
            project=self.project1,
            group=self.group,
        )
        self.batch_b = TaskBatch.objects.create(
            name="Batch B",
            created_by=self.user,
            wav_file_name="b.wav",
            species=self.species,
            project=self.project1,
            group=self.group,
        )
        self.batch_c = TaskBatch.objects.create(
            name="Batch C",
            created_by=self.user,
            wav_file_name="c.wav",
            species=self.species,
            project=self.project2,
            group=self.group,
        )

        # Create tasks
        self.task_a = Task.objects.create(
            wav_file_name="a.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project1,
            batch=self.batch_a,
            created_by=self.user,
            group=self.group,
            status="pending",
        )
        self.task_b = Task.objects.create(
            wav_file_name="b.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project1,
            batch=self.batch_b,
            created_by=self.user,
            group=self.group,
            status="pending",
        )
        self.task_c = Task.objects.create(
            wav_file_name="c.wav",
            onset=1.0,
            offset=2.0,
            species=self.species,
            project=self.project2,
            batch=self.batch_c,
            created_by=self.user,
            group=self.group,
            status="pending",
        )

    def test_skip_batch_stays_in_same_project(self):
        """Test that skip prefers same-project batches."""
        self.client.login(username="testuser", password="password123")

        # From A (project1), should go to B (project1), not C (project2)
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_b.id}/", response.url)

    def test_skip_batch_falls_back_to_other_project(self):
        """Test fallback to other project when same-project batches exhausted."""
        self.client.login(username="testuser", password="password123")

        # Mark B as done, so project1 only has A
        self.task_b.is_done = True
        self.task_b.status = "done"
        self.task_b.save()

        # From A (project1), should fall back to C (project2) since no other project1 batches
        url_a = reverse("battycoda_app:skip_to_next_batch", args=[self.task_a.id])
        response = self.client.get(url_a)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_c.id}/", response.url)

    def test_skip_batch_cycles_within_project_before_fallback(self):
        """Test cycling within same project before falling back."""
        self.client.login(username="testuser", password="password123")

        # From B (project1, higher ID), should wrap to A (project1), not go to C (project2)
        url_b = reverse("battycoda_app:skip_to_next_batch", args=[self.task_b.id])
        response = self.client.get(url_b)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/tasks/annotate/{self.task_a.id}/", response.url)
