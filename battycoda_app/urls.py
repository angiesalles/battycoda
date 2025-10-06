"""
Main URL configuration for BattyCoda.

URL patterns are organized into feature-specific modules for better maintainability.
"""
from django.urls import path, include
from . import views_audio, views_chess, views_dashboard, views_debug, views_landing

app_name = "battycoda_app"

urlpatterns = [
    # Core application routes
    path("", views_dashboard.index, name="index"),
    path("welcome/", views_landing.landing_page, name="landing"),

    # Audio/spectrogram routes
    path("spectrogram/", views_audio.spectrogram_view, name="spectrogram"),
    path("status/task/<str:task_id>/", views_audio.task_status, name="task_status"),
    path("audio/snippet/", views_audio.audio_snippet_view, name="audio_snippet"),
    path("audio/bit/", views_audio.simple_audio_bit_view, name="simple_audio_bit"),

    # Debug routes
    path("debug/env/", views_debug.debug_env_view, name="debug_env"),

    # Chess proxy routes (authenticated users only)
    path("chess/", views_chess.chess_home_view, name="chess_home"),
    path("chess/<path:path>", views_chess.chess_proxy_view, name="chess_proxy"),

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

    # Simple API routes (API key authentication)
    path("simple-api/", include("battycoda_app.simple_api_urls")),
]
