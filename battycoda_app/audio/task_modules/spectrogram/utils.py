"""
Utility functions for spectrogram operations.
"""

import os

from django.conf import settings


class MissingSpectrogramError(Exception):
    """Raised when a recording is missing its spectrogram.

    This error indicates a bug - spectrograms should be created automatically
    by the post_save signal when a recording is created. If this error occurs,
    check that signals are properly registered in apps.py.
    """

    pass


def ensure_hdf5_exists(recording, user):
    """
    Verify HDF5 spectrogram file exists for a recording.

    Args:
        recording: Recording model instance
        user: User requesting the spectrogram

    Returns:
        tuple: (success: bool, error_response: HttpResponse or None)

    Raises:
        MissingSpectrogramError: If spectrogram is missing. This indicates a bug -
            spectrograms should be created by the post_save signal on Recording.
    """
    if not recording.spectrogram_file:
        raise MissingSpectrogramError(
            f"Recording {recording.id} ({recording.name}) has no spectrogram. "
            "This should have been created by the post_save signal. "
            "Check that battycoda_app.signals is imported in apps.py ready()."
        )

    h5_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file)

    if not os.path.exists(h5_path):
        raise MissingSpectrogramError(
            f"Spectrogram file missing for recording {recording.id}: {h5_path}. "
            "The database references a file that doesn't exist on disk."
        )

    return True, None
