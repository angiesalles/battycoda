"""
Path utility functions for handling file paths.
"""

import os

from django.conf import settings


def convert_path_to_os_specific(path):
    """
    Convert a web path to an OS-specific path

    Args:
        path (str): Web path (like "recordings/audio.wav")

    Returns:
        str: OS-specific path to the location in media directory
    """
    # Normalize directory separators
    path = path.replace("\\", "/")

    # Remove leading slash if present
    if path.startswith("/"):
        path = path[1:]

    # All paths now go to media folder
    return os.path.join(settings.MEDIA_ROOT, path)


def get_r_server_path(local_path: str) -> str:
    """
    Convert a local filesystem path to the path the R server expects.

    In Docker deployments, the R server may see paths differently than the Django app.
    For example, local '/home/ubuntu/battycoda/tmp' might be '/app/tmp' for R server.

    Args:
        local_path: Absolute path on the local filesystem

    Returns:
        Path as the R server expects it
    """
    base = str(settings.BASE_DIR)
    r_base = getattr(settings, "R_SERVER_BASE_PATH", base)
    return local_path.replace(base, r_base)


def get_r_server_tmp() -> str:
    """
    Get the temp directory path as the R server expects it.

    Returns:
        Temp directory path for R server
    """
    return getattr(settings, "R_SERVER_TMP_DIR", os.path.join(str(settings.BASE_DIR), "tmp"))


def get_local_tmp() -> str:
    """
    Get the local temp directory path (for Django/Celery to use).

    Returns:
        Local temp directory path
    """
    return os.path.join(settings.BASE_DIR, "tmp")


def get_species_images_path() -> str:
    """
    Get the path to species images directory.

    Returns:
        Path to data/species_images directory
    """
    return os.path.join(settings.BASE_DIR, "data", "species_images")
