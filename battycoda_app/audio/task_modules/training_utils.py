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

from django.conf import settings

from .classification_utils import (
    R_SERVER_URL,
    check_r_server_connection,
    process_training_response,
    send_training_request,
    update_classification_run_status,
)

logger = logging.getLogger(__name__)


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
        update_classification_run_status(training_job, "failed", error_msg)
    return server_ok, error_msg


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
        update_classification_run_status(training_job, "completed", progress=100)
        return True, None
    except Exception as e:
        error_msg = f"Error updating training job with classifier: {str(e)}"
        update_classification_run_status(training_job, "failed", error_msg)
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


def train_and_create_classifier(
    training_job,
    model_path,
    model_filename,
    data_folder,
    species,
    source_task_batch,
    name_suffix,
    sample_count,
    extra_params=None,
):
    """
    Common training logic: send request to R server and create classifier.

    Args:
        training_job: ClassifierTrainingJob instance
        model_path: Path where model will be saved
        model_filename: Filename for the model
        data_folder: Folder containing training data
        species: Species instance
        source_task_batch: Optional TaskBatch used for training
        name_suffix: Suffix for classifier name (batch name or folder name)
        sample_count: Number of training samples
        extra_params: Additional parameters for training

    Returns:
        dict: Result of training process
    """
    algorithm_type = get_algorithm_type(training_job)
    algorithm_desc = get_algorithm_description(algorithm_type)

    # Build training parameters
    train_params = {
        "data_folder": data_folder,
        "output_model_path": model_path,
        "test_split": 0.2,
    }

    # Add extra params (like k for KNN)
    if extra_params:
        train_params.update(extra_params)

    # Add parameters from job (except special ones)
    if training_job.parameters:
        for key, value in training_job.parameters.items():
            if key not in ["algorithm_type", "training_data_folder"]:
                train_params[key] = value

    update_classification_run_status(training_job, "in_progress", progress=50)

    # Send training request
    success, result = send_training_request(algorithm_type, train_params)
    if not success:
        update_classification_run_status(training_job, "failed", result)
        return {"status": "error", "message": result}

    update_classification_run_status(training_job, "in_progress", progress=80)

    # Process response
    success, data = process_training_response(result)
    if not success:
        update_classification_run_status(training_job, "failed", data)
        return {"status": "error", "message": data}

    accuracy = data["accuracy"]
    classes = data["classes"]

    # Create classifier
    name = f"{algorithm_type.upper()} Classifier: {name_suffix}"
    description = (
        f"{algorithm_desc} classifier trained on {name_suffix} "
        f"with {sample_count} samples. Accuracy: {accuracy:.1f}%"
    )

    success, classifier_or_error = create_classifier_from_training(
        training_job=training_job,
        algorithm_type=algorithm_type,
        model_filename=model_filename,
        accuracy=accuracy,
        classes=classes,
        name=name,
        description=description,
        species=species,
        source_task_batch=source_task_batch,
    )

    if not success:
        update_classification_run_status(training_job, "failed", classifier_or_error)
        return {"status": "error", "message": classifier_or_error}

    classifier = classifier_or_error

    # Finalize job
    success, error = finalize_training_job(training_job, classifier)
    if not success:
        return {"status": "error", "message": error}

    return {
        "status": "success",
        "message": f"Successfully trained classifier with {sample_count} samples and {len(classes)} call types. Accuracy: {accuracy:.1f}%",
        "classifier_id": classifier.id,
        "model_path": model_path,
        "accuracy": accuracy,
        "classes": classes,
    }
