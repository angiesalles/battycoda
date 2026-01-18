"""Clustering run detail and status views."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from ..models.clustering import Cluster, ClusteringRun
from .permissions import check_clustering_permission


@login_required
def clustering_run_detail(request, run_id):
    """Display details of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to view this clustering run"
    )
    if error:
        return error

    clusters = []
    if clustering_run.status == "completed":
        clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by("cluster_id")

    context = {
        "clustering_run": clustering_run,
        "clusters": clusters,
    }
    return render(request, "clustering/run_detail.html", context)


@login_required
def clustering_run_status(request, run_id):
    """Check the status of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(request, clustering_run, json_response=True)
    if error:
        return error

    return JsonResponse(
        {
            "status": clustering_run.status,
            "progress": clustering_run.progress,
            "progress_message": clustering_run.progress_message,
            "clusters_created": clustering_run.num_clusters_created,
        }
    )
