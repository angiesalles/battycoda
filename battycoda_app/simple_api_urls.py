"""
URL patterns for simple API endpoints.
These use API key authentication and are designed for easy R script access.
"""
from django.urls import path

# Import views from modular files
from .simple_api.user_views import simple_user_info, simple_generate_api_key
from .simple_api.data_views import simple_species_list, simple_projects_list, simple_recordings_list
from .simple_api.upload_views import simple_upload_recording
from .simple_api.recording_upload import upload_recording
from .simple_api.pickle_upload import upload_pickle_segmentation
from .simple_api.segmentation_views import simple_segmentation_algorithms, simple_start_segmentation
from .simple_api.classification_views import (
    simple_classifiers_list, simple_start_classification, simple_classification_runs_list
)
from .simple_api.task_views import (
    simple_create_task_batch, simple_task_batches_list, simple_task_batch_tasks
)

app_name = 'simple_api'

urlpatterns = [
    # Data listing endpoints
    path('species/', simple_species_list, name='species_list'),
    path('projects/', simple_projects_list, name='projects_list'),
    path('recordings/', simple_recordings_list, name='recordings_list'),
    
    # Upload endpoints
    path('upload/', upload_recording, name='upload_recording'),
    path('recordings/<int:recording_id>/upload-pickle/', upload_pickle_segmentation, name='upload_pickle'),
    
    # Segmentation endpoints
    path('recordings/<int:recording_id>/segment/', simple_start_segmentation, name='start_segmentation'),
    path('algorithms/', simple_segmentation_algorithms, name='segmentation_algorithms'),
    
    # Core Classification API endpoints
    path('classifiers/', simple_classifiers_list, name='classifiers_list'),
    path('recordings/<int:recording_id>/classify/', simple_start_classification, name='start_classification'),
    path('classification-runs/', simple_classification_runs_list, name='classification_runs_list'),
    path('classification-runs/<int:run_id>/create-task-batch/', simple_create_task_batch, name='create_task_batch'),
    path('task-batches/', simple_task_batches_list, name='task_batches_list'),
    path('task-batches/<int:batch_id>/tasks/', simple_task_batch_tasks, name='task_batch_tasks'),
    
    # User info and API key management
    path('user/', simple_user_info, name='user_info'),
    path('generate-key/', simple_generate_api_key, name='generate_api_key'),
]