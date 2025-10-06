"""
Species management URL patterns.

Handles species CRUD operations and call management.
"""
from django.urls import path
from . import views_species

urlpatterns = [
    path("species/", views_species.species_list_view, name="species_list"),
    path("species/<int:species_id>/", views_species.species_detail_view, name="species_detail"),
    path("species/create/", views_species.create_species_view, name="create_species"),
    path("species/<int:species_id>/edit/", views_species.edit_species_view, name="edit_species"),
    path("species/<int:species_id>/delete/", views_species.delete_species_view, name="delete_species"),
    path("species/parse-calls-file/", views_species.parse_calls_file_view, name="parse_calls_file"),
    path("species/<int:species_id>/calls/add/", views_species.add_call_view, name="add_call"),
    path("species/<int:species_id>/calls/<int:call_id>/delete/", views_species.delete_call_view, name="delete_call"),
]
