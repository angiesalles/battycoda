"""
Job management URL patterns.

Handles background job monitoring, status checking, and job control.
"""

from django.urls import path

from .views_jobs.ajax import cancel_job_view, job_status_api_view
from .views_jobs.dashboard import jobs_dashboard_view
from .views_jobs.spectrogram import create_spectrogram_job_view

urlpatterns = [
    path("jobs/", jobs_dashboard_view, name="jobs_dashboard"),
    path("jobs/api/status/", job_status_api_view, name="job_status_api"),
    path("jobs/cancel/<str:job_type>/<int:job_id>/", cancel_job_view, name="cancel_job"),
    path("jobs/spectrogram/create/<int:recording_id>/", create_spectrogram_job_view, name="create_spectrogram_job"),
]
