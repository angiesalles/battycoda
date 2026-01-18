"""
Segmentation management URL patterns.

Handles segmentation CRUD, auto-segmentation, segment management,
batch segmentation, and spectrogram data.
"""

from django.urls import path

from .views_segmentation.segment_crud import (
    add_segment_view,
    delete_segment_view,
    edit_segment_view,
)
from .views_segmentation.segment_management import (
    create_segmentation_view,
    delete_segmentation_view,
    segmentation_detail_view,
    segmentation_list_view,
)
from .views_segmentation.segmentation_batches import batch_segmentation_view, segmentation_jobs_status_view
from .views_segmentation.segmentation_execution import auto_segment_recording_view
from .views_segmentation.segmentation_import import upload_pickle_segments_view
from .views_segmentation.segmentation_preview import create_preview_recording_view
from .views_segmentation.segmentation_selection import select_recording_for_segmentation_view
from .views_segmentation.segmentation_settings import activate_segmentation_view
from .views_segmentation.segmentation_status import auto_segment_status_view
from .views_segmentation.spectrogram_data import get_spectrogram_data_view

urlpatterns = [
    path("segmentations/", segmentation_list_view, name="segmentation_list"),
    path("segmentations/create/", create_segmentation_view, name="create_segmentation"),
    path("segmentations/<int:segmentation_id>/", segmentation_detail_view, name="segmentation_detail"),
    path(
        "segmentations/<int:segmentation_id>/auto-segment/",
        auto_segment_recording_view,
        name="auto_segment_segmentation",
    ),
    path(
        "segmentations/<int:segmentation_id>/auto-segment/<int:algorithm_id>/",
        auto_segment_recording_view,
        name="auto_segment_segmentation_with_algorithm",
    ),
    path(
        "segmentations/<int:segmentation_id>/auto-segment/status/",
        auto_segment_status_view,
        name="auto_segment_segmentation_status",
    ),
    path(
        "segmentations/<int:segmentation_id>/upload-pickle/",
        upload_pickle_segments_view,
        name="upload_pickle_to_segmentation",
    ),
    path(
        "recordings/<int:recording_id>/auto-segment/",
        auto_segment_recording_view,
        name="auto_segment_recording",
    ),
    path(
        "recordings/<int:recording_id>/auto-segment/<int:algorithm_id>/",
        auto_segment_recording_view,
        name="auto_segment_recording_with_algorithm",
    ),
    path(
        "recordings/<int:recording_id>/auto-segment/status/",
        auto_segment_status_view,
        name="auto_segment_status",
    ),
    path(
        "recordings/<int:recording_id>/create-preview/",
        create_preview_recording_view,
        name="create_preview_recording",
    ),
    path(
        "recordings/<int:recording_id>/upload-pickle/",
        upload_pickle_segments_view,
        name="upload_pickle_segments",
    ),
    path("segmentation/batch-jobs/", batch_segmentation_view, name="batch_segmentation"),
    path(
        "segmentation/batch-jobs/select-recording/",
        select_recording_for_segmentation_view,
        name="select_recording_for_segmentation",
    ),
    path("segmentation/batch-jobs/status/", segmentation_jobs_status_view, name="segmentation_jobs_status"),
    path(
        "segmentations/<int:segmentation_id>/activate/",
        activate_segmentation_view,
        name="activate_segmentation",
    ),
    path("segmentations/<int:segmentation_id>/segments/add/", add_segment_view, name="add_segment"),
    path("segmentations/<int:segmentation_id>/segments/<int:segment_id>/edit/", edit_segment_view, name="edit_segment"),
    path(
        "segmentations/<int:segmentation_id>/segments/<int:segment_id>/delete/",
        delete_segment_view,
        name="delete_segment",
    ),
    path("segmentations/<int:segmentation_id>/delete/", delete_segmentation_view, name="delete_segmentation"),
    path("recordings/<int:recording_id>/spectrogram-data/", get_spectrogram_data_view, name="get_spectrogram_data"),
]
