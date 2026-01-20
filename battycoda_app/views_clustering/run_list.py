"""Clustering run list views."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from ..models.clustering import ClusteringRun
from ..utils_modules.validation import get_int_param
from .helpers import get_available_algorithms

RUNS_PER_PAGE = 20


@login_required
def dashboard(request):
    """Display a paginated list of clustering runs for the user's group."""
    group = request.user.profile.group

    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by("-created_at")
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by("-created_at")

    # Pagination
    page_number = get_int_param(request, "page", default=1, min_val=1)
    paginator = Paginator(clustering_runs, RUNS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    context = {
        "clustering_runs": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "algorithms": get_available_algorithms(request.user),
    }
    return render(request, "clustering/dashboard.html", context)
