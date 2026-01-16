"""Tests for clustering views"""
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from battycoda_app.models import Group, GroupMembership, Recording, Segmentation, UserProfile
from battycoda_app.models.clustering import Cluster, ClusteringAlgorithm, ClusteringRun
from battycoda_app.models.organization import Project, Species
from battycoda_app.models.segmentation import SegmentationAlgorithm
from battycoda_app.tests.test_base import BattycodaTestCase


class ClusteringDashboardViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

        # Set as active group
        self.profile.group = self.group
        # is_current_group_admin is derived from GroupMembership.is_admin
        self.profile.save()

        # URL paths
        self.dashboard_url = reverse("battycoda_app:clustering_dashboard")

    def test_dashboard_view_authenticated(self):
        """Authenticated users should see the clustering dashboard"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clustering/dashboard.html")
        self.assertIn("clustering_runs", response.context)

    def test_dashboard_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)


class CreateClusteringRunViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # URL paths
        self.create_clustering_url = reverse("battycoda_app:create_clustering_run")

    def test_create_clustering_view_get(self):
        """GET request should show the create clustering run form"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.create_clustering_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clustering/create_run.html")
        self.assertIn("algorithms", response.context)

    def test_create_clustering_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.create_clustering_url)
        self.assertEqual(response.status_code, 302)


class ClusteringRunDetailViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test users
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="password123"
        )

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # Create a clustering run
        self.clustering_run = ClusteringRun.objects.create(
            name="Test Clustering Run",
            segmentation=self.segmentation,
            algorithm=self.clustering_algorithm,
            status="completed",
            scope="segmentation",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.clustering_detail_url = reverse(
            "battycoda_app:clustering_run_detail", args=[self.clustering_run.id]
        )

    def test_clustering_detail_view_owner(self):
        """Clustering run owner should see the detail view"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.clustering_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clustering/run_detail.html")

    def test_clustering_detail_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.clustering_detail_url)
        self.assertEqual(response.status_code, 302)


class ClusterExplorerViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # Create a clustering run
        self.clustering_run = ClusteringRun.objects.create(
            name="Test Clustering Run",
            segmentation=self.segmentation,
            algorithm=self.clustering_algorithm,
            status="completed",
            scope="segmentation",
            group=self.group,
            created_by=self.user,
        )

        # Create a cluster
        self.cluster = Cluster.objects.create(
            clustering_run=self.clustering_run,
            cluster_id=0,
            label="Cluster 0",
            size=5,
        )

        # URL paths
        self.cluster_explorer_url = reverse(
            "battycoda_app:cluster_explorer", args=[self.clustering_run.id]
        )

    def test_cluster_explorer_view_authenticated(self):
        """Authenticated users should see the cluster explorer"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.cluster_explorer_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clustering/cluster_explorer.html")

    def test_cluster_explorer_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.cluster_explorer_url)
        self.assertEqual(response.status_code, 302)


class ClusterMappingViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # Create a clustering run
        self.clustering_run = ClusteringRun.objects.create(
            name="Test Clustering Run",
            segmentation=self.segmentation,
            algorithm=self.clustering_algorithm,
            status="completed",
            scope="segmentation",
            group=self.group,
            created_by=self.user,
        )

        # URL paths
        self.mapping_url = reverse(
            "battycoda_app:map_clusters_to_calls", args=[self.clustering_run.id]
        )

    def test_mapping_view_authenticated(self):
        """Authenticated users should see the mapping interface"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.mapping_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clustering/mapping_interface.html")

    def test_mapping_view_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.get(self.mapping_url)
        self.assertEqual(response.status_code, 302)


class ClusteringAPIViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # Create a clustering run
        self.clustering_run = ClusteringRun.objects.create(
            name="Test Clustering Run",
            segmentation=self.segmentation,
            algorithm=self.clustering_algorithm,
            status="completed",
            scope="segmentation",
            group=self.group,
            created_by=self.user,
        )

        # Create a cluster
        self.cluster = Cluster.objects.create(
            clustering_run=self.clustering_run,
            cluster_id=0,
            label="Cluster 0",
            size=5,
        )

    def test_get_cluster_data_authenticated(self):
        """Authenticated users should get cluster data"""
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:get_cluster_data")
        response = self.client.get(f"{url}?cluster_id={self.cluster.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Check that we got cluster data (status, cluster_id, label etc)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("cluster_id", data)

    def test_get_cluster_data_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        url = reverse("battycoda_app:get_cluster_data")
        response = self.client.get(f"{url}?cluster_id={self.cluster.id}")
        self.assertEqual(response.status_code, 302)

    def test_get_cluster_members_authenticated(self):
        """Authenticated users should get cluster members"""
        self.client.login(username="testuser", password="password123")
        url = reverse("battycoda_app:get_cluster_members")
        response = self.client.get(f"{url}?cluster_id={self.cluster.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("members", data)

    def test_clustering_run_status_authenticated(self):
        """Authenticated users should get clustering run status"""
        self.client.login(username="testuser", password="password123")
        url = reverse(
            "battycoda_app:clustering_run_status", args=[self.clustering_run.id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)


class ClusterLabelUpdateViewTest(BattycodaTestCase):
    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.profile = UserProfile.objects.get(user=self.user)

        # Create a test group
        self.group = Group.objects.create(name="Test Group", description="A test group")

        # Add user to the group
        self.membership = GroupMembership.objects.create(
            user=self.user, group=self.group, is_admin=True
        )

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
        self.seg_algorithm = SegmentationAlgorithm.objects.create(
            name="Test Algorithm",
            algorithm_type="amplitude",
        )

        # Create a segmentation
        self.segmentation = Segmentation.objects.create(
            recording=self.recording,
            algorithm=self.seg_algorithm,
            status="completed",
            created_by=self.user,
        )

        # Create a clustering algorithm
        self.clustering_algorithm = ClusteringAlgorithm.objects.create(
            name="K-Means",
            algorithm_type="kmeans",
            is_active=True,
            created_by=self.user,
        )

        # Create a clustering run
        self.clustering_run = ClusteringRun.objects.create(
            name="Test Clustering Run",
            segmentation=self.segmentation,
            algorithm=self.clustering_algorithm,
            status="completed",
            scope="segmentation",
            group=self.group,
            created_by=self.user,
        )

        # Create a cluster
        self.cluster = Cluster.objects.create(
            clustering_run=self.clustering_run,
            cluster_id=0,
            label="Original Label",
            size=5,
        )

        # URL paths
        self.update_label_url = reverse("battycoda_app:update_cluster_label")

    def test_update_cluster_label_post(self):
        """POST request should update cluster label"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            self.update_label_url,
            {"cluster_id": self.cluster.id, "label": "New Label"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")

        self.cluster.refresh_from_db()
        self.assertEqual(self.cluster.label, "New Label")

    def test_update_cluster_label_unauthenticated(self):
        """Unauthenticated users should be redirected"""
        response = self.client.post(
            self.update_label_url,
            {"cluster_id": self.cluster.id, "label": "New Label"},
        )
        self.assertEqual(response.status_code, 302)
