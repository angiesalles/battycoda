"""Tests for recording views"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, Recording, UserProfile
from battycoda_app.models.organization import Project, Species
from battycoda_app.tests.test_base import BattycodaTestCase


def create_mock_wav_file(name="test.wav"):
    """Create a minimal valid WAV file for testing"""
    # Create a minimal WAV header (44 bytes) with silence
    wav_header = bytes(
        [
            0x52,
            0x49,
            0x46,
            0x46,  # "RIFF"
            0x24,
            0x00,
            0x00,
            0x00,  # File size - 8
            0x57,
            0x41,
            0x56,
            0x45,  # "WAVE"
            0x66,
            0x6D,
            0x74,
            0x20,  # "fmt "
            0x10,
            0x00,
            0x00,
            0x00,  # Subchunk1Size (16 for PCM)
            0x01,
            0x00,  # AudioFormat (1 = PCM)
            0x01,
            0x00,  # NumChannels (1)
            0x44,
            0xAC,
            0x00,
            0x00,  # SampleRate (44100)
            0x88,
            0x58,
            0x01,
            0x00,  # ByteRate
            0x02,
            0x00,  # BlockAlign
            0x10,
            0x00,  # BitsPerSample (16)
            0x64,
            0x61,
            0x74,
            0x61,  # "data"
            0x00,
            0x00,
            0x00,
            0x00,  # Subchunk2Size (0 bytes of audio)
        ]
    )
    return SimpleUploadedFile(name, wav_header, content_type="audio/wav")


class RecordingListViewTest(BattycodaTestCase):
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

        # Create a species and project
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name="Test Project",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.recording_list_url = reverse("battycoda_app:recording_list")

    def test_recording_list_view_authenticated(self):
        """Authenticated users should see the recording list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.recording_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordings/recording_list.html")
        self.assertIn("recordings", response.context)

    def test_recording_list_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.recording_list_url)
        self.assertEqual(response.status_code, 302)

    def test_recording_list_filters_by_project(self):
        """Recording list should filter by project when specified"""
        self.client.login(username="testuser", password="password123")

        # Create a recording
        recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        response = self.client.get(f"{self.recording_list_url}?project={self.project.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_project_id"], self.project.id)


class RecordingDetailViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test users
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species and project
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name="Test Project",
            group=self.group,
            created_by=self.user,
        )

        # Create a recording with a mock wav file
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
            wav_file=create_mock_wav_file("test_recording.wav"),
        )

        # URL paths
        self.recording_detail_url = reverse("battycoda_app:recording_detail", args=[self.recording.id])

    def test_recording_detail_view_owner(self):
        """Recording owner should see the detail view"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.recording_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordings/recording_detail.html")
        self.assertEqual(response.context["recording"].name, "Test Recording")

    def test_recording_detail_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.recording_detail_url)
        self.assertEqual(response.status_code, 302)

    def test_recording_detail_view_non_group_member(self):
        """Non-group members should be denied access"""
        self.client.login(username="testuser2", password="password123")
        response = self.client.get(self.recording_detail_url)
        self.assertEqual(response.status_code, 302)  # Redirected to list


class CreateRecordingViewTest(BattycodaTestCase):
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

        # Create a species and project
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name="Test Project",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.create_recording_url = reverse("battycoda_app:create_recording")

    def test_create_recording_view_get(self):
        """GET request should show the create recording form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.create_recording_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordings/create_recording.html")
        self.assertIn("form", response.context)

    def test_create_recording_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.create_recording_url)
        self.assertEqual(response.status_code, 302)


class EditRecordingViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test users
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species and project
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name="Test Project",
            group=self.group,
            created_by=self.user,
        )

        # Create a recording
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.edit_recording_url = reverse("battycoda_app:edit_recording", args=[self.recording.id])

    def test_edit_recording_view_get_owner(self):
        """Recording owner should see the edit form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.edit_recording_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordings/edit_recording.html")
        self.assertIn("form", response.context)

    def test_edit_recording_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.edit_recording_url)
        self.assertEqual(response.status_code, 302)

    def test_edit_recording_view_non_group_member(self):
        """Non-group members should be denied access"""
        self.client.login(username="testuser2", password="password123")
        response = self.client.get(self.edit_recording_url)
        self.assertEqual(response.status_code, 302)  # Redirected to list

    def test_edit_recording_post_success(self):
        """POST request with valid data should update recording"""
        self.client.login(username="testuser", password="password123")
        recording_data = {
            "name": "Updated Recording Name",
            "description": "Updated description",
            "species": self.species.id,
            "project": self.project.id,
        }
        response = self.client.post(self.edit_recording_url, recording_data)
        self.assertEqual(response.status_code, 302)  # Redirects to detail

        self.recording.refresh_from_db()
        self.assertEqual(self.recording.name, "Updated Recording Name")


class DeleteRecordingViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test users
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)

        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="password123")

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # Create a species and project
        self.species = Species.objects.create(
            name="Test Species",
            group=self.group,
            created_by=self.user,
        )
        self.project = Project.objects.create(
            name="Test Project",
            group=self.group,
            created_by=self.user,
        )

        # Create a recording
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.delete_recording_url = reverse("battycoda_app:delete_recording", args=[self.recording.id])

    def test_delete_recording_view_get(self):
        """GET request should show the delete confirmation page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.delete_recording_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "recordings/delete_recording.html")

    def test_delete_recording_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.delete_recording_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_recording_view_non_group_member(self):
        """Non-group members should be denied access"""
        self.client.login(username="testuser2", password="password123")
        response = self.client.get(self.delete_recording_url)
        self.assertEqual(response.status_code, 302)  # Redirected to list

    def test_delete_recording_post_success(self):
        """POST request should delete the recording"""
        self.client.login(username="testuser", password="password123")
        recording_id = self.recording.id
        response = self.client.post(self.delete_recording_url)
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertFalse(Recording.objects.filter(id=recording_id).exists())
