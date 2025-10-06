"""
Project management URL patterns.

Handles project CRUD operations.
"""
from django.urls import path
from . import views_project

urlpatterns = [
    path("projects/", views_project.project_list_view, name="project_list"),
    path("projects/<int:project_id>/", views_project.project_detail_view, name="project_detail"),
    path("projects/create/", views_project.create_project_view, name="create_project"),
    path("projects/<int:project_id>/edit/", views_project.edit_project_view, name="edit_project"),
    path("projects/<int:project_id>/delete/", views_project.delete_project_view, name="delete_project"),
]
