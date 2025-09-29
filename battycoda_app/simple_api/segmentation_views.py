"""
Segmentation API views.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .auth import api_key_required
from ..models import Recording
from ..models.recording import SegmentationAlgorithm, Segmentation


@require_http_methods(["GET"])
@api_key_required
def simple_segmentation_algorithms(request):
    """List available segmentation algorithms for the user"""
    user = request.api_user
    user_group = user.profile.group
    
    # Get algorithms available to the user
    if user_group and user.profile.is_current_group_admin:
        # Admin sees global algorithms and group-specific ones
        algorithms = SegmentationAlgorithm.objects.filter(
            is_active=True
        ).filter(
            Q(group__isnull=True) | Q(group=user_group)
        ).order_by('name')
    else:
        # Regular users see only global algorithms
        algorithms = SegmentationAlgorithm.objects.filter(
            is_active=True, group__isnull=True
        ).order_by('name')
    
    algorithms_data = []
    for alg in algorithms:
        algorithms_data.append({
            'id': alg.id,
            'name': alg.name,
            'description': alg.description or '',
            'algorithm_type': alg.algorithm_type,
            'default_min_duration_ms': alg.default_min_duration_ms,
            'default_smooth_window': alg.default_smooth_window,
            'default_threshold_factor': alg.default_threshold_factor
        })
    
    return JsonResponse({
        'success': True,
        'algorithms': algorithms_data,
        'count': len(algorithms_data)
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_start_segmentation(request, recording_id):
    """Start segmentation for a specific recording"""
    user = request.api_user
    
    # Get the recording
    try:
        recording = Recording.objects.get(id=recording_id)
    except Recording.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Recording with ID {recording_id} not found'
        }, status=404)
    
    # Check permissions
    user_group = user.profile.group
    if recording.created_by != user and (not user_group or recording.group != user_group):
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to segment this recording'
        }, status=403)
    
    # Get algorithm parameters
    algorithm_id = request.POST.get('algorithm_id')
    min_duration_ms = request.POST.get('min_duration_ms', 10)
    smooth_window = request.POST.get('smooth_window', 3)
    threshold_factor = request.POST.get('threshold_factor', 0.5)
    
    # Get the algorithm
    if algorithm_id:
        try:
            algorithm_id = int(algorithm_id)
            # Check if user has access to this algorithm
            if user_group and user.profile.is_current_group_admin:
                algorithm = SegmentationAlgorithm.objects.filter(
                    id=algorithm_id, is_active=True
                ).filter(
                    Q(group__isnull=True) | Q(group=user_group)
                ).first()
            else:
                algorithm = SegmentationAlgorithm.objects.filter(
                    id=algorithm_id, is_active=True, group__isnull=True
                ).first()
                
            if not algorithm:
                return JsonResponse({
                    'success': False,
                    'error': f'Algorithm with ID {algorithm_id} not found or not accessible'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid algorithm_id format'
            }, status=400)
    else:
        # Use the first available algorithm as default
        if user_group and user.profile.is_current_group_admin:
            algorithm = SegmentationAlgorithm.objects.filter(
                is_active=True
            ).filter(
                Q(group__isnull=True) | Q(group=user_group)
            ).order_by('name').first()
        else:
            algorithm = SegmentationAlgorithm.objects.filter(
                is_active=True, group__isnull=True
            ).order_by('name').first()
            
        if not algorithm:
            return JsonResponse({
                'success': False,
                'error': 'No segmentation algorithms available'
            }, status=400)
    
    # Validate parameters
    try:
        min_duration_ms = int(min_duration_ms)
        smooth_window = int(smooth_window)
        threshold_factor = float(threshold_factor)
        
        if min_duration_ms < 1:
            raise ValueError("Minimum duration must be at least 1ms")
        if smooth_window < 1:
            raise ValueError("Smooth window must be at least 1 sample")
        if threshold_factor <= 0 or threshold_factor > 10:
            raise ValueError("Threshold factor must be between 0 and 10")
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid parameter: {str(e)}'
        }, status=400)
    
    # Start the segmentation
    try:
        from celery import current_app
        from django.db import transaction
        
        # Create a Segmentation entry to track this job
        segmentation = Segmentation.objects.create(
            recording=recording,
            name=f"{algorithm.name}",
            created_by=user,
            algorithm=algorithm,
            task_id="pending",
            status="in_progress",
            progress=0,
            manually_edited=False,
        )
        
        # Launch Celery task
        task = current_app.send_task(
            algorithm.celery_task,
            args=[recording.id, segmentation.id, min_duration_ms, smooth_window, threshold_factor, False],
        )
        
        # Update the segmentation with the actual task ID
        segmentation.task_id = task.id
        segmentation.save(update_fields=['task_id'])
        
        # No need to manage is_active field anymore
        
        return JsonResponse({
            'success': True,
            'message': f'Segmentation started using {algorithm.name}',
            'segmentation': {
                'id': segmentation.id,
                'name': segmentation.name,
                'algorithm_name': algorithm.name,
                'task_id': task.id,
                'status': segmentation.status,
                'created_at': segmentation.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to start segmentation: {str(e)}'
        }, status=500)