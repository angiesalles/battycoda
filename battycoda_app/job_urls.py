"""
Job management URL patterns.

Handles background job monitoring, status checking, and job control.
"""
from django.urls import path
from . import views_jobs

urlpatterns = [
    path("jobs/", views_jobs.jobs_dashboard_view, name="jobs_dashboard"),
    path("jobs/api/status/", views_jobs.job_status_api_view, name="job_status_api"),
    path("jobs/cancel/<str:job_type>/<int:job_id>/", views_jobs.cancel_job_view, name="cancel_job"),
    path("jobs/spectrogram/create/<int:recording_id>/", views_jobs.create_spectrogram_job_view, name="create_spectrogram_job"),
]
