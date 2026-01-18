"""Clustering run list views."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models.clustering import ClusteringRun
from .helpers import get_available_algorithms


@login_required
def dashboard(request):
    """Display a list of clustering runs for the user's group."""
    group = request.user.profile.group

    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by("-created_at")
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by("-created_at")

    context = {
        "clustering_runs": clustering_runs,
        "algorithms": get_available_algorithms(request.user),
    }
    return render(request, "clustering/dashboard.html", context)
