"""
Backward compatibility shim for jobs views.

This module provides backward compatibility by importing views from the new
views_jobs package structure.
"""
from .views_jobs import (cancel_job_view, create_spectrogram_job_view,
                         job_status_api_view, jobs_dashboard_view)

__all__ = [
    'jobs_dashboard_view',
    'job_status_api_view',
    'cancel_job_view',
    'create_spectrogram_job_view',
]
