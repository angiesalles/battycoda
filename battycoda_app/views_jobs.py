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

from .models.detection import ClassifierTrainingJob, DetectionRun
from .models.recording import Segmentation
from .models.clustering import ClusteringRun
from .models.spectrogram import SpectrogramJob
from .models.recording import Recording


@login_required
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
        # Get segmentation jobs
        if profile.is_current_group_admin:
            segmentations = Segmentation.objects.filter(
                recording__group=profile.group,
                status__in=['pending', 'in_progress', 'completed', 'failed']
            ).order_by('-created_at')[:20]
        else:
            segmentations = Segmentation.objects.filter(
                created_by=request.user,
                status__in=['pending', 'in_progress', 'completed', 'failed']
            ).order_by('-created_at')[:20]
        
        context['segmentation_jobs'] = segmentations
        
        # Get classification/detection runs
        if profile.is_current_group_admin:
            detection_runs = DetectionRun.objects.filter(
                group=profile.group,
                status__in=['pending', 'running', 'completed', 'failed']
            ).order_by('-created_at')[:20]
        else:
            detection_runs = DetectionRun.objects.filter(
                created_by=request.user,
                status__in=['pending', 'running', 'completed', 'failed']
            ).order_by('-created_at')[:20]
        
        context['detection_jobs'] = detection_runs
        
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
        
        # Get clustering jobs (if clustering is available)
        try:
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
        except:
            # Clustering module not available
            context['clustering_jobs'] = []
        
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


@login_required
def job_status_api_view(request):
    """API endpoint to get the status of multiple jobs"""
    profile = request.user.profile
    
    # Get all active (non-completed) jobs
    jobs_status = {
        'segmentation_jobs': [],
        'detection_jobs': [],
        'training_jobs': [],
        'clustering_jobs': [],
        'spectrogram_jobs': [],
    }
    
    if profile.group:
        # Filter jobs by user permissions
        if profile.is_current_group_admin:
            # Admin sees all group jobs
            segmentations = Segmentation.objects.filter(
                recording__group=profile.group,
                status__in=['pending', 'in_progress']
            )
            detection_runs = DetectionRun.objects.filter(
                group=profile.group,
                status__in=['pending', 'running']
            )
            training_jobs = ClassifierTrainingJob.objects.filter(
                group=profile.group,
                status__in=['pending', 'running']
            )
            try:
                clustering_runs = ClusteringRun.objects.filter(
                    group=profile.group,
                    status__in=['pending', 'running']
                )
            except:
                clustering_runs = []
            
            spectrogram_jobs = SpectrogramJob.objects.filter(
                recording__group=profile.group,
                status__in=['pending', 'in_progress']
            )
        else:
            # Regular user sees only their own jobs
            segmentations = Segmentation.objects.filter(
                created_by=request.user,
                status__in=['pending', 'in_progress']
            )
            detection_runs = DetectionRun.objects.filter(
                created_by=request.user,
                status__in=['pending', 'running']
            )
            training_jobs = ClassifierTrainingJob.objects.filter(
                created_by=request.user,
                status__in=['pending', 'running']
            )
            try:
                clustering_runs = ClusteringRun.objects.filter(
                    created_by=request.user,
                    status__in=['pending', 'running']
                )
            except:
                clustering_runs = []
            
            spectrogram_jobs = SpectrogramJob.objects.filter(
                created_by=request.user,
                status__in=['pending', 'in_progress']
            )
        
        # Format segmentation jobs
        for seg in segmentations:
            jobs_status['segmentation_jobs'].append({
                'id': seg.id,
                'name': f"Segmentation: {seg.recording.name}",
                'status': seg.status,
                'created_at': seg.created_at.isoformat(),
                'progress': seg.progress if hasattr(seg, 'progress') else None,
                'url': f"/recordings/{seg.recording.id}/",
            })
        
        # Format detection jobs
        for run in detection_runs:
            jobs_status['detection_jobs'].append({
                'id': run.id,
                'name': f"Classification: {run.name}",
                'status': run.status,
                'created_at': run.created_at.isoformat(),
                'progress': run.progress if hasattr(run, 'progress') else None,
                'url': f"/automation/runs/{run.id}/",
            })
        
        # Format training jobs
        for job in training_jobs:
            jobs_status['training_jobs'].append({
                'id': job.id,
                'name': f"Training: {job.name}",
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'progress': job.progress if hasattr(job, 'progress') else None,
                'url': f"/automation/classifiers/{job.id}/",
            })
        
        # Format clustering jobs
        for run in clustering_runs:
            jobs_status['clustering_jobs'].append({
                'id': run.id,
                'name': f"Clustering: {run.name}",
                'status': run.status,
                'created_at': run.created_at.isoformat(),
                'progress': run.progress if hasattr(run, 'progress') else None,
                'url': f"/clustering/run/{run.id}/",
            })
        
        # Format spectrogram jobs
        for job in spectrogram_jobs:
            jobs_status['spectrogram_jobs'].append({
                'id': job.id,
                'name': f"Spectrogram: {job.recording.name}",
                'status': job.status,
                'created_at': job.created_at.isoformat(),
                'progress': job.progress,
                'url': f"/recordings/{job.recording.id}/",
            })
    
    return JsonResponse(jobs_status)


@login_required
def cancel_job_view(request, job_type, job_id):
    """Cancel a specific job"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'})
    
    profile = request.user.profile
    
    try:
        # Get the job based on type and ID
        if job_type == 'segmentation':
            job = Segmentation.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.recording.group == profile.group
            ):
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Cancel the job if possible
            if job.status in ['pending', 'in_progress']:
                job.status = 'cancelled'
                job.save()
                return JsonResponse({'success': True, 'message': 'Segmentation job cancelled'})
        
        elif job_type == 'detection':
            job = DetectionRun.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.group == profile.group
            ):
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Cancel the job if possible
            if job.status in ['pending', 'running']:
                job.status = 'cancelled'
                job.save()
                return JsonResponse({'success': True, 'message': 'Detection job cancelled'})
        
        elif job_type == 'training':
            job = ClassifierTrainingJob.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.group == profile.group
            ):
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Cancel the job if possible
            if job.status in ['pending', 'running']:
                job.status = 'cancelled'
                job.save()
                return JsonResponse({'success': True, 'message': 'Training job cancelled'})
        
        elif job_type == 'clustering':
            try:
                job = ClusteringRun.objects.get(id=job_id)
                # Check permissions
                if job.created_by != request.user and not (
                    profile.is_current_group_admin and job.group == profile.group
                ):
                    return JsonResponse({'success': False, 'error': 'Permission denied'})
                
                # Cancel the job if possible
                if job.status in ['pending', 'running']:
                    job.status = 'cancelled'
                    job.save()
                    return JsonResponse({'success': True, 'message': 'Clustering job cancelled'})
            except:
                return JsonResponse({'success': False, 'error': 'Clustering not available'})
        
        elif job_type == 'spectrogram':
            job = SpectrogramJob.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.recording.group == profile.group
            ):
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            # Cancel the job if possible
            if job.status in ['pending', 'in_progress']:
                job.status = 'cancelled'
                job.save()
                return JsonResponse({'success': True, 'message': 'Spectrogram job cancelled'})
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid job type'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Job not found or cannot be cancelled'})


@login_required
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