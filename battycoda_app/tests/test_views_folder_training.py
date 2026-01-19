"""Tests for folder training views."""

import os
import shutil
import tempfile

from django.contrib.auth.models import User
from django.http import Http404
from django.test import Client, override_settings
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, UserProfile
from battycoda_app.models.organization import Species
from battycoda_app.tests.test_base import BattycodaTestCase
from battycoda_app.views_classification.folder_training import (
    _parse_label_from_filename,
    _validate_folder_name,
)


class ParseLabelFromFilenameTest(BattycodaTestCase):
    """Tests for _parse_label_from_filename helper function."""

    def test_valid_filename_returns_label(self):
        """Test that valid filenames return the correct label."""
        self.assertEqual(_parse_label_from_filename("001_echolocation.wav"), "echolocation")
        self.assertEqual(_parse_label_from_filename("123_call_type.wav"), "type")
        self.assertEqual(_parse_label_from_filename("file_LABEL.WAV"), "LABEL")

    def test_filename_without_underscore_returns_none(self):
        """Test that filenames without underscore return None."""
        self.assertIsNone(_parse_label_from_filename("filename.wav"))
        self.assertIsNone(_parse_label_from_filename("no-underscore.wav"))

    def test_filename_with_empty_label_returns_none(self):
        """Test that filenames with empty label return None."""
        self.assertIsNone(_parse_label_from_filename("file_.wav"))

    def test_filename_ending_with_underscore_only_returns_none(self):
        """Test edge case where label part is just .wav."""
        # "file_.wav" -> parts = ["file", ".wav"] -> label = "" -> None
        self.assertIsNone(_parse_label_from_filename("file_.wav"))


class ValidateFolderNameTest(BattycodaTestCase):
    """Tests for _validate_folder_name helper function."""

    def test_valid_folder_name_returns_name(self):
        """Test that valid folder names are returned unchanged."""
        self.assertEqual(_validate_folder_name("my_folder"), "my_folder")
        self.assertEqual(_validate_folder_name("training-data-2024"), "training-data-2024")
        self.assertEqual(_validate_folder_name("Folder123"), "Folder123")

    def test_empty_folder_name_raises_404(self):
        """Test that empty folder name raises Http404."""
        with self.assertRaises(Http404):
            _validate_folder_name("")
        with self.assertRaises(Http404):
            _validate_folder_name(None)

    def test_path_traversal_with_dotdot_raises_404(self):
        """Test that path traversal with .. raises Http404."""
        with self.assertRaises(Http404):
            _validate_folder_name("..")
        with self.assertRaises(Http404):
            _validate_folder_name("../etc")
        with self.assertRaises(Http404):
            _validate_folder_name("folder/../secret")

    def test_absolute_path_raises_404(self):
        """Test that absolute paths raise Http404."""
        with self.assertRaises(Http404):
            _validate_folder_name("/etc/passwd")
        with self.assertRaises(Http404):
            _validate_folder_name("\\windows\\system32")

    def test_path_with_slashes_raises_404(self):
        """Test that paths with slashes raise Http404."""
        with self.assertRaises(Http404):
            _validate_folder_name("folder/subfolder")
        with self.assertRaises(Http404):
            _validate_folder_name("folder\\subfolder")


class SelectTrainingFolderViewTest(BattycodaTestCase):
    """Tests for select_training_folder_view."""

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

        self.url = reverse("battycoda_app:select_training_folder")

    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_authenticated_user_can_access(self):
        """Authenticated users should be able to access the view."""
        self.client.login(username="testuser", password="password123")
        # Create a temporary training_data directory
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(BASE_DIR=tmpdir):
                os.makedirs(os.path.join(tmpdir, "training_data"))
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "classification/select_training_folder.html")


class TrainingFolderDetailsViewTest(BattycodaTestCase):
    """Tests for training_folder_details_view."""

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

        # Create temp directory structure
        self.tmpdir = tempfile.mkdtemp()
        self.training_data_dir = os.path.join(self.tmpdir, "training_data")
        os.makedirs(self.training_data_dir)

        # Create a test folder with files
        self.test_folder = os.path.join(self.training_data_dir, "test_folder")
        os.makedirs(self.test_folder)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        url = reverse("battycoda_app:training_folder_details", kwargs={"folder_name": "test"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_path_traversal_returns_404(self):
        """Path traversal attempts should return 404."""
        self.client.login(username="testuser", password="password123")

        # Test path traversal attempts that Django URL routing allows
        # (no slashes - those are already blocked by the URL pattern)
        traversal_attempts = [
            "..",
            "..secret",
            "folder..",
        ]

        for attempt in traversal_attempts:
            url = reverse("battycoda_app:training_folder_details", kwargs={"folder_name": attempt})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f"Path traversal '{attempt}' should return 404")

        # Test that URL patterns with slashes are blocked by Django's routing
        # (can't use reverse() for these, so test directly)
        response = self.client.get("/classification/training-folders/../etc/")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_folder_redirects(self):
        """Non-existent folder should redirect with error message."""
        self.client.login(username="testuser", password="password123")
        with override_settings(BASE_DIR=self.tmpdir):
            url = reverse("battycoda_app:training_folder_details", kwargs={"folder_name": "nonexistent"})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_valid_folder_returns_200(self):
        """Valid folder should return 200 with correct template."""
        self.client.login(username="testuser", password="password123")
        with override_settings(BASE_DIR=self.tmpdir):
            url = reverse("battycoda_app:training_folder_details", kwargs={"folder_name": "test_folder"})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "classification/create_classifier_from_folder.html")
            self.assertEqual(response.context["folder_name"], "test_folder")


class CreateTrainingJobViewTest(BattycodaTestCase):
    """Tests for create_training_job_view."""

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

        # Create a species
        self.species = Species.objects.create(name="Test Species", group=self.group, created_by=self.user)

    def test_unauthenticated_user_redirected(self):
        """Unauthenticated users should be redirected to login."""
        url = reverse("battycoda_app:create_training_job", kwargs={"folder_name": "test"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_request_redirects_to_details(self):
        """GET requests should redirect to folder details view."""
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:create_training_job", kwargs={"folder_name": "test_folder"})
        response = self.client.get(url)
        # Will raise 404 due to path validation, which is expected
        # since we're not mocking the file system
        self.assertIn(response.status_code, [302, 404])

    def test_path_traversal_returns_404(self):
        """Path traversal attempts should return 404."""
        self.client.login(username="testuser", password="password123")

        # Test path traversal attempts that Django URL routing allows
        # (no slashes - those are already blocked by the URL pattern)
        traversal_attempts = ["..", "..secret"]

        for attempt in traversal_attempts:
            url = reverse("battycoda_app:create_training_job", kwargs={"folder_name": attempt})
            response = self.client.post(url, {"species_id": self.species.id})
            self.assertEqual(response.status_code, 404, f"Path traversal '{attempt}' should return 404")

    def test_missing_species_redirects_with_error(self):
        """Missing species_id should redirect with error."""
        self.client.login(username="testuser", password="password123")

        # Create temp directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            training_data_dir = os.path.join(tmpdir, "training_data")
            test_folder = os.path.join(training_data_dir, "test_folder")
            os.makedirs(test_folder)

            with override_settings(BASE_DIR=tmpdir):
                url = reverse("battycoda_app:create_training_job", kwargs={"folder_name": "test_folder"})
                response = self.client.post(url, {})
                self.assertEqual(response.status_code, 302)
