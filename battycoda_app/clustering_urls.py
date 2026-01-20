"""
Clustering URL patterns.

Handles clustering run management, cluster exploration, mapping,
and cluster data API endpoints.
"""

from django.urls import path

from . import views_clustering

urlpatterns = [
    path("clustering/", views_clustering.dashboard, name="clustering_dashboard"),
    path("clustering/create/", views_clustering.create_clustering_run, name="create_clustering_run"),
    path("clustering/run/<int:run_id>/", views_clustering.clustering_run_detail, name="clustering_run_detail"),
    path("clustering/run/<int:run_id>/status/", views_clustering.clustering_run_status, name="clustering_run_status"),
    path("clustering/explorer/<int:run_id>/", views_clustering.cluster_explorer, name="cluster_explorer"),
    path("clustering/mapping/<int:run_id>/", views_clustering.mapping_interface, name="map_clusters_to_calls"),
    path("clustering/export/<int:run_id>/", views_clustering.export_clusters, name="export_clusters"),
    path("clustering/export-mappings/<int:run_id>/", views_clustering.export_mappings, name="export_mappings"),
    path("clustering/get-cluster-data/", views_clustering.get_cluster_data, name="get_cluster_data"),
    path("clustering/get-cluster-members/", views_clustering.get_cluster_members, name="get_cluster_members"),
    path("clustering/update-cluster-label/", views_clustering.update_cluster_label, name="update_cluster_label"),
    path("clustering/create-mapping/", views_clustering.create_cluster_mapping, name="create_cluster_mapping"),
    path("clustering/bulk-create-mappings/", views_clustering.bulk_create_mappings, name="bulk_create_mappings"),
    path("clustering/delete-mapping/", views_clustering.delete_cluster_mapping, name="delete_cluster_mapping"),
    path(
        "clustering/update-mapping-confidence/",
        views_clustering.update_mapping_confidence,
        name="update_mapping_confidence",
    ),
    path("clustering/get-segment-data/", views_clustering.get_segment_data, name="get_segment_data"),
    path(
        "clustering/project-segments/<int:project_id>/",
        views_clustering.get_project_segment_count,
        name="get_project_segment_count",
    ),
]
