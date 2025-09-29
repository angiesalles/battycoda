"""
Classification API views for the core classification workflow.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count

from .auth import api_key_required
from ..models import Recording
from ..models.classification import Classifier, ClassificationRun, ClassificationResult, CallProbability


@require_http_methods(["GET"])
@api_key_required
def simple_classifiers_list(request):
    """List available classifiers for the user"""
    user = request.api_user
    user_group = user.profile.group
    
    # Get classifiers available to the user
    if user_group:
        classifiers = Classifier.objects.filter(
            Q(group=user_group) | Q(group__isnull=True)
        ).filter(is_active=True).order_by('name')
    else:
        classifiers = Classifier.objects.filter(
            Q(created_by=user) | Q(group__isnull=True)
        ).filter(is_active=True).order_by('name')
    
    classifiers_data = []
    for classifier in classifiers:
        classifiers_data.append({
            'id': classifier.id,
            'name': classifier.name,
            'description': classifier.description or '',
            'species_name': classifier.species.name if classifier.species else 'Multi-species',
            'species_id': classifier.species.id if classifier.species else None,
            'response_format': classifier.response_format
        })
    
    return JsonResponse({
        'success': True,
        'classifiers': classifiers_data,
        'count': len(classifiers_data)
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_start_classification(request, segmentation_id):
    """Start classification on a recording's segments"""
    user = request.api_user
    
    if not user.profile.group:
        return JsonResponse({
            'success': False,
            'error': 'User must be assigned to a group to start classification'
        }, status=400)
    
    try:
        # Get the segmentation
        try:
            from ..models.recording import Segmentation
            segmentation = Segmentation.objects.get(id=segmentation_id)
        except Segmentation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Segmentation with ID {segmentation_id} not found'
            }, status=404)
        
        # Check permissions - user must have access to the recording
        recording = segmentation.recording
        user_group = user.profile.group
        if recording.created_by != user and (not user_group or recording.group != user_group):
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to classify this segmentation'
            }, status=403)
        
        # Get classifier parameters
        classifier_id = request.POST.get('classifier_id')
        name = request.POST.get('name')
        
        if not classifier_id:
            return JsonResponse({
                'success': False,
                'error': 'classifier_id is required'
            }, status=400)
        
        # Validate classifier
        try:
            classifier_id = int(classifier_id)
            
            if user_group:
                classifier = Classifier.objects.get(
                    Q(id=classifier_id) & (Q(group=user_group) | Q(group__isnull=True)) & Q(is_active=True)
                )
            else:
                classifier = Classifier.objects.get(
                    Q(id=classifier_id) & (Q(created_by=user) | Q(group__isnull=True)) & Q(is_active=True)
                )
        except (ValueError, Classifier.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': f'Classifier with ID {classifier_id} not found or not accessible'
            }, status=400)
        
        # Generate name if not provided
        if not name:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"{classifier.name}_on_{recording.name}_{timestamp}"
        
        # Create the classification run
        classification_run = ClassificationRun.objects.create(
            name=name,
            segmentation=segmentation,
            created_by=user,
            group=user_group,
            classifier=classifier,
            status='queued',
            progress=0
        )
        
        # Start the classification task
        from celery import current_app
        task = current_app.send_task(
            'battycoda_app.tasks.run_classification',
            args=[classification_run.id]
        )
        
        # Update with task ID
        classification_run.task_id = task.id
        classification_run.save(update_fields=['task_id'])
        
        return JsonResponse({
            'success': True,
            'message': f'Classification started using {classifier.name}',
            'classification_run': {
                'id': classification_run.id,
                'name': classification_run.name,
                'status': classification_run.status,
                'classifier_name': classifier.name,
                'recording_name': recording.name,
                'task_id': task.id,
                'created_at': classification_run.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to start classification: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
@api_key_required
def simple_classification_runs_list(request):
    """List classification runs and their status"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        runs = ClassificationRun.objects.filter(group=user_group).order_by('-created_at')
    else:
        runs = ClassificationRun.objects.filter(created_by=user).order_by('-created_at')
    
    # Apply recording filter if provided
    recording_id = request.GET.get('recording_id')
    if recording_id:
        try:
            recording_id = int(recording_id)
            runs = runs.filter(segmentation__recording_id=recording_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid recording_id format'
            }, status=400)
    
    # Apply project filter if provided
    project_id = request.GET.get('project_id')
    if project_id:
        try:
            project_id = int(project_id)
            runs = runs.filter(segmentation__recording__project_id=project_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid project_id format'
            }, status=400)
    
    runs_data = []
    for run in runs:
        # Get result counts if completed
        result_summary = {}
        if run.status == 'completed':
            # Get the top predicted call types and their counts
            results = ClassificationResult.objects.filter(classification_run=run)
            call_counts = {}
            
            for result in results:
                # Get the highest probability call type for this result
                top_call = CallProbability.objects.filter(
                    classification_result=result
                ).order_by('-probability').first()
                
                if top_call:
                    call_name = top_call.call.short_name
                    call_counts[call_name] = call_counts.get(call_name, 0) + 1
            
            result_summary = call_counts
        
        runs_data.append({
            'id': run.id,
            'name': run.name,
            'status': run.status,
            'progress': run.progress,
            'classifier_name': run.classifier.name if run.classifier else None,
            'classifier_id': run.classifier.id if run.classifier else None,
            'recording_name': run.segmentation.recording.name if run.segmentation else None,
            'recording_id': run.segmentation.recording.id if run.segmentation else None,
            'segmentation_id': run.segmentation.id if run.segmentation else None,
            'segmentation_name': run.segmentation.name if run.segmentation else None,
            'project_name': run.segmentation.recording.project.name if run.segmentation and run.segmentation.recording.project else None,
            'project_id': run.segmentation.recording.project.id if run.segmentation and run.segmentation.recording.project else None,
            'species_name': run.segmentation.recording.species.name if run.segmentation else None,
            'species_id': run.segmentation.recording.species.id if run.segmentation else None,
            'created_at': run.created_at.isoformat(),
            'created_by': run.created_by.username,
            'error_message': run.error_message,
            'result_summary': result_summary
        })
    
    return JsonResponse({
        'success': True,
        'classification_runs': runs_data,
        'count': len(runs_data)
    })