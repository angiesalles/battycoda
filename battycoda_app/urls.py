"""
Main URL configuration for BattyCoda.

URL patterns are organized into feature-specific modules for better maintainability.
"""

from django.urls import include, path

from . import views_audio, views_dashboard, views_landing

app_name = "battycoda_app"

urlpatterns = [
    # Core application routes
    path("", views_dashboard.index, name="index"),
    path("welcome/", views_landing.landing_page, name="landing"),
    # Audio/spectrogram routes
    path("audio/task/<int:task_id>/snippet/", views_audio.task_audio_snippet_view, name="task_audio_snippet"),
    path("audio/task/<int:task_id>/spectrogram/", views_audio.task_spectrogram_view, name="task_spectrogram"),
    path("audio/bit/", views_audio.simple_audio_bit_view, name="simple_audio_bit"),
    # Feature-specific URL modules
    path("", include("battycoda_app.auth_urls")),
    path("", include("battycoda_app.task_urls")),
    path("", include("battycoda_app.classification_urls")),
    path("", include("battycoda_app.species_urls")),
    path("", include("battycoda_app.project_urls")),
    path("", include("battycoda_app.group_urls")),
    path("", include("battycoda_app.recording_urls")),
    path("", include("battycoda_app.segmentation_urls")),
    path("", include("battycoda_app.notification_urls")),
    path("", include("battycoda_app.clustering_urls")),
    path("", include("battycoda_app.job_urls")),
    # TUS resumable upload protocol
    path("tus/", include("battycoda_app.tus_urls")),
    # Simple API routes (API key authentication)
    path("simple-api/", include("battycoda_app.simple_api_urls")),
]
