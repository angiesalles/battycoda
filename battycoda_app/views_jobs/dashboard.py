"""
Views for managing long-running background jobs in BattyCoda.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from celery.result import AsyncResult
from celery import current_app
from django.core.paginator import Paginator
from django.contrib import messages

from battycoda_app.models.classification import ClassifierTrainingJob, ClassificationRun
from battycoda_app.models import Segmentation
from battycoda_app.models.clustering import ClusteringRun
from battycoda_app.models.spectrogram import SpectrogramJob
from battycoda_app.models import Recording


def jobs_dashboard_view(request):
    """Display a dashboard of all long-running jobs for the user"""
    profile = request.user.profile
    
    # Initialize context
    context = {
        'segmentation_jobs': [],
        'classification_jobs': [],
        'detection_jobs': [],
        'clustering_jobs': [],
        'training_jobs': [],
        'spectrogram_jobs': [],
    }
    
    if profile.group:
        # Get active segmentation jobs (pending/in_progress only)
        if profile.is_current_group_admin:
            segmentations_active = Segmentation.objects.filter(
                recording__group=profile.group,
                recording__hidden=False,  # Exclude hidden recordings
                status__in=['pending', 'in_progress']
            ).order_by('-created_at')
            
            # Get recent completed/failed for display (last 10)
            segmentations_recent = Segmentation.objects.filter(
                recording__group=profile.group,
                recording__hidden=False,  # Exclude hidden recordings
                status__in=['completed', 'failed']
            ).order_by('-created_at')[:10]
        else:
            segmentations_active = Segmentation.objects.filter(
                created_by=request.user,
                status__in=['pending', 'in_progress']
            ).order_by('-created_at')
            
            # Get recent completed/failed for display (last 10)
            segmentations_recent = Segmentation.objects.filter(
                created_by=request.user,
                status__in=['completed', 'failed']
            ).order_by('-created_at')[:10]
        
        # Combine active and recent for display
        segmentations = list(segmentations_active) + list(segmentations_recent)
        
        context['segmentation_jobs'] = segmentations
        context['segmentation_active_count'] = segmentations_active.count()
        
        # Get classification/detection runs
        if profile.is_current_group_admin:
            detection_runs_active = ClassificationRun.objects.filter(
                group=profile.group,
                status__in=['queued', 'pending', 'in_progress']
            ).order_by('-created_at')
            
            detection_runs_recent = ClassificationRun.objects.filter(
                group=profile.group,
                status__in=['completed', 'failed']
            ).order_by('-created_at')[:10]
        else:
            detection_runs_active = ClassificationRun.objects.filter(
                created_by=request.user,
                status__in=['queued', 'pending', 'in_progress']
            ).order_by('-created_at')
            
            detection_runs_recent = ClassificationRun.objects.filter(
                created_by=request.user,
                status__in=['completed', 'failed']
            ).order_by('-created_at')[:10]
        
        detection_runs = list(detection_runs_active) + list(detection_runs_recent)
        
        context['detection_jobs'] = detection_runs
        context['detection_active_count'] = detection_runs_active.count()
        
        # Get classifier training jobs
        if profile.is_current_group_admin:
            training_jobs = ClassifierTrainingJob.objects.filter(
                group=profile.group
            ).order_by('-created_at')[:20]
        else:
            training_jobs = ClassifierTrainingJob.objects.filter(
                created_by=request.user
            ).order_by('-created_at')[:20]
        
        context['training_jobs'] = training_jobs
        
        # Get clustering jobs
        if profile.is_current_group_admin:
            clustering_runs = ClusteringRun.objects.filter(
                group=profile.group,
                status__in=['pending', 'running', 'completed', 'failed']
            ).order_by('-created_at')[:20]
        else:
            clustering_runs = ClusteringRun.objects.filter(
                created_by=request.user,
                status__in=['pending', 'running', 'completed', 'failed']
            ).order_by('-created_at')[:20]

        context['clustering_jobs'] = clustering_runs
        
        # Get spectrogram jobs
        if profile.is_current_group_admin:
            spectrogram_jobs = SpectrogramJob.objects.filter(
                recording__group=profile.group
            ).order_by('-created_at')[:20]
        else:
            spectrogram_jobs = SpectrogramJob.objects.filter(
                created_by=request.user
            ).order_by('-created_at')[:20]
        
        context['spectrogram_jobs'] = spectrogram_jobs

    return render(request, 'jobs/dashboard.html', context)
