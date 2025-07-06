"""
Celery tasks for asynchronous task batch creation.
"""
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from ..models.classification import ClassificationResult, CallProbability, ClassificationRun
from ..models.task import Task, TaskBatch
from ..models.recording import Segment
from ..models.notification import UserNotification


@shared_task(bind=True, name="battycoda_app.tasks.create_task_batch_async")
def create_task_batch_async(self, run_id, batch_name, description, max_confidence, user_id):
    """
    Asynchronously create a task batch from a classification run.
    
    Args:
        run_id: ID of the ClassificationRun
        batch_name: Name for the task batch
        description: Description for the task batch  
        max_confidence: Maximum confidence threshold (filter out high-confidence results)
        user_id: ID of the user creating the batch
    """
    from django.contrib.auth.models import User
    
    try:
        # Get the user and classification run
        user = User.objects.get(id=user_id)
        run = ClassificationRun.objects.get(id=run_id)
        recording = run.segmentation.recording
        
        # Update task status
        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Starting task batch creation...'})
        
        # Create the task batch first
        with transaction.atomic():
            batch = TaskBatch.objects.create(
                name=batch_name,
                description=description,
                created_by=user,
                wav_file_name=recording.wav_file.name if recording.wav_file else '',
                wav_file=recording.wav_file,
                species=recording.species,
                project=recording.project,
                group=user.profile.group,
                classification_run=run,
            )
        
        # Get all classification results
        results = ClassificationResult.objects.filter(classification_run=run).select_related('segment')
        total_results = results.count()
        
        self.update_state(state='PROGRESS', meta={
            'current': 20, 
            'total': 100, 
            'status': f'Processing {total_results} classification results...'
        })
        
        # Process results in batches to avoid memory issues
        batch_size = 100
        tasks_created = 0
        tasks_filtered = 0
        
        for i in range(0, total_results, batch_size):
            batch_results = results[i:i + batch_size]
            
            # Process this batch of results
            with transaction.atomic():
                for result in batch_results:
                    segment = result.segment
                    
                    # Skip segments that already have tasks
                    if hasattr(segment, 'task') and segment.task:
                        continue
                    
                    # Get the highest probability call type
                    top_probability = CallProbability.objects.filter(
                        classification_result=result
                    ).order_by('-probability').first()
                    
                    # Skip if confidence threshold is set and this result's confidence is too high
                    if max_confidence is not None and top_probability and top_probability.probability > max_confidence:
                        tasks_filtered += 1
                        continue
                    
                    # Create a task for this segment
                    task = Task.objects.create(
                        wav_file_name=recording.wav_file.name if recording.wav_file else '',
                        onset=segment.onset,
                        offset=segment.offset,
                        species=recording.species,
                        project=recording.project,
                        batch=batch,
                        created_by=user,
                        group=user.profile.group,
                        label=top_probability.call.short_name if top_probability else None,
                        classification_result=top_probability.call.short_name if top_probability else None,
                        confidence=top_probability.probability if top_probability else None,
                        status="pending",
                    )
                    
                    # Link the task back to the segment
                    segment.task = task
                    segment.save(update_fields=['task'])
                    
                    tasks_created += 1
            
            # Update progress
            progress = 20 + int((i + batch_size) / total_results * 70)  # 20-90% range
            self.update_state(state='PROGRESS', meta={
                'current': progress,
                'total': 100,
                'status': f'Created {tasks_created} tasks, processed {min(i + batch_size, total_results)}/{total_results} results...'
            })
        
        # Final validation and cleanup
        if tasks_created == 0:
            batch.delete()
            error_msg = "No tasks were created. All segments may already have tasks or were filtered out."
            
            # Create failure notification
            UserNotification.add_notification(
                user=user,
                title="Task Batch Creation Failed",
                message=error_msg,
                notification_type="system",
                icon="s7-close"
            )
            
            return {
                'status': 'error',
                'message': error_msg,
                'batch_id': None,
                'tasks_created': 0,
                'tasks_filtered': tasks_filtered
            }
        
        # Create success notification
        success_msg = f"Created task batch '{batch.name}' with {tasks_created} tasks for review."
        if tasks_filtered > 0:
            success_msg += f" ({tasks_filtered} high-confidence tasks filtered out)"
        
        UserNotification.add_notification(
            user=user,
            title="Task Batch Created",
            message=success_msg,
            notification_type="system",
            icon="s7-check",
            link=f"/tasks/batches/{batch.id}/"
        )
        
        return {
            'status': 'success',
            'message': success_msg,
            'batch_id': batch.id,
            'tasks_created': tasks_created,
            'tasks_filtered': tasks_filtered
        }
        
    except Exception as e:
        # Create error notification
        error_msg = f"Error creating task batch: {str(e)}"
        
        try:
            user = User.objects.get(id=user_id)
            UserNotification.add_notification(
                user=user,
                title="Task Batch Creation Failed",
                message=error_msg,
                notification_type="system",
                icon="s7-close"
            )
        except:
            pass  # Don't fail if we can't create notification
        
        # Re-raise the exception for Celery to handle
        raise Exception(error_msg)