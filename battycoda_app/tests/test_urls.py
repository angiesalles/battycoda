from django.contrib.auth.models import User
from django.urls import reverse

from battycoda_app.tests.test_base import BattycodaTestCase


class UrlsTest(BattycodaTestCase):
    """Test that URL patterns resolve correctly."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

    def test_index_url_resolves(self):
        """Test that index URL resolves."""
        url = reverse("battycoda_app:index")
        self.assertEqual(url, "/")

    def test_auth_urls_resolve(self):
        """Test that authentication URLs resolve."""
        self.assertEqual(reverse("battycoda_app:login"), "/accounts/login/")
        self.assertEqual(reverse("battycoda_app:register"), "/accounts/register/")
        self.assertEqual(reverse("battycoda_app:logout"), "/accounts/logout/")
        self.assertEqual(reverse("battycoda_app:profile"), "/accounts/profile/")

    def test_group_urls_resolve(self):
        """Test that group URLs resolve."""
        self.assertEqual(reverse("battycoda_app:group_list"), "/groups/")
        self.assertEqual(reverse("battycoda_app:create_group"), "/groups/create/")
        self.assertEqual(reverse("battycoda_app:group_detail", args=[1]), "/groups/1/")

    def test_task_urls_resolve(self):
        """Test that task URLs resolve."""
        self.assertEqual(reverse("battycoda_app:task_batch_list"), "/tasks/batches/")
        self.assertEqual(reverse("battycoda_app:task_batch_detail", args=[1]), "/tasks/batches/1/")

    def test_species_urls_resolve(self):
        """Test that species URLs resolve."""
        self.assertEqual(reverse("battycoda_app:species_list"), "/species/")
        self.assertEqual(reverse("battycoda_app:species_detail", args=[1]), "/species/1/")
        self.assertEqual(reverse("battycoda_app:create_species"), "/species/create/")

    def test_recording_urls_resolve(self):
        """Test that recording URLs resolve."""
        self.assertEqual(reverse("battycoda_app:recording_list"), "/recordings/")

    def test_project_urls_resolve(self):
        """Test that project URLs resolve."""
        self.assertEqual(reverse("battycoda_app:project_list"), "/projects/")

    def test_classification_urls_resolve(self):
        """Test that classification URLs resolve."""
        self.assertEqual(reverse("battycoda_app:classification_home"), "/classification/")


class URLEndpointTestCase(BattycodaTestCase):
    """Test that URL endpoints return correct status codes."""

    def setUp(self):
        """Set up test user and login."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_index_requires_authentication(self):
        """Test that index redirects unauthenticated users."""
        self.client.logout()
        url = reverse("battycoda_app:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # Index redirects to /welcome/ for unauthenticated users
        self.assertIn("/welcome/", response.url)

    def test_index_accessible_when_authenticated(self):
        """Test that authenticated users can access index."""
        url = reverse("battycoda_app:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_login_page_accessible(self):
        """Test that login page is accessible."""
        self.client.logout()
        url = reverse("battycoda_app:login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_register_page_accessible(self):
        """Test that register page is accessible."""
        self.client.logout()
        url = reverse("battycoda_app:register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_species_list_requires_authentication(self):
        """Test that species list requires authentication."""
        self.client.logout()
        url = reverse("battycoda_app:species_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_species_list_accessible_when_authenticated(self):
        """Test that authenticated users can access species list."""
        url = reverse("battycoda_app:species_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recording_list_requires_authentication(self):
        """Test that recording list requires authentication."""
        self.client.logout()
        url = reverse("battycoda_app:recording_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_project_list_requires_authentication(self):
        """Test that project list requires authentication."""
        self.client.logout()
        url = reverse("battycoda_app:project_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_task_batch_list_requires_authentication(self):
        """Test that task batch list requires authentication."""
        self.client.logout()
        url = reverse("battycoda_app:task_batch_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_classification_home_requires_authentication(self):
        """Test that classification home requires authentication."""
        self.client.logout()
        url = reverse("battycoda_app:classification_home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
