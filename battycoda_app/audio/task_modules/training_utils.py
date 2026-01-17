"""
Shared utilities for classifier training tasks.

This module contains helper functions used by both train_classifier
and train_classifier_from_folder tasks.
"""

import hashlib
import logging
import os
import shutil
import time

import requests
from django.conf import settings

from .classification_utils import R_SERVER_URL, check_r_server_connection, update_detection_run_status

logger = logging.getLogger(__name__)


def unwrap_list(value):
    """
    Unwrap single-element lists from R server responses.

    R server sometimes returns values wrapped in lists (e.g., ["success"] instead of "success").
    This function extracts the first element if value is a non-empty list.

    Args:
        value: Any value, potentially a list

    Returns:
        The unwrapped value, or original value if not a list
    """
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    return value


def cleanup_temp_dir(temp_dir):
    """
    Safely clean up a temporary directory.

    Args:
        temp_dir: Path to the temporary directory to remove
    """
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception:
        # Don't fail if cleanup fails
        pass


def build_model_path(identifier):
    """
    Create model directory and generate a unique model filename.

    Args:
        identifier: String to include in the hash (e.g., batch_id or folder_path)

    Returns:
        tuple: (model_path, model_filename) - full path and just the filename
    """
    model_dir = os.path.join(settings.MEDIA_ROOT, "models", "classifiers")
    os.makedirs(model_dir, exist_ok=True)

    timestamp = int(time.time())
    model_hash = hashlib.md5(f"{identifier}_{timestamp}".encode()).hexdigest()[:10]
    model_filename = f"classifier_{model_hash}_{identifier}.RData"
    model_path = os.path.join(model_dir, model_filename)

    return model_path, model_filename


def check_r_server_and_update_status(training_job):
    """
    Check R server connection and update job status if failed.

    Args:
        training_job: ClassifierTrainingJob instance

    Returns:
        tuple: (is_ok, error_message) - True if connected, False with error message otherwise
    """
    server_ok, error_msg = check_r_server_connection(R_SERVER_URL)
    if not server_ok:
        update_detection_run_status(training_job, "failed", error_msg)
    return server_ok, error_msg


def send_training_request(algorithm_type, train_params):
    """
    Send training request to R server.

    Args:
        algorithm_type: "knn" or "lda"
        train_params: Dictionary of training parameters

    Returns:
        tuple: (success, result_or_error)
            - On success: (True, response_json)
            - On failure: (False, error_message)
    """
    if algorithm_type.lower() == "lda":
        endpoint = f"{R_SERVER_URL}/train/lda"
    else:
        endpoint = f"{R_SERVER_URL}/train/knn"

    logger.debug(f"Using {algorithm_type.upper()} training endpoint: {endpoint}")
    logger.debug(f"Training parameters: {train_params}")

    try:
        response = requests.post(endpoint, data=train_params, timeout=3600)

        if response.status_code != 200:
            error_msg = f"R server training failed. Status: {response.status_code}, Response: {response.text}"
            return False, error_msg

        logger.debug(f"Raw training response text: {response.text[:200]}...")
        return True, response.json()

    except Exception as e:
        return False, f"Error communicating with R server: {str(e)}"


def process_training_response(train_result):
    """
    Process and validate training response from R server.

    Args:
        train_result: JSON response from R server

    Returns:
        tuple: (success, data_or_error)
            - On success: (True, {"accuracy": float, "classes": list})
            - On failure: (False, error_message)
    """
    status_value = train_result.get("status")
    is_success = status_value == "success" or (
        isinstance(status_value, list) and len(status_value) > 0 and status_value[0] == "success"
    )

    if not is_success:
        error_msg = f"R server training error: {train_result.get('message', 'Unknown error')}"
        return False, error_msg

    # Extract and validate accuracy
    accuracy = unwrap_list(train_result.get("accuracy", 0))
    if not isinstance(accuracy, (int, float)):
        try:
            accuracy = float(accuracy)
        except (ValueError, TypeError):
            accuracy = 0

    # Extract and validate classes
    classes = train_result.get("classes", [])
    if not isinstance(classes, list):
        classes = []

    return True, {"accuracy": accuracy, "classes": classes}


def create_classifier_from_training(
    training_job,
    algorithm_type,
    model_filename,
    accuracy,
    classes,
    name,
    description,
    species,
    source_task_batch=None,
):
    """
    Create a Classifier object in the database from training results.

    Args:
        training_job: ClassifierTrainingJob instance
        algorithm_type: "knn" or "lda"
        model_filename: Filename of the saved model
        accuracy: Training accuracy percentage
        classes: List of class labels
        name: Classifier name
        description: Classifier description
        species: Species instance
        source_task_batch: Optional TaskBatch that was used for training

    Returns:
        tuple: (success, classifier_or_error)
            - On success: (True, Classifier instance)
            - On failure: (False, error_message)
    """
    from ...models.classification import Classifier

    try:
        classifier = Classifier.objects.create(
            name=name,
            description=description,
            response_format=training_job.response_format,
            celery_task="battycoda_app.audio.task_modules.classification.run_classification.run_call_classification",
            service_url=R_SERVER_URL,
            endpoint=f"/predict/{algorithm_type.lower()}",
            source_task_batch=source_task_batch,
            model_file=os.path.join("media", "models", "classifiers", model_filename),
            is_active=True,
            created_by=training_job.created_by,
            group=training_job.group,
            species=species,
        )
        logger.debug(f"Successfully created classifier {classifier.id}")
        return True, classifier

    except Exception as e:
        error_msg = f"Error creating classifier in database: {str(e)}"
        logger.exception(error_msg)
        return False, error_msg


def finalize_training_job(training_job, classifier):
    """
    Update training job with the created classifier and mark as completed.

    Args:
        training_job: ClassifierTrainingJob instance
        classifier: Classifier instance

    Returns:
        tuple: (success, error_message or None)
    """
    try:
        training_job.classifier = classifier
        training_job.save()
        update_detection_run_status(training_job, "completed", progress=100)
        return True, None
    except Exception as e:
        error_msg = f"Error updating training job with classifier: {str(e)}"
        update_detection_run_status(training_job, "failed", error_msg)
        return False, error_msg


def get_algorithm_type(training_job):
    """
    Extract algorithm type from training job parameters.

    Args:
        training_job: ClassifierTrainingJob instance

    Returns:
        str: Algorithm type ("knn" or "lda"), defaults to "knn"
    """
    if training_job.parameters and "algorithm_type" in training_job.parameters:
        return training_job.parameters["algorithm_type"]
    return "knn"


def get_algorithm_description(algorithm_type):
    """
    Get human-readable description for algorithm type.

    Args:
        algorithm_type: "knn" or "lda"

    Returns:
        str: Full algorithm name
    """
    if algorithm_type.lower() == "lda":
        return "Linear Discriminant Analysis"
    return "K-Nearest Neighbors"
