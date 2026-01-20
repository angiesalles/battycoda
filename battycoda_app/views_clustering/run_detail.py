"""Clustering run detail and status views."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from ..models.clustering import Cluster, ClusteringRun
from ..utils_modules.validation import get_int_param
from .permissions import check_clustering_permission

CLUSTERS_PER_PAGE = 50


@login_required
def clustering_run_detail(request, run_id):
    """Display details of a clustering run with paginated clusters."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to view this clustering run"
    )
    if error:
        return error

    clusters = []
    page_obj = None
    paginator = None

    if clustering_run.status == "completed":
        all_clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by("cluster_id")
        page_number = get_int_param(request, "page", default=1, min_val=1)
        paginator = Paginator(all_clusters, CLUSTERS_PER_PAGE)
        page_obj = paginator.get_page(page_number)
        clusters = page_obj

    context = {
        "clustering_run": clustering_run,
        "clusters": clusters,
        "page_obj": page_obj,
        "paginator": paginator,
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
