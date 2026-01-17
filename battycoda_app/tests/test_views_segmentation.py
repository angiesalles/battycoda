"""Tests for segmentation views"""

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, Recording, Segmentation, UserProfile
from battycoda_app.models.organization import Project, Species
from battycoda_app.models.segmentation import Segment, SegmentationAlgorithm
from battycoda_app.tests.test_base import BattycodaTestCase


class SegmentationListViewTest(BattycodaTestCase):
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

        # Create a recording
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        # Create a segmentation algorithm
        self.algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.algorithm,
            status="completed",
            created_by=self.user,
        )

        # URL paths
        self.segmentation_list_url = reverse("battycoda_app:segmentation_list")

    def test_segmentation_list_view_authenticated(self):
        """Authenticated users should see the segmentation list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.segmentation_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "segmentations/segmentation_list.html")

    def test_segmentation_list_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.segmentation_list_url)
        self.assertEqual(response.status_code, 302)


class SegmentationDetailViewTest(BattycodaTestCase):
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

        # Create a segmentation algorithm
        self.algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.algorithm,
            status="completed",
            created_by=self.user,
        )

        # URL paths
        self.segmentation_detail_url = reverse("battycoda_app:segmentation_detail", args=[self.segmentation.id])

    def test_segmentation_detail_view_owner(self):
        """Segmentation owner should see the detail view"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.segmentation_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "segmentations/segmentation_detail.html")

    def test_segmentation_detail_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.segmentation_detail_url)
        self.assertEqual(response.status_code, 302)


class CreateSegmentationViewTest(BattycodaTestCase):
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

        # Create a recording
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.create_segmentation_url = reverse("battycoda_app:create_segmentation")

    def test_create_segmentation_with_recording(self):
        """Create segmentation with a recording parameter should create a segmentation"""
        self.client.login(username="testuser", password="password123")
        url = f"{self.create_segmentation_url}?recording={self.recording.id}"
        response = self.client.get(url)
        # Should redirect to the new segmentation detail
        self.assertEqual(response.status_code, 302)
        # A segmentation should have been created
        self.assertTrue(Segmentation.objects.filter(recording=self.recording).exists())

    def test_create_segmentation_without_recording(self):
        """Create segmentation without recording should redirect to recording list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.create_segmentation_url)
        # Should redirect to recording list
        self.assertEqual(response.status_code, 302)

    def test_create_segmentation_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.create_segmentation_url)
        self.assertEqual(response.status_code, 302)


class SegmentManagementViewTest(BattycodaTestCase):
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

        # Create a recording
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            group=self.group,
            created_by=self.user,
        )

        # Create a segmentation algorithm
        self.algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a segment
        self.segment = Segment.objects.create(
            recording=self.recording,
            segmentation=self.segmentation,
            onset=0.0,
            offset=1.0,
            created_by=self.user,
        )

    def test_edit_segment_view_post(self):
        """Edit segment POST should work for authenticated users"""
        self.client.login(username="testuser", password="password123")
        edit_segment_url = reverse(
            "battycoda_app:edit_segment",
            args=[self.segmentation.id, self.segment.id],
        )
        # Edit segment is an AJAX endpoint, so POST with form data
        response = self.client.post(
            edit_segment_url,
            {
                "onset": 0.5,
                "offset": 1.5,
            },
        )
        self.assertIn(response.status_code, [200, 400])  # 200 success, 400 form errors


class SegmentationBatchViewTest(BattycodaTestCase):
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
        self.batch_segmentation_url = reverse("battycoda_app:batch_segmentation")

    def test_batch_segmentation_view_get(self):
        """GET request should show the batch segmentation form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.batch_segmentation_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "segmentations/batch_segmentation.html")

    def test_batch_segmentation_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.batch_segmentation_url)
        self.assertEqual(response.status_code, 302)
