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


def create_spectrogram_job_view(request, recording_id):
    """Create a new spectrogram generation job for a recording"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    profile = request.user.profile
    recording = get_object_or_404(Recording, id=recording_id)
    
    # Check permissions - user must be in the same group as the recording
    if not profile.group or recording.group != profile.group:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Check if a spectrogram job already exists and is pending/in_progress
    existing_job = SpectrogramJob.objects.filter(
        recording=recording,
        status__in=['pending', 'in_progress']
    ).first()
    
    if existing_job:
        return JsonResponse({
            'success': False, 
            'error': 'Spectrogram generation already in progress for this recording'
        })
    
    # Create the spectrogram job
    job = SpectrogramJob.objects.create(
        name=f"Spectrogram for {recording.name}",
        recording=recording,
        group=recording.group,
        created_by=request.user,
        status='pending',
        progress=0
    )
    
    # Queue the actual spectrogram generation task with Celery
    from .audio.task_modules.spectrogram_tasks import generate_recording_spectrogram
    
    try:
        # Start the task
        task_result = generate_recording_spectrogram.delay(recording.id)
        
        # Update job with task ID for tracking
        job.celery_task_id = task_result.id
        job.status = 'in_progress'
        job.progress = 10  # Starting progress
        job.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Spectrogram generation job started successfully',
            'job_id': job.id,
            'task_id': task_result.id
        })
    except Exception as e:
        # If task queuing fails, mark job as failed
        job.status = 'failed'
        job.error_message = f'Failed to queue task: {str(e)}'
        job.save()
        
        return JsonResponse({
            'success': False, 
            'error': f'Failed to start spectrogram generation: {str(e)}'
        })