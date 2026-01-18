"""
Batch upload views package.

Split from views_batch_upload.py into focused modules:
- zip_extraction.py: ZIP archive handling
- file_processing.py: WAV/recording/segmentation creation
- views.py: Main view function
"""

from .views import batch_upload_recordings_view

__all__ = ["batch_upload_recordings_view"]
