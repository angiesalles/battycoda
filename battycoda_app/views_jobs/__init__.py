"""Jobs views package."""

from .ajax import cancel_job_view, job_status_api_view
from .dashboard import jobs_dashboard_view
from .spectrogram import create_spectrogram_job_view

__all__ = [
    "jobs_dashboard_view",
    "job_status_api_view",
    "cancel_job_view",
    "create_spectrogram_job_view",
]
