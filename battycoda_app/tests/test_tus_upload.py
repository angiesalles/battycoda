"""Tests for TUS resumable upload protocol endpoint."""

import base64
import os
import uuid

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, Recording, UserProfile
from battycoda_app.models.organization import Project, Species
from battycoda_app.models.tus_upload import TusUpload
from battycoda_app.tests.test_base import BattycodaTestCase


def _encode_metadata(**kwargs):
    """Build a TUS Upload-Metadata header value from keyword args."""
    pairs = []
    for key, value in kwargs.items():
        encoded = base64.b64encode(value.encode()).decode()
        pairs.append(f"{key} {encoded}")
    return ", ".join(pairs)


class TusOptionsTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="t@t.com", password="password123")
        self.url = reverse("battycoda_app:tus_upload_create")

    def test_options_returns_tus_headers(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.options(self.url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Tus-Resumable"], "1.0.0")
        self.assertIn("creation", response["Tus-Extension"])
        self.assertIn("Tus-Max-Size", response)

    def test_options_unauthenticated(self):
        response = self.client.options(self.url)
        self.assertEqual(response.status_code, 302)


class TusCreateTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="t@t.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)
        self.group = Group.objects.create(name="Test Group")
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        self.species = Species.objects.create(name="Test Species", group=self.group, created_by=self.user)
        self.project = Project.objects.create(name="Test Project", group=self.group, created_by=self.user)
        self.url = reverse("battycoda_app:tus_upload_create")

    def test_create_upload(self):
        self.client.login(username="testuser", password="password123")
        metadata = _encode_metadata(
            filename="test.wav",
            name="My Recording",
            species_id=str(self.species.id),
            project_id=str(self.project.id),
        )
        response = self.client.post(
            self.url,
            content_type="application/octet-stream",
            HTTP_UPLOAD_LENGTH="1024",
            HTTP_UPLOAD_METADATA=metadata,
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("Location", response)
        self.assertEqual(response["Upload-Offset"], "0")

        # Verify TusUpload record created
        self.assertEqual(TusUpload.objects.count(), 1)
        upload = TusUpload.objects.first()
        self.assertEqual(upload.upload_length, 1024)
        self.assertEqual(upload.filename, "test.wav")
        self.assertEqual(upload.metadata_json["name"], "My Recording")

    def test_create_missing_upload_length(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(self.url, content_type="application/octet-stream")
        self.assertEqual(response.status_code, 400)

    def test_create_exceeds_max_size(self):
        self.client.login(username="testuser", password="password123")
        # TUS_MAX_SIZE defaults to 2GB
        huge_size = str(3 * 1024 * 1024 * 1024)  # 3 GB
        response = self.client.post(
            self.url,
            content_type="application/octet-stream",
            HTTP_UPLOAD_LENGTH=huge_size,
        )
        self.assertEqual(response.status_code, 413)

    def test_create_unauthenticated(self):
        response = self.client.post(
            self.url,
            content_type="application/octet-stream",
            HTTP_UPLOAD_LENGTH="1024",
        )
        self.assertEqual(response.status_code, 302)


class TusHeadTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="t@t.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)
        self.group = Group.objects.create(name="Test Group")
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        # Create a TusUpload directly
        from django.conf import settings

        self.upload_id = uuid.uuid4()
        self.temp_path = os.path.join(settings.TUS_UPLOAD_DIR, f"{self.upload_id}.part")
        with open(self.temp_path, "wb") as f:
            f.write(b"\x00" * 512)

        self.tus_upload = TusUpload.objects.create(
            upload_id=self.upload_id,
            upload_length=1024,
            upload_offset=512,
            temp_file_path=self.temp_path,
            filename="test.wav",
            user=self.user,
            group=self.group,
        )

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_head_returns_offset(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        response = self.client.head(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Upload-Offset"], "512")
        self.assertEqual(response["Upload-Length"], "1024")

    def test_head_not_found(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": uuid.uuid4()})
        response = self.client.head(url)
        self.assertEqual(response.status_code, 404)

    def test_head_user_isolation(self):
        """User cannot see another user's upload."""
        other = User.objects.create_user(username="other", email="o@o.com", password="password123")
        self.client.login(username="other", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        response = self.client.head(url)
        self.assertEqual(response.status_code, 404)


class TusPatchTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="t@t.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)
        self.group = Group.objects.create(name="Test Group")
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        self.species = Species.objects.create(name="Test Species", group=self.group, created_by=self.user)
        self.project = Project.objects.create(name="Test Project", group=self.group, created_by=self.user)

        from django.conf import settings

        self.upload_id = uuid.uuid4()
        self.temp_path = os.path.join(settings.TUS_UPLOAD_DIR, f"{self.upload_id}.part")
        with open(self.temp_path, "wb") as f:
            pass  # empty

        self.tus_upload = TusUpload.objects.create(
            upload_id=self.upload_id,
            upload_length=100,
            upload_offset=0,
            temp_file_path=self.temp_path,
            filename="test.wav",
            metadata_json={
                "name": "Test Rec",
                "species_id": str(self.species.id),
                "project_id": str(self.project.id),
            },
            user=self.user,
            group=self.group,
        )

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_patch_appends_chunk(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        chunk = b"\x00" * 50
        response = self.client.patch(
            url,
            data=chunk,
            content_type="application/offset+octet-stream",
            HTTP_UPLOAD_OFFSET="0",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Upload-Offset"], "50")

        # Verify file was written
        self.assertEqual(os.path.getsize(self.temp_path), 50)

    def test_patch_offset_mismatch_returns_409(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        response = self.client.patch(
            url,
            data=b"\x00" * 50,
            content_type="application/offset+octet-stream",
            HTTP_UPLOAD_OFFSET="10",  # Wrong: server is at 0
        )
        self.assertEqual(response.status_code, 409)

    def test_patch_wrong_content_type(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        response = self.client.patch(
            url,
            data=b"\x00" * 50,
            content_type="application/octet-stream",
            HTTP_UPLOAD_OFFSET="0",
        )
        self.assertEqual(response.status_code, 415)

    def test_patch_exceeds_declared_length(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        # Upload length is 100, sending 200 bytes
        response = self.client.patch(
            url,
            data=b"\x00" * 200,
            content_type="application/offset+octet-stream",
            HTTP_UPLOAD_OFFSET="0",
        )
        self.assertEqual(response.status_code, 413)

    def test_patch_completes_upload_creates_recording(self):
        """When the final chunk completes the upload, a Recording should be created."""
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})

        # Send exactly upload_length bytes
        chunk = b"\x00" * 100
        response = self.client.patch(
            url,
            data=chunk,
            content_type="application/offset+octet-stream",
            HTTP_UPLOAD_OFFSET="0",
        )
        self.assertEqual(response.status_code, 204)
        self.assertIn("X-Redirect-Url", response)

        # Recording created
        rec = Recording.objects.filter(created_by=self.user).first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.name, "Test Rec")
        self.assertEqual(rec.species, self.species)
        self.assertEqual(rec.project, self.project)

        # TusUpload record cleaned up
        self.assertFalse(TusUpload.objects.filter(upload_id=self.upload_id).exists())


class TusDeleteTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="t@t.com", password="password123")
        self.profile = UserProfile.objects.get(user=self.user)
        self.group = Group.objects.create(name="Test Group")
        GroupMembership.objects.create(user=self.user, group=self.group, is_admin=True)
        self.profile.group = self.group
        self.profile.save()

        from django.conf import settings

        self.upload_id = uuid.uuid4()
        self.temp_path = os.path.join(settings.TUS_UPLOAD_DIR, f"{self.upload_id}.part")
        with open(self.temp_path, "wb") as f:
            f.write(b"\x00" * 100)

        self.tus_upload = TusUpload.objects.create(
            upload_id=self.upload_id,
            upload_length=1024,
            upload_offset=100,
            temp_file_path=self.temp_path,
            filename="test.wav",
            user=self.user,
            group=self.group,
        )

    def test_delete_cleans_up(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": self.upload_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(TusUpload.objects.filter(upload_id=self.upload_id).exists())
        self.assertFalse(os.path.exists(self.temp_path))

    def test_delete_not_found(self):
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": uuid.uuid4()})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
