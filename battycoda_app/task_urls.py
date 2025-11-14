"""
Task management URL patterns.

Handles task viewing, task batch management, task navigation,
and task annotation.
"""
from django.urls import path
from . import views_task_listing, views_task_batch, views_task_navigation, views_task_annotation
from .views_batch_export import export_completed_batches
from .views_task_batch_management import delete_task_batch_view

urlpatterns = [
    path("tasks/<int:task_id>/", views_task_listing.task_detail_view, name="task_detail"),
    path("tasks/batches/", views_task_batch.task_batch_list_view, name="task_batch_list"),
    path("tasks/batches/<int:batch_id>/", views_task_batch.task_batch_detail_view, name="task_batch_detail"),
    path("tasks/batches/<int:batch_id>/export/", views_task_batch.export_task_batch_view, name="export_task_batch"),
    path("tasks/batches/<int:batch_id>/review/", views_task_batch.task_batch_review_view, name="task_batch_review"),
    path("tasks/batches/<int:batch_id>/delete/", delete_task_batch_view, name="delete_task_batch"),
    path("tasks/batches/export-completed/", export_completed_batches, name="export_completed_batches"),
    path("tasks/batches/create/", views_task_batch.create_task_batch_view, name="create_task_batch"),
    path("tasks/batches/check-name/", views_task_batch.check_taskbatch_name, name="check_taskbatch_name"),
    path("tasks/relabel-ajax/", views_task_batch.relabel_task_ajax, name="relabel_task_ajax"),
    path("tasks/next/", views_task_navigation.get_next_task_view, name="get_next_task"),
    path("tasks/last/", views_task_navigation.get_last_task_view, name="get_last_task"),
    path("tasks/<int:current_task_id>/skip-batch/", views_task_navigation.skip_to_next_batch_view, name="skip_to_next_batch"),
    path(
        "tasks/batch/<int:batch_id>/annotate/",
        views_task_navigation.get_next_task_from_batch_view,
        name="annotate_batch",
    ),
    path("tasks/annotate/<int:task_id>/", views_task_annotation.task_annotation_view, name="annotate_task"),
]
