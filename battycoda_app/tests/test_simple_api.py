"""
Tests for the Simple API endpoints.
"""

# Suppress noisy logs during tests
import logging
import secrets

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, Project
from battycoda_app.models.organization import Species
from battycoda_app.models.user import UserProfile
from battycoda_app.tests.test_base import BattycodaTestCase

logging.disable(logging.ERROR)


class SimpleAPITestCase(BattycodaTestCase):
    """Base test case for Simple API tests with common setup."""

    def setUp(self):
        self.client = Client()

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Create a test user (UserProfile is auto-created via signal)
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

        # Get the auto-created profile and update it with group and API key
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.group = self.group
        self.api_key = secrets.token_urlsafe(30)[:40]
        self.profile.api_key = self.api_key
        self.profile.save()

        # Create a system species (no group - available to all)
        self.system_species = Species.objects.create(
            name="System Species", description="A system-wide species", group=None, created_by=self.user
        )

        # Create a group species
        self.group_species = Species.objects.create(
            name="Test Species", description="A test species for the group", group=self.group, created_by=self.user
        )

        # Create a test project
        self.project = Project.objects.create(
            name="Test Project", description="A test project", group=self.group, created_by=self.user
        )

    def get_api_url(self, name, **kwargs):
        """Helper to get API URL with api_key parameter."""
        full_name = f"battycoda_app:simple_api:{name}"
        url = reverse(full_name, kwargs=kwargs) if kwargs else reverse(full_name)
        return f"{url}?api_key={self.api_key}"

    def get_api_url_no_key(self, name, **kwargs):
        """Helper to get API URL without api_key parameter."""
        full_name = f"battycoda_app:simple_api:{name}"
        return reverse(full_name, kwargs=kwargs) if kwargs else reverse(full_name)


class AuthenticationTests(SimpleAPITestCase):
    """Tests for API key authentication."""

    def test_missing_api_key_returns_401(self):
        """Request without API key should return 401."""
        url = self.get_api_url_no_key("species_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("API key", data["error"])

    def test_invalid_api_key_returns_401(self):
        """Request with invalid API key should return 401."""
        url = self.get_api_url_no_key("species_list") + "?api_key=invalid_key_12345"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertIn("error", data)

    def test_valid_api_key_succeeds(self):
        """Request with valid API key should succeed."""
        url = self.get_api_url("species_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])


class SpeciesListTests(SimpleAPITestCase):
    """Tests for the species list endpoint."""

    def test_species_list_returns_species(self):
        """Should return list of accessible species."""
        url = self.get_api_url("species_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("species", data)
        self.assertIn("count", data)

        # Should include both system species and group species
        species_names = [s["name"] for s in data["species"]]
        self.assertIn("System Species", species_names)
        self.assertIn("Test Species", species_names)

    def test_species_list_includes_required_fields(self):
        """Each species should have id, name, description."""
        url = self.get_api_url("species_list")
        response = self.client.get(url)
        data = response.json()

        for species in data["species"]:
            self.assertIn("id", species)
            self.assertIn("name", species)
            self.assertIn("description", species)


class ProjectsListTests(SimpleAPITestCase):
    """Tests for the projects list endpoint."""

    def test_projects_list_returns_projects(self):
        """Should return list of accessible projects."""
        url = self.get_api_url("projects_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("projects", data)
        self.assertIn("count", data)
        self.assertEqual(data["count"], 1)  # Only the test project

    def test_projects_list_includes_required_fields(self):
        """Each project should have required fields."""
        url = self.get_api_url("projects_list")
        response = self.client.get(url)
        data = response.json()

        for project in data["projects"]:
            self.assertIn("id", project)
            self.assertIn("name", project)
            self.assertIn("description", project)
            self.assertIn("recording_count", project)


class RecordingsListTests(SimpleAPITestCase):
    """Tests for the recordings list endpoint."""

    def test_recordings_list_empty(self):
        """Should return empty list when no recordings exist."""
        url = self.get_api_url("recordings_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("recordings", data)
        self.assertEqual(data["count"], 0)

    def test_recordings_list_project_filter(self):
        """Should filter recordings by project_id."""
        url = self.get_api_url("recordings_list") + f"&project_id={self.project.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])

    def test_recordings_list_invalid_project_id(self):
        """Should return error for invalid project_id."""
        url = self.get_api_url("recordings_list") + "&project_id=invalid"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)


class UserInfoTests(SimpleAPITestCase):
    """Tests for the user info endpoint."""

    def test_user_info_returns_user_data(self):
        """Should return current user's information."""
        url = self.get_api_url("user_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("user", data)

        user_data = data["user"]
        self.assertEqual(user_data["username"], "testuser")
        self.assertEqual(user_data["email"], "test@example.com")
        self.assertEqual(user_data["group_name"], "Test Group")
        self.assertTrue(user_data["api_key_active"])


class ClassifiersListTests(SimpleAPITestCase):
    """Tests for the classifiers list endpoint."""

    def test_classifiers_list_returns_classifiers(self):
        """Should return list of accessible classifiers."""
        url = self.get_api_url("classifiers_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("classifiers", data)
        self.assertIn("count", data)
        # Check that count matches the list length
        self.assertEqual(data["count"], len(data["classifiers"]))


class AlgorithmsListTests(SimpleAPITestCase):
    """Tests for the segmentation algorithms list endpoint."""

    def test_algorithms_list(self):
        """Should return list of segmentation algorithms."""
        url = self.get_api_url("segmentation_algorithms")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("algorithms", data)
        self.assertIn("count", data)


class ClassificationRunsListTests(SimpleAPITestCase):
    """Tests for the classification runs list endpoint."""

    def test_classification_runs_list_empty(self):
        """Should return empty list when no classification runs exist."""
        url = self.get_api_url("classification_runs_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("classification_runs", data)
        self.assertEqual(data["count"], 0)

    def test_classification_runs_list_invalid_recording_filter(self):
        """Should return error for invalid recording_id filter."""
        url = self.get_api_url("classification_runs_list") + "&recording_id=invalid"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])

    def test_classification_runs_list_invalid_project_filter(self):
        """Should return error for invalid project_id filter."""
        url = self.get_api_url("classification_runs_list") + "&project_id=invalid"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])


class TaskBatchesListTests(SimpleAPITestCase):
    """Tests for the task batches list endpoint."""

    def test_task_batches_list_empty(self):
        """Should return empty list when no task batches exist."""
        url = self.get_api_url("task_batches_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("task_batches", data)
        self.assertEqual(data["count"], 0)

    def test_task_batches_list_invalid_project_filter(self):
        """Should return error for invalid project_id filter."""
        url = self.get_api_url("task_batches_list") + "&project_id=invalid"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])


class TaskBatchTasksTests(SimpleAPITestCase):
    """Tests for the task batch tasks endpoint."""

    def test_task_batch_tasks_not_found(self):
        """Should return 404 for non-existent task batch."""
        url = self.get_api_url("task_batch_tasks", batch_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)


class APIKeyGenerationTests(SimpleAPITestCase):
    """Tests for the API key generation endpoint."""

    def test_generate_api_key_requires_post(self):
        """Generate API key should only accept POST requests."""
        url = self.get_api_url("generate_api_key")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_generate_api_key_creates_new_key(self):
        """Should generate a new API key."""
        # Get current key
        old_key = self.api_key

        url = self.get_api_url("generate_api_key")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("api_key", data)

        # New key should be different
        new_key = data["api_key"]
        self.assertNotEqual(old_key, new_key)

        # Verify new key is saved in database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.api_key, new_key)
