"""
Main classification task for BattyCoda.

Runs automated call classification on segments using configured classifiers.
"""

import logging
import os

from celery import shared_task
from django.conf import settings

from ....utils_modules.path_utils import get_r_server_path
from ..classification_utils import (
    check_r_server_connection,
    get_call_types,
    get_segments,
    update_classification_run_status,
)
from .dummy_classifier import run_dummy_classifier
from .r_server_client import process_classification_batch
from .result_processing import combine_features_files, save_batch_results

logger = logging.getLogger(__name__)


@shared_task(
    bind=True, name="battycoda_app.audio.task_modules.classification.run_classification.run_call_classification"
)
def run_call_classification(self, classification_run_id):
    """
    Run automated call classification on segments using the configured classifier.

    Processes segments in small batches for better progress tracking and reliability.
    """
    from battycoda_app.models.classification import ClassificationRun, Classifier

    try:
        classification_run = ClassificationRun.objects.get(id=classification_run_id)

        update_classification_run_status(classification_run, "in_progress", progress=0)

        classifier = classification_run.classifier

        if not classifier:
            classifier = _get_default_classifier(Classifier)
            if not classifier:
                update_classification_run_status(
                    classification_run, "failed", "No classifier specified and default classifier not found"
                )
                return {"status": "error", "message": "No classifier specified and default classifier not found"}

        # Check if this is the Dummy Classifier - route to dummy classifier logic
        if classifier.name == "Dummy Classifier" or not classifier.service_url:
            return run_dummy_classifier(self, classification_run_id)

        # Validate prerequisites
        error = _validate_classification_prerequisites(classification_run, classifier)
        if error:
            update_classification_run_status(classification_run, "failed", error)
            return {"status": "error", "message": error}

        recording = classification_run.segmentation.recording
        service_url = classifier.service_url
        endpoint = f"{service_url}{classifier.endpoint}"

        segments, seg_error = get_segments(recording, classification_run.segmentation)
        if not segments:
            update_classification_run_status(classification_run, "failed", seg_error)
            return {"status": "error", "message": seg_error}

        calls, call_error = get_call_types(recording.species)
        if not calls:
            update_classification_run_status(classification_run, "failed", call_error)
            return {"status": "error", "message": call_error}

        try:
            return _process_all_batches(
                classification_run, classifier, recording, segments, calls, service_url, endpoint
            )

        except Exception as error:
            update_classification_run_status(classification_run, "failed", str(error))
            raise error

    except Exception as e:
        classification_run = ClassificationRun.objects.get(id=classification_run_id)
        update_classification_run_status(classification_run, "failed", str(e))
        return {"status": "error", "message": str(e)}


def _get_default_classifier(Classifier):
    """Get the default classifier if none specified."""
    try:
        return Classifier.objects.get(name="KNN E. fuscus")
    except Classifier.DoesNotExist:
        try:
            return Classifier.objects.get(name="R-direct Classifier")
        except Classifier.DoesNotExist:
            return None


def _validate_classification_prerequisites(classification_run, classifier):
    """
    Validate that all prerequisites for classification are met.

    Returns error message string if validation fails, None if all OK.
    """
    recording = classification_run.segmentation.recording
    service_url = classifier.service_url

    if not recording.wav_file or not os.path.exists(recording.wav_file.path):
        return f"WAV file not found for recording {recording.id}"

    server_ok, error_msg = check_r_server_connection(service_url)
    if not server_ok:
        return error_msg

    return None


def _process_all_batches(classification_run, classifier, recording, segments, calls, service_url, endpoint):
    """
    Process all segment batches and save results.

    Returns result dict with status and message.
    """
    total_segments = segments.count()
    segment_list = list(segments)

    all_features_files = []
    all_segment_metadata = {}
    total_saved = 0

    model_path_for_r_server = _get_model_path(classifier)

    batch_size = max(5, min(50, total_segments // 100 + 1))
    num_batches = (total_segments + batch_size - 1) // batch_size

    logger.info(f"Processing {total_segments} segments in {num_batches} batches (batch size: {batch_size})")

    for batch_index in range(num_batches):
        start_idx = batch_index * batch_size
        end_idx = min(start_idx + batch_size, total_segments)

        batch_segments = segment_list[start_idx:end_idx]

        batch_results, segment_map, features_file = process_classification_batch(
            batch_index,
            batch_segments,
            classification_run,
            recording,
            classifier,
            service_url,
            endpoint,
            model_path_for_r_server,
            start_idx,
        )

        all_segment_metadata.update(segment_map)

        if features_file:
            all_features_files.append(features_file)

        # Save batch results immediately to avoid memory buildup
        saved_count = save_batch_results(batch_results, classification_run, segments, calls)
        total_saved += saved_count

        # Update progress after each batch is saved
        batch_progress = 100 * ((batch_index + 1) / num_batches)
        update_classification_run_status(classification_run, status="in_progress", progress=batch_progress)
        logger.debug(f"Batch {batch_index + 1}/{num_batches} complete: {total_saved}/{total_segments} results saved")

    combined_features_path = combine_features_files(all_features_files, all_segment_metadata, classification_run)

    if combined_features_path and os.path.exists(combined_features_path):
        classification_run.features_file = combined_features_path
        classification_run.save()

    update_classification_run_status(classification_run, "completed", progress=100)

    result = {
        "status": "success",
        "message": f"Successfully processed {total_segments} segments using classifier: {classifier.name}",
        "classification_run_id": classification_run.id,
    }

    if combined_features_path and os.path.exists(combined_features_path):
        result["features_file"] = combined_features_path
        result["message"] += " | Features exported to CSV file"

    return result


def _get_model_path(classifier):
    """Get the model path formatted for the R server."""
    if not classifier.model_file:
        return None

    model_file_path = classifier.model_file
    model_path = os.path.join(settings.BASE_DIR, model_file_path)

    if not os.path.exists(model_path):
        raise ValueError(f"Model file not found: {model_path}")

    return get_r_server_path(model_path)
