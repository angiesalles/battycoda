"""
Task management API views for task batches and annotation.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.db import transaction

from .auth import api_key_required
from ..models import Task, TaskBatch
from ..models.classification import ClassificationRun, ClassificationResult, CallProbability
from ..models import Segment


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_create_task_batch(request, run_id):
    """Create task batch from completed classification"""
    user = request.api_user
    user_group = user.profile.group
    
    if not user_group:
        return JsonResponse({
            'success': False,
            'error': 'User must be assigned to a group to create task batches'
        }, status=400)
    
    try:
        # Get the classification run
        try:
            run = ClassificationRun.objects.get(id=run_id, group=user_group)
        except ClassificationRun.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Classification run with ID {run_id} not found or not accessible'
            }, status=404)
        
        if run.status != 'completed':
            return JsonResponse({
                'success': False,
                'error': 'Classification run must be completed before creating task batch'
            }, status=400)
        
        # Get parameters
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        confidence_threshold = request.POST.get('confidence_threshold')
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Task batch name is required'
            }, status=400)
        
        # Parse confidence threshold
        max_confidence = None
        if confidence_threshold:
            try:
                max_confidence = float(confidence_threshold)
                if max_confidence < 0 or max_confidence > 1:
                    raise ValueError("Confidence threshold must be between 0 and 1")
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid confidence threshold: {str(e)}'
                }, status=400)
        
        # Create task batch using transaction
        recording = run.segmentation.recording
        
        with transaction.atomic():
            # Create the task batch
            task_batch = TaskBatch.objects.create(
                name=name,
                description=description,
                created_by=user,
                wav_file_name=recording.wav_file.name if recording.wav_file else '',
                wav_file=recording.wav_file,
                species=recording.species,
                project=recording.project,
                group=user_group,
                classification_run=run
            )
            
            # Get all classification results from this run
            results = ClassificationResult.objects.filter(classification_run=run)
            
            tasks_created = 0
            for result in results:
                segment = result.segment
                
                # Skip segments that already have tasks
                if hasattr(segment, 'task') and segment.task:
                    continue
                
                # Get the highest probability call type
                top_probability = CallProbability.objects.filter(
                    classification_result=result
                ).select_related('call').order_by('-probability').first()

                # Skip if confidence threshold is set and this result's confidence is too high
                if max_confidence is not None and top_probability and top_probability.probability > max_confidence:
                    continue

                # Skip if call object is missing (broken foreign key)
                if top_probability and not top_probability.call:
                    continue

                # Create a task for this segment
                predicted_call = top_probability.call.short_name if top_probability else None
                confidence = top_probability.probability if top_probability else 0.0
                
                task = Task.objects.create(
                    wav_file_name=task_batch.wav_file_name,
                    onset=segment.onset,
                    offset=segment.offset,
                    species=task_batch.species,
                    project=task_batch.project,
                    batch=task_batch,
                    classification_result=predicted_call,
                    confidence=confidence,
                    created_by=user,
                    group=user_group
                )
                
                # Link segment to task
                segment.task = task
                segment.save(manual_edit=False)
                
                tasks_created += 1
        
        return JsonResponse({
            'success': True,
            'message': 'Task batch created successfully',
            'task_batch': {
                'id': task_batch.id,
                'name': task_batch.name,
                'description': task_batch.description,
                'species_name': task_batch.species.name if task_batch.species else None,
                'project_name': task_batch.project.name if task_batch.project else None,
                'total_tasks': tasks_created,
                'created_at': task_batch.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to create task batch: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@api_key_required
def simple_task_batches_list(request):
    """List existing task batches"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        if user.profile.is_current_group_admin:
            batches = TaskBatch.objects.filter(group=user_group).order_by('-created_at')
        else:
            batches = TaskBatch.objects.filter(created_by=user).order_by('-created_at')
    else:
        batches = TaskBatch.objects.filter(created_by=user).order_by('-created_at')
    
    # Apply project filter if provided
    project_id = request.GET.get('project_id')
    if project_id:
        try:
            project_id = int(project_id)
            batches = batches.filter(project_id=project_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid project_id format'
            }, status=400)
    
    batches_data = []
    for batch in batches:
        # Get task counts
        total_tasks = batch.tasks.count()
        completed_tasks = batch.tasks.filter(is_done=True).count()
        
        batches_data.append({
            'id': batch.id,
            'name': batch.name,
            'description': batch.description or '',
            'species_name': batch.species.name if batch.species else None,
            'species_id': batch.species.id if batch.species else None,
            'project_name': batch.project.name if batch.project else None,
            'project_id': batch.project.id if batch.project else None,
            'created_by': batch.created_by.username,
            'created_at': batch.created_at.isoformat(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        })
    
    return JsonResponse({
        'success': True,
        'task_batches': batches_data,
        'count': len(batches_data)
    })


@require_http_methods(["GET"])
@api_key_required
def simple_task_batch_tasks(request, batch_id):
    """List tasks in a batch for annotation"""
    user = request.api_user
    user_group = user.profile.group
    
    try:
        if user_group:
            if user.profile.is_current_group_admin:
                batch = TaskBatch.objects.get(id=batch_id, group=user_group)
            else:
                batch = TaskBatch.objects.get(id=batch_id, created_by=user)
        else:
            batch = TaskBatch.objects.get(id=batch_id, created_by=user)
    except TaskBatch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Task batch with ID {batch_id} not found or not accessible'
        }, status=404)
    
    # Get tasks with optional filtering
    tasks = batch.tasks.order_by('id')
    
    # Apply call type filter if provided
    call_type = request.GET.get('call_type')
    if call_type and call_type != 'all':
        tasks = tasks.filter(
            Q(label=call_type) |
            Q(label__isnull=True, classification_result=call_type) |
            Q(label='', classification_result=call_type)
        )
    
    # Simple pagination
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    
    total_tasks = tasks.count()
    tasks_page = tasks[offset:offset + limit]
    
    tasks_data = []
    for task in tasks_page:
        tasks_data.append({
            'id': task.id,
            'onset': task.onset,
            'offset': task.offset,
            'label': task.label,
            'classification_result': task.classification_result,
            'confidence': task.confidence,
            'is_done': task.is_done,
            'status': task.status,
            'annotated_by': task.annotated_by.username if task.annotated_by else None,
            'annotated_at': task.annotated_at.isoformat() if task.annotated_at else None
        })
    
    # Get available call types
    species = batch.species
    available_call_types = []
    if species:
        available_call_types = list(species.calls.values_list('short_name', flat=True))
    
    return JsonResponse({
        'success': True,
        'task_batch': {
            'id': batch.id,
            'name': batch.name,
            'description': batch.description,
            'species_name': batch.species.name if batch.species else None,
            'species_id': batch.species.id if batch.species else None,
            'project_name': batch.project.name if batch.project else None,
            'project_id': batch.project.id if batch.project else None,
            'created_by': batch.created_by.username,
            'created_at': batch.created_at.isoformat(),
            'available_call_types': available_call_types
        },
        'tasks': tasks_data,
        'pagination': {
            'total': total_tasks,
            'limit': limit,
            'offset': offset,
            'has_next': offset + limit < total_tasks,
            'has_previous': offset > 0
        }
    })