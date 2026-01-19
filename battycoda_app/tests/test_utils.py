import io
import pickle
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from battycoda_app.audio.modules.file_utils import (
    safe_pickle_load,
    safe_pickle_loads,
)
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


class RestrictedUnpicklerTest(TestCase):
    """Tests for the security-focused RestrictedUnpickler class."""

    def test_load_basic_list(self):
        """Test that basic lists can be loaded."""
        data = [1, 2, 3, 4, 5]
        pickled = pickle.dumps(data)
        result = safe_pickle_loads(pickled)
        self.assertEqual(result, data)

    def test_load_basic_dict(self):
        """Test that basic dicts can be loaded."""
        data = {"onsets": [0.1, 0.5, 1.0], "offsets": [0.2, 0.6, 1.1]}
        pickled = pickle.dumps(data)
        result = safe_pickle_loads(pickled)
        self.assertEqual(result, data)

    def test_load_nested_structure(self):
        """Test that nested lists/dicts can be loaded."""
        data = {"data": [[1, 2], [3, 4]], "meta": {"name": "test"}}
        pickled = pickle.dumps(data)
        result = safe_pickle_loads(pickled)
        self.assertEqual(result, data)

    def test_load_tuple(self):
        """Test that tuples can be loaded."""
        data = ([0.1, 0.2], [0.3, 0.4])
        pickled = pickle.dumps(data)
        result = safe_pickle_loads(pickled)
        self.assertEqual(result, data)

    def test_load_numpy_array(self):
        """Test that numpy arrays can be loaded."""
        try:
            import numpy as np

            data = np.array([1.0, 2.0, 3.0])
            pickled = pickle.dumps(data)
            result = safe_pickle_loads(pickled)
            self.assertTrue(np.array_equal(result, data))
        except ImportError:
            self.skipTest("numpy not available")

    def test_load_numpy_dict(self):
        """Test that dicts containing numpy arrays can be loaded."""
        try:
            import numpy as np

            data = {"onsets": np.array([0.1, 0.5]), "offsets": np.array([0.2, 0.6])}
            pickled = pickle.dumps(data)
            result = safe_pickle_loads(pickled)
            self.assertTrue(np.array_equal(result["onsets"], data["onsets"]))
            self.assertTrue(np.array_equal(result["offsets"], data["offsets"]))
        except ImportError:
            self.skipTest("numpy not available")

    def test_block_os_system(self):
        """Test that os.system calls are blocked."""
        # Create a malicious pickle that would execute os.system
        # This uses pickle's reduce protocol to call os.system
        malicious = b"cos\nsystem\n(S'echo pwned'\ntR."
        with self.assertRaises(pickle.UnpicklingError) as ctx:
            safe_pickle_loads(malicious)
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_block_subprocess(self):
        """Test that subprocess calls are blocked."""
        # Attempt to unpickle something that references subprocess
        malicious = b"csubprocess\nPopen\n(S'id'\ntR."
        with self.assertRaises(pickle.UnpicklingError) as ctx:
            safe_pickle_loads(malicious)
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_block_eval(self):
        """Test that eval/exec are blocked."""
        # Attempt to unpickle something that would call eval
        malicious = b"cbuiltins\neval\n(S'print(1)'\ntR."
        with self.assertRaises(pickle.UnpicklingError) as ctx:
            safe_pickle_loads(malicious)
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_block_arbitrary_class(self):
        """Test that arbitrary classes cannot be instantiated."""
        # Try to instantiate an arbitrary class
        malicious = b"csocket\nsocket\n(tR."
        with self.assertRaises(pickle.UnpicklingError) as ctx:
            safe_pickle_loads(malicious)
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_safe_pickle_load_file(self):
        """Test safe_pickle_load with a file object."""
        data = {"test": [1, 2, 3]}
        pickled = pickle.dumps(data)
        file_obj = io.BytesIO(pickled)
        result = safe_pickle_load(file_obj)
        self.assertEqual(result, data)
