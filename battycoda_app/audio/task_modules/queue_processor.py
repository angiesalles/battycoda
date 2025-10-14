"""
Queue processor for managing sequential classification runs.

This module handles the database-based queue system to prevent
classification runs from running concurrently and causing resource conflicts.
"""
import time
from celery import shared_task
from django.db import transaction
from django.utils import timezone


@shared_task(bind=True, name="battycoda_app.audio.task_modules.queue_processor.process_classification_queue")
def process_classification_queue(self):
    """
    Process the classification queue by picking up queued ClassificationRuns
    and processing them one at a time.
    
    This task should be run periodically (e.g., every 30 seconds) to
    ensure queued classification runs are processed.
    """
    from ...models.classification import ClassificationRun
    
    try:
        # Get the next queued run to process
        with transaction.atomic():
            # Use select_for_update to prevent race conditions
            queued_run = (
                ClassificationRun.objects
                .select_for_update(skip_locked=True)
                .filter(status="queued")
                .order_by("created_at")
                .first()
            )
            
            if not queued_run:
                # No queued runs to process
                return {"status": "success", "message": "No queued runs found"}
            
            # Mark as pending before processing
            queued_run.status = "pending"
            queued_run.save(update_fields=["status"])
            
        # Now process this run outside the transaction
        print(f"Processing queued classification run: {queued_run.id} - {queued_run.name}")
        
        # Choose the appropriate task based on classifier
        if queued_run.classifier and queued_run.classifier.name == "Dummy Classifier":
            # Use the dummy classifier task directly
            from .classification.dummy_classifier import run_dummy_classifier
            result = run_dummy_classifier.delay(queued_run.id)
        else:
            # For other classifiers, use the standard task
            from .classification.run_classification import run_call_detection
            result = run_call_detection.delay(queued_run.id)
        
        return {
            "status": "success", 
            "message": f"Started processing run {queued_run.id}",
            "task_id": result.id
        }
        
    except Exception as e:
        print(f"Error in queue processor: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.queue_processor.queue_classification_run")
def queue_classification_run(self, detection_run_id):
    """
    Add a ClassificationRun to the queue for processing.
    
    This is a lightweight task that just updates the status to "queued"
    and lets the queue processor handle the actual classification.
    
    Args:
        detection_run_id: ID of the ClassificationRun to queue
    """
    from ...models.classification import ClassificationRun
    
    try:
        run = ClassificationRun.objects.get(id=detection_run_id)
        run.status = "queued"
        run.save(update_fields=["status"])
        
        print(f"Queued classification run: {run.id} - {run.name}")
        
        return {
            "status": "success",
            "message": f"Run {run.id} queued for processing"
        }
        
    except ClassificationRun.DoesNotExist:
        error_msg = f"ClassificationRun {detection_run_id} not found"
        print(error_msg)
        return {"status": "error", "message": error_msg}
    except Exception as e:
        error_msg = f"Error queuing run {detection_run_id}: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.queue_processor.get_queue_status")
def get_queue_status(self):
    """
    Get the current status of the classification queue.
    
    Returns information about queued, pending, and running classification runs.
    """
    from ...models.classification import ClassificationRun
    
    try:
        queued_count = ClassificationRun.objects.filter(status="queued").count()
        pending_count = ClassificationRun.objects.filter(status="pending").count()
        in_progress_count = ClassificationRun.objects.filter(status="in_progress").count()
        
        return {
            "status": "success",
            "queue_stats": {
                "queued": queued_count,
                "pending": pending_count,
                "in_progress": in_progress_count,
                "total_waiting": queued_count + pending_count
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}