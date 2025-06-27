from django.urls import path, include

from .views_segmentation.segment_management import (
    add_segment_view, delete_segment_view, edit_segment_view, segment_recording_view
)
from .views_segmentation.segment_ajax import load_segments_ajax
from .views_segmentation.segmentation_batches import batch_segmentation_view, segmentation_jobs_status_view
from .views_segmentation.segmentation_execution import (
    auto_segment_recording_view, auto_segment_status_view, select_recording_for_segmentation_view
)
from .views_segmentation.segmentation_import import upload_pickle_segments_view
from .views_segmentation.segmentation_preview import preview_segmentation_view
from .views_segmentation.segmentation_settings import activate_segmentation_view

# Direct imports from views_automation
from .views_automation.results_application import apply_detection_results_view
from .views_automation.runs_details import detection_run_detail_view, detection_run_status_view, download_features_file_view
from .views_automation.runs_management import (
    automation_home_view, create_detection_run_view, delete_detection_run_view,
    classify_unclassified_segments_view, create_classification_for_species_view
)
from .views_automation.task_creation import (
    create_task_batch_from_detection_run, create_task_batches_for_species_view,
    create_tasks_for_species_view
)
from .views_automation.classifier_training import (
    classifier_list_view, create_classifier_training_job_view, 
    classifier_training_job_detail_view, classifier_training_job_status_view,
    delete_classifier_training_job_view
)

# Notification views
from .views_notifications import (
    notification_list_view, mark_notification_read, mark_all_read, get_navbar_notifications
)

# Import batch export views
from .views_batch_export import export_completed_batches

from . import (
    views_audio,
    views_audio_streaming,
    views_auth,
    views_batch_upload,
    views_chess,
    views_clustering,
    views_dashboard,
    views_debug,
    views_group,
    views_invitations,
    views_jobs,
    views_landing,
    views_project,
    views_recording_core,
    views_recordings_duplicates,
    views_species,
    views_task_annotation,
    views_task_batch,
    views_task_listing,
    views_task_navigation,
    views_tasks,
)

app_name = "battycoda_app"

urlpatterns = [
    path("", views_dashboard.index, name="index"),
    path("welcome/", views_landing.landing_page, name="landing"),
    # Authentication URLs
    path("accounts/login/", views_auth.login_view, name="login"),
    path("accounts/register/", views_auth.register_view, name="register"),
    path("accounts/logout/", views_auth.logout_view, name="logout"),
    path("accounts/profile/", views_auth.edit_profile_view, name="profile"),  # Redirect to edit profile
    path("accounts/profile/edit/", views_auth.edit_profile_view, name="edit_profile"),
    path("accounts/password-reset/", views_auth.password_reset_request, name="password_reset_request"),
    path("accounts/reset-password/<str:token>/", views_auth.password_reset, name="password_reset"),
    path("accounts/request-login-code/", views_auth.request_login_code, name="request_login_code"),
    path("accounts/enter-login-code/<str:username>/", views_auth.enter_login_code, name="enter_login_code"),
    path("accounts/login-with-token/<str:token>/", views_auth.login_with_token, name="login_with_token"),
    path("accounts/check-username/", views_auth.check_username, name="check_username"),
    path("accounts/check-email/", views_auth.check_email, name="check_email"),
    path("accounts/generate-api-key/", views_auth.generate_api_key_view, name="generate_api_key"),
    path("update_theme_preference/", views_auth.update_theme_preference, name="update_theme_preference"),
    path("update_profile_ajax/", views_auth.update_profile_ajax, name="update_profile_ajax"),
    # Admin user hijacking is now handled by django-hijack package
    # Routes for task functionality only
    # Directory and file browsing functionality removed
    # Spectrogram routes
    path("spectrogram/", views_audio.spectrogram_view, name="spectrogram"),
    path("status/task/<str:task_id>/", views_audio.task_status, name="task_status"),
    path("audio/snippet/", views_audio.audio_snippet_view, name="audio_snippet"),
    # Test static file serving (disabled - using built-in Django static file handling)
    # path('test-static/<path:filename>', views_audio.test_static_view, name='test_static'),
    # Task management routes
    path("tasks/<int:task_id>/", views_task_listing.task_detail_view, name="task_detail"),
    # Individual task creation removed - tasks are now only created through batches
    path("tasks/batches/", views_task_batch.task_batch_list_view, name="task_batch_list"),
    path("tasks/batches/<int:batch_id>/", views_task_batch.task_batch_detail_view, name="task_batch_detail"),
    path("tasks/batches/<int:batch_id>/export/", views_task_batch.export_task_batch_view, name="export_task_batch"),
    path("tasks/batches/export-completed/", export_completed_batches, name="export_completed_batches"),
    path("tasks/batches/create/", views_task_batch.create_task_batch_view, name="create_task_batch"),
    path("tasks/batches/check-name/", views_task_batch.check_taskbatch_name, name="check_taskbatch_name"),
    path("tasks/next/", views_task_navigation.get_next_task_view, name="get_next_task"),
    path("tasks/last/", views_task_navigation.get_last_task_view, name="get_last_task"),
    path(
        "tasks/batch/<int:batch_id>/annotate/",
        views_task_navigation.get_next_task_from_batch_view,
        name="annotate_batch",
    ),
    path("tasks/annotate/<int:task_id>/", views_task_annotation.task_annotation_view, name="annotate_task"),
    # Automation routes
    path("automation/", automation_home_view, name="automation_home"),
    path("automation/runs/<int:run_id>/", detection_run_detail_view, name="detection_run_detail"),
    path("automation/runs/create/", create_detection_run_view, name="create_detection_run"),
    path(
        "automation/runs/create/<int:segmentation_id>/",
        create_detection_run_view,
        name="create_detection_run_for_segmentation",
    ),
    path(
        "automation/runs/<int:run_id>/status/", detection_run_status_view, name="detection_run_status"
    ),
    path(
        "automation/runs/<int:run_id>/download-features/", 
        download_features_file_view, 
        name="download_features_file"
    ),
    path(
        "automation/runs/<int:run_id>/apply/",
        apply_detection_results_view,
        name="apply_detection_results",
    ),
    path(
        "automation/runs/<int:run_id>/apply/<int:segment_id>/",
        apply_detection_results_view,
        name="apply_detection_result_for_segment",
    ),
    path(
        "automation/runs/<int:run_id>/create-tasks/",
        create_task_batch_from_detection_run,
        name="create_task_batch_from_detection_run",
    ),
    path(
        "automation/runs/<int:run_id>/delete/", delete_detection_run_view, name="delete_detection_run"
    ),
    # Classify unclassified segments
    path(
        "automation/unclassified/",
        classify_unclassified_segments_view,
        name="classify_unclassified_segments"
    ),
    path(
        "automation/unclassified/<int:species_id>/classify/",
        create_classification_for_species_view,
        name="create_classification_for_species"
    ),
    # Create task batches from classification runs
    path(
        "automation/task-batches/",
        create_task_batches_for_species_view,
        name="create_task_batches_for_species"
    ),
    path(
        "automation/task-batches/<int:species_id>/create/",
        create_tasks_for_species_view,
        name="create_tasks_for_species"
    ),
    # Classifier training routes
    path("automation/classifiers/", classifier_list_view, name="classifier_list"),
    path(
        "automation/classifiers/create/", 
        create_classifier_training_job_view, 
        name="create_classifier_training_job"
    ),
    path(
        "automation/classifiers/create/<int:batch_id>/",
        create_classifier_training_job_view,
        name="create_classifier_training_job_for_batch"
    ),
    path(
        "automation/classifiers/<int:job_id>/",
        classifier_training_job_detail_view,
        name="classifier_training_job_detail"
    ),
    path(
        "automation/classifiers/<int:job_id>/status/",
        classifier_training_job_status_view,
        name="classifier_training_job_status"
    ),
    path(
        "automation/classifiers/<int:job_id>/delete/",
        delete_classifier_training_job_view,
        name="delete_classifier_training_job"
    ),
    # Species management routes
    path("species/", views_species.species_list_view, name="species_list"),
    path("species/<int:species_id>/", views_species.species_detail_view, name="species_detail"),
    path("species/create/", views_species.create_species_view, name="create_species"),
    path("species/<int:species_id>/edit/", views_species.edit_species_view, name="edit_species"),
    path("species/<int:species_id>/delete/", views_species.delete_species_view, name="delete_species"),
    path("species/parse-calls-file/", views_species.parse_calls_file_view, name="parse_calls_file"),
    path("species/<int:species_id>/calls/add/", views_species.add_call_view, name="add_call"),
    path("species/<int:species_id>/calls/<int:call_id>/delete/", views_species.delete_call_view, name="delete_call"),
    # Project management routes
    path("projects/", views_project.project_list_view, name="project_list"),
    path("projects/<int:project_id>/", views_project.project_detail_view, name="project_detail"),
    path("projects/create/", views_project.create_project_view, name="create_project"),
    path("projects/<int:project_id>/edit/", views_project.edit_project_view, name="edit_project"),
    path("projects/<int:project_id>/delete/", views_project.delete_project_view, name="delete_project"),
    # Group management routes
    path("groups/", views_group.group_list_view, name="group_list"),
    path("groups/<int:group_id>/", views_group.group_detail_view, name="group_detail"),
    path("groups/create/", views_group.create_group_view, name="create_group"),
    path("groups/<int:group_id>/edit/", views_group.edit_group_view, name="edit_group"),
    path("groups/<int:group_id>/members/", views_group.manage_group_members_view, name="manage_group_members"),
    path("groups/switch/<int:group_id>/", views_group.switch_group_view, name="switch_group"),
    # Group users and invitations
    path("users/", views_invitations.group_users_view, name="group_users"),
    path("users/invite/", views_invitations.invite_user_view, name="invite_user"),
    path("invitation/<str:token>/", views_invitations.accept_invitation_view, name="accept_invitation"),
    # Debug routes
    path("debug/env/", views_debug.debug_env_view, name="debug_env"),
    # Recordings management - Core views
    path("recordings/", views_recording_core.recording_list_view, name="recording_list"),
    path("recordings/<int:recording_id>/", views_recording_core.recording_detail_view, name="recording_detail"),
    path("recordings/create/", views_recording_core.create_recording_view, name="create_recording"),
    path("recordings/<int:recording_id>/edit/", views_recording_core.edit_recording_view, name="edit_recording"),
    path("recordings/<int:recording_id>/delete/", views_recording_core.delete_recording_view, name="delete_recording"),
    path("recordings/<int:recording_id>/recalculate-audio-info/", views_recording_core.recalculate_audio_info_view, name="recalculate_audio_info"),
    path("recordings/process-missing-sample-rates/", views_recording_core.process_missing_sample_rates, name="process_missing_sample_rates"),
    path("recordings/duplicates/", views_recordings_duplicates.detect_duplicate_recordings_view, name="detect_duplicate_recordings"),
    path("recordings/duplicates/remove/", views_recordings_duplicates.remove_duplicate_recordings, name="remove_duplicate_recordings"),
    # Batch Upload
    path("recordings/batch-upload/", views_batch_upload.batch_upload_recordings_view, name="batch_upload_recordings"),
    # Segmentation related views
    path("recordings/<int:recording_id>/segment/", segment_recording_view, name="segment_recording"),
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
        "recordings/<int:recording_id>/auto-segment/preview/",
        preview_segmentation_view,
        name="preview_segmentation",
    ),
    path(
        "recordings/<int:recording_id>/upload-pickle/",
        upload_pickle_segments_view,
        name="upload_pickle_segments",
    ),
    # Audio streaming and data related views
    path(
        "recordings/<int:recording_id>/waveform-data/",
        views_audio_streaming.get_audio_waveform_data,
        name="recording_waveform_data",
    ),
    path(
        "recordings/<int:recording_id>/stream/", views_audio_streaming.stream_audio_view, name="stream_recording_audio"
    ),
    # Tasks and spectrograms
    path(
        "recordings/<int:recording_id>/spectrogram-status/",
        views_tasks.recording_spectrogram_status_view,
        name="recording_spectrogram_status",
    ),
    path(
        "recordings/<int:recording_id>/create-tasks/",
        views_tasks.create_tasks_from_segments_view,
        name="create_tasks_from_segments",
    ),
    # Segmentation management
    path("segmentation/", batch_segmentation_view, name="batch_segmentation"),
    path("segmentation/select-recording/", select_recording_for_segmentation_view, name="select_recording_for_segmentation"),
    path(
        "segmentation/jobs/status/", segmentation_jobs_status_view, name="segmentation_jobs_status"
    ),
    path(
        "segmentation/<int:segmentation_id>/activate/",
        activate_segmentation_view,
        name="activate_segmentation",
    ),
    # Segment management
    path("segments/<int:recording_id>/add/", add_segment_view, name="add_segment"),
    path("segments/<int:segment_id>/edit/", edit_segment_view, name="edit_segment"),
    path("segments/<int:segment_id>/delete/", delete_segment_view, name="delete_segment"),
    path("segments/<int:recording_id>/load-ajax/", load_segments_ajax, name="load_segments_ajax"),
    
    # Notification routes
    path("notifications/", notification_list_view, name="notifications"),
    path("notifications/<int:notification_id>/read/", mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", mark_all_read, name="mark_all_read"),
    path("notifications/navbar/", get_navbar_notifications, name="get_navbar_notifications"),
    
    # Clustering routes
    path("clustering/", views_clustering.dashboard, name="clustering_dashboard"),
    path("clustering/create/", views_clustering.create_clustering_run, name="create_clustering_run"),
    path("clustering/run/<int:run_id>/", views_clustering.clustering_run_detail, name="clustering_run_detail"),
    path("clustering/run/<int:run_id>/status/", views_clustering.clustering_run_status, name="clustering_run_status"),
    path("clustering/explorer/<int:run_id>/", views_clustering.cluster_explorer, name="cluster_explorer"),
    path("clustering/mapping/<int:run_id>/", views_clustering.mapping_interface, name="map_clusters_to_calls"),
    path("clustering/export/<int:run_id>/", views_clustering.export_clusters, name="export_clusters"),
    path("clustering/export-mappings/<int:run_id>/", views_clustering.export_mappings, name="export_mappings"),
    
    # Clustering API endpoints
    path("clustering/get-cluster-data/", views_clustering.get_cluster_data, name="get_cluster_data"),
    path("clustering/update-cluster-label/", views_clustering.update_cluster_label, name="update_cluster_label"),
    path("clustering/create-mapping/", views_clustering.create_cluster_mapping, name="create_cluster_mapping"),
    path("clustering/delete-mapping/", views_clustering.delete_cluster_mapping, name="delete_cluster_mapping"),
    path("clustering/update-mapping-confidence/", views_clustering.update_mapping_confidence, name="update_mapping_confidence"),
    path("clustering/get-segment-data/", views_clustering.get_segment_data, name="get_segment_data"),
    
    # Jobs management routes
    path("jobs/", views_jobs.jobs_dashboard_view, name="jobs_dashboard"),
    path("jobs/api/status/", views_jobs.job_status_api_view, name="job_status_api"),
    path("jobs/cancel/<str:job_type>/<int:job_id>/", views_jobs.cancel_job_view, name="cancel_job"),
    path("jobs/spectrogram/create/<int:recording_id>/", views_jobs.create_spectrogram_job_view, name="create_spectrogram_job"),
    
    # Chess proxy routes (authenticated users only)
    path("chess/", views_chess.chess_home_view, name="chess_home"),
    path("chess/<path:path>", views_chess.chess_proxy_view, name="chess_proxy"),
    
    # Simple API routes (API key authentication)
    path("simple-api/", include('battycoda_app.simple_api_urls')),
]
