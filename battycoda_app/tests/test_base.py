"""
Base test case for all Battycoda tests
"""

import logging

from django.test import TestCase, override_settings

from battycoda_app.tests.test_settings import PASSWORD_HASHERS, all_patches


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHERS)
class BattycodaTestCase(TestCase):
    """Base test case that applies all necessary patches for testing.

    - Uses MD5PasswordHasher (~100x faster than PBKDF2) for user creation
    - Suppresses noisy logs (INFO/WARNING/ERROR) to keep test output clean
    """

    @classmethod
    def setUpClass(cls):
        """Start all patches before any tests run"""
        super().setUpClass()

        # Suppress all logging below CRITICAL to keep test output clean
        logging.disable(logging.ERROR)

        # Start all patches
        for patch in all_patches:
            patch.start()

    @classmethod
    def tearDownClass(cls):
        """Stop all patches after all tests are done"""
        # Stop all patches
        for patch in all_patches:
            patch.stop()

        # Re-enable logging
        logging.disable(logging.NOTSET)

        super().tearDownClass()
