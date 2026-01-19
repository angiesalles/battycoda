"""
Classification URL patterns.

Handles detection runs, classifier training, applying results,
and creating task batches from classification results.
"""

from django.urls import path

from .views_classification.batch_operations import (
    classify_unclassified_segments_view,
    create_classification_for_species_view,
)
from .views_classification.dashboard import classification_home_view
from .views_classification.folder_training import (
    create_classifier_from_folder_view,
    create_training_job_view,
    select_training_folder_view,
    training_folder_details_view,
)
from .views_classification.job_creation import (
    classifier_list_view,
    create_classifier_training_job_view,
)
from .views_classification.job_status import (
    classifier_training_job_detail_view,
    classifier_training_job_status_view,
    delete_classifier_training_job_view,
)
from .views_classification.results_application import apply_detection_results_view
from .views_classification.run_creation import create_detection_run_view, delete_detection_run_view
from .views_classification.runs_details import (
    detection_run_detail_view,
    detection_run_status_view,
    download_features_file_view,
    download_segments_zip_view,
)
from .views_classification.task_creation.batch_creation import (
    create_task_batch_from_detection_run,
    create_task_batches_for_species_view,
)
from .views_classification.task_creation.species_tasks import create_tasks_for_species_view

urlpatterns = [
    path("classification/", classification_home_view, name="classification_home"),
    path("classification/runs/<int:run_id>/", detection_run_detail_view, name="detection_run_detail"),
    path("classification/runs/create/", create_detection_run_view, name="create_detection_run"),
    path(
        "classification/runs/create/<int:segmentation_id>/",
        create_detection_run_view,
        name="create_detection_run_for_segmentation",
    ),
    path("classification/runs/<int:run_id>/status/", detection_run_status_view, name="detection_run_status"),
    path(
        "classification/runs/<int:run_id>/download-features/",
        download_features_file_view,
        name="download_features_file",
    ),
    path(
        "classification/runs/<int:run_id>/download-segments/", download_segments_zip_view, name="download_segments_zip"
    ),
    path(
        "classification/runs/<int:run_id>/apply/",
        apply_detection_results_view,
        name="apply_detection_results",
    ),
    path(
        "classification/runs/<int:run_id>/apply/<int:segment_id>/",
        apply_detection_results_view,
        name="apply_detection_result_for_segment",
    ),
    path(
        "classification/runs/<int:run_id>/create-tasks/",
        create_task_batch_from_detection_run,
        name="create_task_batch_from_detection_run",
    ),
    path("classification/runs/<int:run_id>/delete/", delete_detection_run_view, name="delete_detection_run"),
    path("classification/unclassified/", classify_unclassified_segments_view, name="classify_unclassified_segments"),
    path(
        "classification/unclassified/<int:species_id>/classify/",
        create_classification_for_species_view,
        name="create_classification_for_species",
    ),
    path("classification/task-batches/", create_task_batches_for_species_view, name="create_task_batches_for_species"),
    path(
        "classification/task-batches/<int:species_id>/create/",
        create_tasks_for_species_view,
        name="create_tasks_for_species",
    ),
    path("classification/classifiers/", classifier_list_view, name="classifier_list"),
    path(
        "classification/classifiers/create/", create_classifier_training_job_view, name="create_classifier_training_job"
    ),
    path(
        "classification/classifiers/create/<int:batch_id>/",
        create_classifier_training_job_view,
        name="create_classifier_training_job_for_batch",
    ),
    path(
        "classification/classifiers/<int:job_id>/",
        classifier_training_job_detail_view,
        name="classifier_training_job_detail",
    ),
    path(
        "classification/classifiers/<int:job_id>/status/",
        classifier_training_job_status_view,
        name="classifier_training_job_status",
    ),
    path(
        "classification/classifiers/<int:job_id>/delete/",
        delete_classifier_training_job_view,
        name="delete_classifier_training_job",
    ),
    # New cleaner URL patterns for folder training
    path(
        "classification/training-folders/",
        select_training_folder_view,
        name="select_training_folder",
    ),
    path(
        "classification/training-folders/<str:folder_name>/",
        training_folder_details_view,
        name="training_folder_details",
    ),
    path(
        "classification/training-folders/<str:folder_name>/create-job/",
        create_training_job_view,
        name="create_training_job",
    ),
    # Legacy URL patterns (maintained for backwards compatibility)
    path(
        "classification/classifiers/from-folder/",
        create_classifier_from_folder_view,
        name="create_classifier_from_folder",
    ),
    path(
        "classification/classifiers/from-folder/<str:folder_name>/",
        create_classifier_from_folder_view,
        name="create_classifier_from_folder_for_folder",
    ),
]
