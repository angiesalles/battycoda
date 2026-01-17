"""
Dummy classifier task for testing purposes.

Assigns equal probability to all call types without actual classification.
"""

from celery import shared_task
from django.db import transaction

from ..classification_utils import get_call_types, get_segments, update_classification_run_status


@shared_task(bind=True, name="battycoda_app.audio.task_modules.classification.dummy_classifier.run_dummy_classifier")
def run_dummy_classifier(self, detection_run_id):
    """
    Dummy classifier that assigns equal probability to all call types.
    This is for testing purposes only and doesn't perform actual classification.

    Args:
        detection_run_id: ID of the ClassificationRun model

    Returns:
        dict: Result of the dummy classification process
    """
    from battycoda_app.models.classification import CallProbability, ClassificationResult, ClassificationRun

    try:
        detection_run = ClassificationRun.objects.get(id=detection_run_id)

        update_classification_run_status(detection_run, "in_progress", progress=0)

        recording = detection_run.segmentation.recording
        segments, seg_error = get_segments(recording, detection_run.segmentation)
        if not segments:
            update_classification_run_status(detection_run, "failed", seg_error)
            return {"status": "error", "message": seg_error}

        calls, call_error = get_call_types(recording.species)
        if not calls:
            update_classification_run_status(detection_run, "failed", call_error)
            return {"status": "error", "message": call_error}

        equal_probability = 1.0 / calls.count()

        total_segments = segments.count()

        for i, segment in enumerate(segments):
            try:
                with transaction.atomic():
                    result = ClassificationResult.objects.create(classification_run=detection_run, segment=segment)

                    for call in calls:
                        CallProbability.objects.create(
                            classification_result=result, call=call, probability=equal_probability
                        )

                progress = ((i + 1) / total_segments) * 100
                update_classification_run_status(detection_run, "in_progress", progress=progress)

            except Exception:
                continue

        update_classification_run_status(detection_run, "completed", progress=100)

        return {
            "status": "success",
            "message": f"Successfully processed {total_segments} segments with dummy classifier",
            "detection_run_id": detection_run_id,
        }

    except Exception as e:
        detection_run = ClassificationRun.objects.get(id=detection_run_id)
        update_classification_run_status(detection_run, "failed", str(e))
        return {"status": "error", "message": str(e)}
