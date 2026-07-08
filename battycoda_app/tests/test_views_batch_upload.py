"""Tests for batch upload views"""

import io
import zipfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, UserProfile
from battycoda_app.models.organization import Project, Species
from battycoda_app.tests.test_base import BattycodaTestCase
from battycoda_app.tests.test_views_recording import create_mock_wav_file

AJAX_HEADERS = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


def create_wav_zip(wav_names=("test.wav",), name="recordings.zip"):
    """Create an in-memory ZIP archive containing minimal valid WAV files"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for wav_name in wav_names:
            zf.writestr(wav_name, create_mock_wav_file(wav_name).read())
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="application/zip")


class BatchUploadViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        self.group = Group.objects.create(name="Test Group", description="A test group")
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        self.species = Species.objects.create(name="Test Species", group=self.group, created_by=self.user)
        self.project = Project.objects.create(name="Test Project", group=self.group, created_by=self.user)

        self.url = reverse("battycoda_app:batch_upload_recordings")
        self.client.login(username="testuser", password="password123")

    def form_data(self, **extra):
        data = {"species": self.species.id, "project": self.project.id}
        data.update(extra)
        return data

    def test_get_shows_upload_limit(self):
        """The page should expose the upload limit in context and as a form data attribute"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("max_upload_size_mb", response.context)
        self.assertContains(response, f'data-max-upload-size-mb="{response.context["max_upload_size_mb"]}"')

    def test_post_without_wav_zip_redirects(self):
        """A non-AJAX POST without a WAV ZIP should redirect back to the upload page"""
        response = self.client.post(self.url, self.form_data())
        self.assertRedirects(response, self.url)

    def test_ajax_post_without_wav_zip_returns_json_error(self):
        """An AJAX POST without a WAV ZIP should get a JSON error, not a redirect"""
        response = self.client.post(self.url, self.form_data(), **AJAX_HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("ZIP file", data["error"])

    def test_ajax_post_with_invalid_form_returns_json_error(self):
        """An AJAX POST with form errors should get a JSON error listing the fields"""
        response = self.client.post(self.url, {"wav_zip": create_wav_zip()}, **AJAX_HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("species", data["error"])

    def test_ajax_post_with_corrupt_zip_returns_json_error(self):
        """An AJAX POST with an unreadable ZIP should get a JSON error"""
        corrupt_zip = SimpleUploadedFile("bad.zip", b"not a zip archive", content_type="application/zip")
        response = self.client.post(self.url, self.form_data(wav_zip=corrupt_zip), **AJAX_HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Failed to extract", data["error"])

    def test_ajax_post_success_returns_json_with_redirect(self):
        """A successful AJAX batch upload should return counts and a redirect URL"""
        response = self.client.post(
            self.url, self.form_data(wav_zip=create_wav_zip(("one.wav", "two.wav"))), **AJAX_HEADERS
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["recordings_created"], 2)
        self.assertEqual(data["redirect_url"], reverse("battycoda_app:recording_list"))

    def test_non_ajax_post_success_still_redirects(self):
        """A successful non-AJAX batch upload should keep the redirect behavior"""
        response = self.client.post(self.url, self.form_data(wav_zip=create_wav_zip()))
        self.assertRedirects(response, reverse("battycoda_app:recording_list"))
