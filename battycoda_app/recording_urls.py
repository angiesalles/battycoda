"""
Recording management URL patterns.

Handles recording CRUD operations, duplicate detection, batch upload,
audio streaming, waveform data, and spectrogram operations.
"""
from django.urls import path
from . import (
    views_recording_core,
    views_recordings_duplicates,
    views_batch_upload,
    views_audio_streaming,
    views_tasks
)

urlpatterns = [
    path("recordings/", views_recording_core.recording_list_view, name="recording_list"),
    path("recordings/<int:recording_id>/", views_recording_core.recording_detail_view, name="recording_detail"),
    path("recordings/create/", views_recording_core.create_recording_view, name="create_recording"),
    path("recordings/<int:recording_id>/edit/", views_recording_core.edit_recording_view, name="edit_recording"),
    path("recordings/<int:recording_id>/delete/", views_recording_core.delete_recording_view, name="delete_recording"),
    path("recordings/<int:recording_id>/recalculate-audio-info/", views_recording_core.recalculate_audio_info_view, name="recalculate_audio_info"),
    path("recordings/process-missing-sample-rates/", views_recording_core.process_missing_sample_rates, name="process_missing_sample_rates"),
    path("recordings/duplicates/", views_recordings_duplicates.detect_duplicate_recordings_view, name="detect_duplicate_recordings"),
    path("recordings/duplicates/remove/", views_recordings_duplicates.remove_duplicate_recordings, name="remove_duplicate_recordings"),
    path("recordings/batch-upload/", views_batch_upload.batch_upload_recordings_view, name="batch_upload_recordings"),
    path(
        "recordings/<int:recording_id>/waveform-data/",
        views_audio_streaming.get_audio_waveform_data,
        name="recording_waveform_data",
    ),
    path(
        "recordings/<int:recording_id>/stream/", views_audio_streaming.stream_audio_view, name="stream_recording_audio"
    ),
    path(
        "recordings/<int:recording_id>/spectrogram-status/",
        views_tasks.recording_spectrogram_status_view,
        name="recording_spectrogram_status",
    ),
]
