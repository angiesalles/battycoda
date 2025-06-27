"""
URL patterns for simple API endpoints.
These use API key authentication and are designed for easy R script access.
"""
from django.urls import path
from . import simple_api_views

app_name = 'simple_api'

urlpatterns = [
    # Data listing endpoints
    path('species/', simple_api_views.simple_species_list, name='species_list'),
    path('projects/', simple_api_views.simple_projects_list, name='projects_list'),
    path('recordings/', simple_api_views.simple_recordings_list, name='recordings_list'),
    
    # Upload endpoint
    path('upload/', simple_api_views.simple_upload_recording, name='upload_recording'),
    
    # User info and API key management
    path('user/', simple_api_views.simple_user_info, name='user_info'),
    path('generate-key/', simple_api_views.simple_generate_api_key, name='generate_api_key'),
]