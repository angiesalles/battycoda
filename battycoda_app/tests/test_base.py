"""
Base test case for all Battycoda tests
"""

from django.test import TestCase, override_settings

from battycoda_app.tests.test_settings import PASSWORD_HASHERS, all_patches


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class BattycodaTestCase(TestCase):
    """Base test case that applies all necessary patches for testing.

    Uses MD5PasswordHasher (~100x faster than PBKDF2) for user creation.
    """

    @classmethod
    def setUpClass(cls):
        """Start all patches before any tests run"""
        super().setUpClass()

        # Start all patches
        for patch in all_patches:
            patch.start()

    @classmethod
    def tearDownClass(cls):
        """Stop all patches after all tests are done"""
        # Stop all patches
        for patch in all_patches:
            patch.stop()

        super().tearDownClass()
