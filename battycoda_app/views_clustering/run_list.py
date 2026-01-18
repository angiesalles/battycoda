"""Clustering run list views."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models.clustering import ClusteringAlgorithm, ClusteringRun


@login_required
def dashboard(request):
    """Display a list of clustering runs for the user's group."""
    group = request.user.profile.group

    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by("-created_at")
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by("-created_at")

    if group:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(group=group).order_by("name")
    else:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(created_by=request.user).order_by("name")

    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(is_active=True, group__isnull=True).exclude(
            id__in=[a.id for a in algorithms]
        )
    )

    context = {
        "clustering_runs": clustering_runs,
        "algorithms": algorithms,
    }
    return render(request, "clustering/dashboard.html", context)
