"""
Safe cleanup utilities for BattyCoda.

Provides helper functions for safely cleaning up temporary files and directories
with proper error logging.
"""

import logging
import os
import shutil

logger = logging.getLogger(__name__)


def safe_remove_file(path: str, description: str = "temporary file") -> bool:
    """
    Safely remove a file, logging any errors.

    Args:
        path: Path to the file to remove
        description: Human-readable description for log messages

    Returns:
        True if file was removed or didn't exist, False on error
    """
    if not path:
        return True
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except PermissionError:
        logger.warning(f"Permission denied removing {description}: {path}")
    except OSError as e:
        logger.warning(f"OS error removing {description} {path}: {e}")
    return False


def safe_cleanup_dir(path: str, description: str = "temporary directory") -> bool:
    """
    Safely remove a directory and its contents, logging any errors.

    Args:
        path: Path to the directory to remove
        description: Human-readable description for log messages

    Returns:
        True if directory was removed or didn't exist, False on error
    """
    if not path:
        return True
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
        return True
    except PermissionError:
        logger.warning(f"Permission denied cleaning up {description}: {path}")
    except OSError as e:
        logger.warning(f"OS error cleaning up {description} {path}: {e}")
    return False
