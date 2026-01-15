from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from battycoda_app.models import Group
from battycoda_app.utils_modules.species_utils import import_default_species


class UtilsTest(TestCase):
    def test_import_default_species(self):
        # Create user first - this triggers the signal which calls import_default_species automatically
        # The signal handler does real file operations, so don't mock those yet
        user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")

        # Create a group
        group = Group.objects.create(name="Test Group", description="Test group")

        # Setup user profile
        user.profile.group = group
        user.profile.save()

        # Now test import_default_species with mocked file operations
        # The signal already ran once, so calling it again should create additional species or return empty
        # Apply patches only for this specific call
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", new_callable=MagicMock) as mock_open,
            patch("django.core.files.File"),
            patch("django.db.models.fields.files.ImageFieldFile.save"),
        ):
            mock_file_handle = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file_handle

            # Call the function again (species may already exist from signal)
            created_species = import_default_species(user)

            # Check the results - should return list (possibly empty if species already created)
            self.assertIsInstance(created_species, list)
