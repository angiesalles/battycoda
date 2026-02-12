"""URL patterns for TUS resumable upload protocol."""

from django.urls import path

from .views_tus_upload import tus_upload_view

urlpatterns = [
    path("", tus_upload_view, name="tus_upload_create"),
    path("<uuid:upload_id>", tus_upload_view, name="tus_upload_chunk"),
]
