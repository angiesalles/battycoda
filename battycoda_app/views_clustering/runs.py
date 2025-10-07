"""Clustering run management views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Segmentation
from ..models.clustering import (Cluster, ClusteringAlgorithm, ClusteringRun)


@login_required
def dashboard(request):
    """Display a list of clustering runs for the user's group."""
    group = request.user.profile.group

    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by('-created_at')
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by('-created_at')

    if group:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            group=group
        ).order_by('name')
    else:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            created_by=request.user
        ).order_by('name')

    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(
            is_active=True,
            group__isnull=True
        ).exclude(id__in=[a.id for a in algorithms])
    )

    context = {
        'clustering_runs': clustering_runs,
        'algorithms': algorithms,
    }
    return render(request, 'clustering/dashboard.html', context)


@login_required
def create_clustering_run(request):
    """Form for creating a new clustering run."""
    group = request.user.profile.group

    if group:
        segmentations = Segmentation.objects.filter(
            recording__group=group
        ).order_by('-created_at')
    else:
        segmentations = Segmentation.objects.filter(
            created_by=request.user
        ).order_by('-created_at')

    if group:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            group=group
        ).order_by('name')
    else:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            created_by=request.user
        ).order_by('name')

    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(
            is_active=True,
            group__isnull=True
        ).exclude(id__in=[a.id for a in algorithms])
    )

    if request.method == 'POST':
        segmentation_id = request.POST.get('segmentation')
        algorithm_id = request.POST.get('algorithm')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        n_clusters = request.POST.get('n_clusters')
        feature_method = request.POST.get('feature_method', 'mfcc')

        if not all([segmentation_id, algorithm_id, name]):
            messages.error(request, "Please fill in all required fields")
            return redirect('battycoda_app:create_clustering_run')

        segmentation = get_object_or_404(Segmentation, id=segmentation_id)
        algorithm = get_object_or_404(ClusteringAlgorithm, id=algorithm_id)

        clustering_run = ClusteringRun.objects.create(
            name=name,
            description=description,
            segmentation=segmentation,
            algorithm=algorithm,
            n_clusters=int(n_clusters) if n_clusters else None,
            feature_extraction_method=feature_method,
            created_by=request.user,
            group=group,
            status='pending',
            progress=0.0
        )

        from celery import current_app

        task_name = algorithm.celery_task

        task_func = current_app.tasks.get(task_name)
        if task_func:
            task = task_func.delay(clustering_run.id)
        else:
            from ..audio.task_modules.clustering.tasks import run_clustering
            task = run_clustering.delay(clustering_run.id)

        clustering_run.task_id = task.id
        clustering_run.save()

        messages.success(request, f"Clustering run '{name}' created and submitted")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)

    context = {
        'segmentations': segmentations,
        'algorithms': algorithms,
    }
    return render(request, 'clustering/create_run.html', context)


@login_required
def clustering_run_detail(request, run_id):
    """Display details of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

    clusters = []
    if clustering_run.status == 'completed':
        clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')

    context = {
        'clustering_run': clustering_run,
        'clusters': clusters,
    }
    return render(request, 'clustering/run_detail.html', context)


@login_required
def clustering_run_status(request, run_id):
    """Check the status of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

        if not clustering_run.group and clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    return JsonResponse({
        'status': clustering_run.status,
        'progress': clustering_run.progress,
        'clusters_created': clustering_run.num_clusters_created,
    })
