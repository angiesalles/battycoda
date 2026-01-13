"""
Tests for the clustering system, including project-level clustering.
"""
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from battycoda_app.models import (
    Group,
    Project,
    Recording,
    Segment,
    Segmentation,
    SegmentationAlgorithm,
    Species,
)
from battycoda_app.models.clustering import (
    Cluster,
    ClusteringAlgorithm,
    ClusteringRun,
    ClusteringRunSegmentation,
    SegmentCluster,
)
from battycoda_app.tests.test_base import BattycodaTestCase


def create_test_segmentation_algorithm(group=None):
    """Helper to create a test segmentation algorithm."""
    return SegmentationAlgorithm.objects.create(
        name="Test Algorithm",
        description="Test segmentation algorithm",
        algorithm_type="amplitude",
        celery_task="test_task",
        is_active=True,
        group=group,
    )


def create_test_segment(segmentation, onset, offset, user):
    """Helper to create a test segment with required fields."""
    return Segment.objects.create(
        segmentation=segmentation,
        recording=segmentation.recording,
        onset=onset,
        offset=offset,
        created_by=user,
    )


class ClusteringRunModelTest(BattycodaTestCase):
    """Tests for ClusteringRun model, including project-level clustering fields."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.group = Group.objects.create(name="Test Group", description="Test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )
        self.algorithm = ClusteringAlgorithm.objects.create(
            name="K-means Test",
            algorithm_type="kmeans",
            description="Test algorithm",
            created_by=self.user,
        )

        # Create a segmentation algorithm
        self.seg_algorithm = create_test_segmentation_algorithm(self.group)

        # Create a recording and segmentation for single-file tests
        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

    def test_clustering_run_str_single_file(self):
        """Test __str__ for single-file (segmentation) scope."""
        run = ClusteringRun.objects.create(
            name="Single File Run",
            scope="segmentation",
            segmentation=self.segmentation,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(str(run), "Single File Run - Test Recording")

    def test_clustering_run_str_project_scope(self):
        """Test __str__ for project scope."""
        run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(str(run), "Project Run - Project: Test Project")

    def test_clustering_run_str_no_source(self):
        """Test __str__ when neither segmentation nor project is set."""
        run = ClusteringRun.objects.create(
            name="Orphan Run",
            scope="segmentation",
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(str(run), "Orphan Run")

    def test_recording_property_single_file(self):
        """Test recording property returns recording for single-file scope."""
        run = ClusteringRun.objects.create(
            name="Single File Run",
            scope="segmentation",
            segmentation=self.segmentation,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(run.recording, self.recording)

    def test_recording_property_project_scope(self):
        """Test recording property returns None for project scope."""
        run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertIsNone(run.recording)

    def test_recordings_property_single_file(self):
        """Test recordings property returns queryset with single recording for single-file scope."""
        run = ClusteringRun.objects.create(
            name="Single File Run",
            scope="segmentation",
            segmentation=self.segmentation,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        recordings = run.recordings
        self.assertEqual(recordings.count(), 1)
        self.assertEqual(recordings.first(), self.recording)

    def test_recordings_property_project_scope(self):
        """Test recordings property returns all project recordings for project scope."""
        # Create additional recordings in the project
        recording2 = Recording.objects.create(
            name="Test Recording 2",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )

        run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        recordings = run.recordings
        self.assertEqual(recordings.count(), 2)
        self.assertIn(self.recording, recordings)
        self.assertIn(recording2, recordings)

    def test_scope_choices(self):
        """Test that scope field has correct choices."""
        run = ClusteringRun(
            name="Test",
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        # Default should be segmentation
        self.assertEqual(run.scope, "segmentation")

        # Both choices should be valid
        run.scope = "project"
        run.full_clean()  # Should not raise

        run.scope = "segmentation"
        run.full_clean()  # Should not raise

    def test_batch_size_default(self):
        """Test that batch_size has correct default."""
        run = ClusteringRun.objects.create(
            name="Test Run",
            scope="project",
            project=self.project,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(run.batch_size, 500)

    def test_progress_message_field(self):
        """Test progress_message field."""
        run = ClusteringRun.objects.create(
            name="Test Run",
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )
        self.assertEqual(run.progress_message, "")

        run.progress_message = "Extracting features: 100/500 segments"
        run.save()
        run.refresh_from_db()
        self.assertEqual(run.progress_message, "Extracting features: 100/500 segments")


class ClusteringRunSegmentationModelTest(BattycodaTestCase):
    """Tests for ClusteringRunSegmentation junction table."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.group = Group.objects.create(name="Test Group", description="Test group")
        self.species = Species.objects.create(
            name="Test Species", description="A test species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )
        self.algorithm = ClusteringAlgorithm.objects.create(
            name="K-means Test",
            algorithm_type="kmeans",
            description="Test algorithm",
            created_by=self.user,
        )

        # Create segmentation algorithm
        self.seg_algorithm = create_test_segmentation_algorithm(self.group)

        # Create recordings and segmentations
        self.recording1 = Recording.objects.create(
            name="Recording 1",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation1 = Segmentation.objects.create(
            recording=self.recording1,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        self.recording2 = Recording.objects.create(
            name="Recording 2",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation2 = Segmentation.objects.create(
            recording=self.recording2,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        self.run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
        )

    def test_create_clustering_run_segmentation(self):
        """Test creating ClusteringRunSegmentation records."""
        crs1 = ClusteringRunSegmentation.objects.create(
            clustering_run=self.run,
            segmentation=self.segmentation1,
            segments_count=10,
            status="included",
        )
        crs2 = ClusteringRunSegmentation.objects.create(
            clustering_run=self.run,
            segmentation=self.segmentation2,
            segments_count=15,
            status="included",
        )

        self.assertEqual(self.run.included_segmentations.count(), 2)
        self.assertEqual(crs1.segments_count, 10)
        self.assertEqual(crs2.segments_count, 15)

    def test_unique_together_constraint(self):
        """Test that same segmentation can't be added twice to same run."""
        ClusteringRunSegmentation.objects.create(
            clustering_run=self.run,
            segmentation=self.segmentation1,
            segments_count=10,
        )

        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ClusteringRunSegmentation.objects.create(
                clustering_run=self.run,
                segmentation=self.segmentation1,
                segments_count=20,
            )

    def test_status_choices(self):
        """Test status field values."""
        crs = ClusteringRunSegmentation.objects.create(
            clustering_run=self.run,
            segmentation=self.segmentation1,
            segments_count=10,
            status="included",
        )
        self.assertEqual(crs.status, "included")

        crs.status = "skipped"
        crs.save()
        crs.refresh_from_db()
        self.assertEqual(crs.status, "skipped")


class ClusteringViewsTest(BattycodaTestCase):
    """Tests for clustering views and API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.group = Group.objects.create(name="Test Group", description="Test group")

        # Update user profile to use this group
        from battycoda_app.models import UserProfile

        profile = UserProfile.objects.get(user=self.user)
        profile.group = self.group
        profile.save()

        self.species1 = Species.objects.create(
            name="Species One", description="First species", created_by=self.user, group=self.group
        )
        self.species2 = Species.objects.create(
            name="Species Two", description="Second species", created_by=self.user, group=self.group
        )

        self.project = Project.objects.create(
            name="Test Project", description="A test project", created_by=self.user, group=self.group
        )

        # Create segmentation algorithm
        self.seg_algorithm = create_test_segmentation_algorithm(self.group)

        # Create recordings with different species
        self.recording1 = Recording.objects.create(
            name="Recording 1",
            project=self.project,
            species=self.species1,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation1 = Segmentation.objects.create(
            recording=self.recording1,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )
        # Create segments
        for i in range(5):
            create_test_segment(self.segmentation1, i * 0.1, (i + 1) * 0.1, self.user)

        self.recording2 = Recording.objects.create(
            name="Recording 2",
            project=self.project,
            species=self.species2,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation2 = Segmentation.objects.create(
            recording=self.recording2,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )
        for i in range(3):
            create_test_segment(self.segmentation2, i * 0.1, (i + 1) * 0.1, self.user)

        self.algorithm = ClusteringAlgorithm.objects.create(
            name="K-means Test",
            algorithm_type="kmeans",
            description="Test algorithm",
            created_by=self.user,
        )

        self.client.login(username="testuser", password="password123")

    def test_get_project_segment_count_single_species(self):
        """Test API returns correct counts for single species."""
        # Create a project with only one species
        project2 = Project.objects.create(
            name="Single Species Project", created_by=self.user, group=self.group
        )
        recording = Recording.objects.create(
            name="Single Species Recording",
            project=project2,
            species=self.species1,
            created_by=self.user,
            group=self.group,
        )
        segmentation = Segmentation.objects.create(
            recording=recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )
        for i in range(7):
            create_test_segment(segmentation, i * 0.1, (i + 1) * 0.1, self.user)

        response = self.client.get(
            reverse("battycoda_app:get_project_segment_count", args=[project2.id])
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data["species"]), 1)
        self.assertEqual(data["species"][0]["name"], "Species One")
        self.assertEqual(data["species"][0]["segment_count"], 7)

    def test_get_project_segment_count_multiple_species(self):
        """Test API returns species breakdown for multi-species project."""
        response = self.client.get(
            reverse("battycoda_app:get_project_segment_count", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data["species"]), 2)

        # Find species by name
        species_dict = {s["name"]: s for s in data["species"]}
        self.assertEqual(species_dict["Species One"]["segment_count"], 5)
        self.assertEqual(species_dict["Species Two"]["segment_count"], 3)

    def test_get_project_segment_count_with_species_filter(self):
        """Test API returns filtered counts when species parameter provided."""
        response = self.client.get(
            reverse("battycoda_app:get_project_segment_count", args=[self.project.id]),
            {"species": self.species1.id},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["species_name"], "Species One")
        self.assertEqual(data["segment_count"], 5)
        self.assertEqual(data["recording_count"], 1)

    def test_get_project_segment_count_permission_denied(self):
        """Test API returns 403 for projects user doesn't have access to."""
        other_group = Group.objects.create(name="Other Group")
        other_project = Project.objects.create(
            name="Other Project", created_by=self.user, group=other_group
        )

        response = self.client.get(
            reverse("battycoda_app:get_project_segment_count", args=[other_project.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_get_cluster_members_returns_recording_info_for_project_scope(self):
        """Test that get_cluster_members includes recording info for project-level runs."""
        # Create a project-level clustering run with results
        run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species1,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
            status="completed",
        )
        cluster = Cluster.objects.create(
            clustering_run=run,
            cluster_id=0,
            size=2,
        )
        segment1 = self.segmentation1.segments.first()
        SegmentCluster.objects.create(
            segment=segment1,
            cluster=cluster,
            confidence=0.9,
        )

        response = self.client.get(
            reverse("battycoda_app:get_cluster_members"),
            {"cluster_id": cluster.id},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data["is_project_scope"])
        self.assertEqual(len(data["members"]), 1)
        self.assertIn("recording_name", data["members"][0])
        self.assertEqual(data["members"][0]["recording_name"], "Recording 1")

    def test_get_cluster_members_no_recording_info_for_single_file(self):
        """Test that get_cluster_members excludes recording info for single-file runs."""
        run = ClusteringRun.objects.create(
            name="Single File Run",
            scope="segmentation",
            segmentation=self.segmentation1,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
            status="completed",
        )
        cluster = Cluster.objects.create(
            clustering_run=run,
            cluster_id=0,
            size=1,
        )
        segment = self.segmentation1.segments.first()
        SegmentCluster.objects.create(
            segment=segment,
            cluster=cluster,
            confidence=0.85,
        )

        response = self.client.get(
            reverse("battycoda_app:get_cluster_members"),
            {"cluster_id": cluster.id},
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertFalse(data["is_project_scope"])
        self.assertNotIn("recording_name", data["members"][0])


class ClusteringExportTest(BattycodaTestCase):
    """Tests for clustering export functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.group = Group.objects.create(name="Test Group", description="Test group")

        from battycoda_app.models import UserProfile

        profile = UserProfile.objects.get(user=self.user)
        profile.group = self.group
        profile.save()

        self.species = Species.objects.create(
            name="Test Species", created_by=self.user, group=self.group
        )
        self.project = Project.objects.create(
            name="Test Project", created_by=self.user, group=self.group
        )

        # Create segmentation algorithm
        self.seg_algorithm = create_test_segmentation_algorithm(self.group)

        self.recording = Recording.objects.create(
            name="Test Recording",
            project=self.project,
            species=self.species,
            created_by=self.user,
            group=self.group,
        )
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )
        self.segment = create_test_segment(self.segmentation, 0.0, 0.1, self.user)
        self.algorithm = ClusteringAlgorithm.objects.create(
            name="K-means Test",
            algorithm_type="kmeans",
            created_by=self.user,
        )

        self.client.login(username="testuser", password="password123")

    def test_export_clusters_single_file_no_recording_columns(self):
        """Test that single-file export doesn't include recording columns."""
        run = ClusteringRun.objects.create(
            name="Single File Run",
            scope="segmentation",
            segmentation=self.segmentation,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
            status="completed",
        )
        cluster = Cluster.objects.create(
            clustering_run=run,
            cluster_id=0,
            size=1,
        )
        SegmentCluster.objects.create(
            segment=self.segment,
            cluster=cluster,
            confidence=0.9,
        )

        response = self.client.get(
            reverse("battycoda_app:export_clusters", args=[run.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")
        header = lines[0]

        self.assertNotIn("recording_id", header)
        self.assertNotIn("recording_name", header)
        self.assertIn("segment_id", header)

    def test_export_clusters_project_scope_includes_recording_columns(self):
        """Test that project-level export includes recording columns."""
        run = ClusteringRun.objects.create(
            name="Project Run",
            scope="project",
            project=self.project,
            species=self.species,
            algorithm=self.algorithm,
            created_by=self.user,
            group=self.group,
            status="completed",
        )
        cluster = Cluster.objects.create(
            clustering_run=run,
            cluster_id=0,
            size=1,
        )
        SegmentCluster.objects.create(
            segment=self.segment,
            cluster=cluster,
            confidence=0.9,
        )

        response = self.client.get(
            reverse("battycoda_app:export_clusters", args=[run.id])
        )
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        lines = content.strip().split("\n")
        header = lines[0]

        self.assertIn("recording_id", header)
        self.assertIn("recording_name", header)

        # Verify data row includes recording info
        if len(lines) > 1:
            data_row = lines[1]
            self.assertIn("Test Recording", data_row)
