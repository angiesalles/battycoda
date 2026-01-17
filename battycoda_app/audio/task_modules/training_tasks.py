"""
Training tasks for BattyCoda.

This module contains Celery tasks for training custom classifiers.
"""

import logging
import os

import soundfile as sf
from celery import shared_task

from ...utils_modules.path_utils import get_local_tmp, get_r_server_path
from .base import extract_audio_segment
from .classification_utils import update_detection_run_status
from .training_utils import (
    build_model_path,
    check_r_server_and_update_status,
    cleanup_temp_dir,
    create_classifier_from_training,
    finalize_training_job,
    get_algorithm_description,
    get_algorithm_type,
    process_training_response,
    send_training_request,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="battycoda_app.audio.task_modules.training_tasks.train_classifier")
def train_classifier(self, training_job_id):
    """
    Train a new classifier from a task batch with labeled tasks.
    Uses the R server to train either KNN or LDA classifier from audio segments.

    Args:
        training_job_id: ID of the ClassifierTrainingJob model

    Returns:
        dict: Result of the training process
    """
    from ...models.classification import ClassifierTrainingJob
    from ...models.task import Task

    temp_dir = None

    try:
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        update_detection_run_status(training_job, "in_progress", progress=5)

        # Get labeled tasks from batch
        task_batch = training_job.task_batch
        tasks = Task.objects.filter(batch=task_batch, is_done=True, label__isnull=False)
        total_tasks = tasks.count()

        if total_tasks == 0:
            error_msg = "No labeled tasks found in this batch. Tasks must be labeled to train a classifier."
            update_detection_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        # Set up model path
        model_path, model_filename = build_model_path(str(task_batch.id))
        update_detection_run_status(training_job, "in_progress", progress=10)

        # Extract audio segments to temp directory
        temp_dir = os.path.join(get_local_tmp(), f"training_{os.path.basename(model_path).split('.')[0]}")
        os.makedirs(temp_dir, exist_ok=True)

        file_counter = _extract_segments_from_tasks(tasks, task_batch, temp_dir, training_job, total_tasks)

        update_detection_run_status(training_job, "in_progress", progress=50)

        if file_counter <= 1:
            error_msg = "Failed to extract any valid audio segments for training."
            update_detection_run_status(training_job, "failed", error_msg)
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        # Check R server
        server_ok, error_msg = check_r_server_and_update_status(training_job)
        if not server_ok:
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        update_detection_run_status(training_job, "in_progress", progress=60)

        # Train the model
        result = _train_and_create_classifier(
            training_job=training_job,
            model_path=model_path,
            model_filename=model_filename,
            data_folder=temp_dir,
            species=task_batch.species,
            source_task_batch=task_batch,
            name_suffix=task_batch.name,
            sample_count=file_counter - 1,
        )

        cleanup_temp_dir(temp_dir)
        return result

    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return _handle_training_error(training_job_id, e, "classifier training")


def _extract_segments_from_tasks(tasks, task_batch, temp_dir, training_job, total_tasks):
    """Extract audio segments from labeled tasks and save to temp directory."""
    file_counter = 1

    for i, task in enumerate(tasks):
        if i % 5 == 0:
            progress = 10.0 + (40.0 * (i / total_tasks))
            update_detection_run_status(training_job, "in_progress", progress=min(50.0, progress))

        if not task.label:
            continue

        try:
            if not task_batch.wav_file:
                logger.warning(f"Task batch {task_batch.id} has no wav_file")
                continue

            wav_file_path = task_batch.wav_file.path
            if not os.path.exists(wav_file_path):
                logger.warning(f"WAV file path does not exist: {wav_file_path}")
                continue

            logger.debug(f"Extracting segment for task {task.id}: {task.onset} to {task.offset}")

            segment_data, sample_rate = extract_audio_segment(wav_file_path, task.onset, task.offset)

            if segment_data is None or len(segment_data) == 0:
                logger.warning(f"No audio data extracted for task {task.id}")
                continue

            output_filename = f"{file_counter}_{task.label}.wav"
            output_path = os.path.join(temp_dir, output_filename)
            sf.write(output_path, segment_data, samplerate=sample_rate)

            logger.debug(f"Saved segment {file_counter} with label '{task.label}'")
            file_counter += 1

        except Exception as e:
            logger.warning(f"Error extracting segment for task {task.id}: {str(e)}")
            continue

    return file_counter


@shared_task(bind=True, name="battycoda_app.audio.task_modules.training_tasks.train_classifier_from_folder")
def train_classifier_from_folder(self, training_job_id, species_id):
    """
    Train a new classifier from a pre-labeled training data folder.
    Uses the R server to train either KNN or LDA classifier from labeled audio files.

    Args:
        training_job_id: ID of the ClassifierTrainingJob model
        species_id: ID of the Species this classifier is for

    Returns:
        dict: Result of the training process
    """
    from ...models.classification import ClassifierTrainingJob
    from ...models.organization import Species

    try:
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        species = Species.objects.get(id=species_id)

        update_detection_run_status(training_job, "in_progress", progress=5)

        # Validate folder path
        if not training_job.parameters or "training_data_folder" not in training_job.parameters:
            error_msg = "No training data folder specified in job parameters"
            update_detection_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        folder_path = training_job.parameters["training_data_folder"]

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            error_msg = f"Training data folder does not exist: {folder_path}"
            update_detection_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        wav_files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]

        if len(wav_files) == 0:
            error_msg = f"No WAV files found in training data folder: {folder_path}"
            update_detection_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        update_detection_run_status(training_job, "in_progress", progress=10)

        # Set up model path
        model_path, model_filename = build_model_path("folder")
        update_detection_run_status(training_job, "in_progress", progress=30)

        # Check R server
        server_ok, error_msg = check_r_server_and_update_status(training_job)
        if not server_ok:
            return {"status": "error", "message": error_msg}

        update_detection_run_status(training_job, "in_progress", progress=40)

        # Convert paths for R server
        folder_path_for_r = get_r_server_path(folder_path)
        model_path_for_r = get_r_server_path(model_path)

        # Calculate k value for KNN
        extra_params = {}
        algorithm_type = get_algorithm_type(training_job)
        if algorithm_type.lower() == "knn":
            import math

            k_value = min(int(math.sqrt(len(wav_files))), len(wav_files) - 1, 20)
            k_value = max(k_value, 3)
            extra_params["k"] = k_value

        # Train the model
        result = _train_and_create_classifier(
            training_job=training_job,
            model_path=model_path_for_r,
            model_filename=model_filename,
            data_folder=folder_path_for_r,
            species=species,
            source_task_batch=None,
            name_suffix=os.path.basename(folder_path),
            sample_count=len(wav_files),
            extra_params=extra_params,
        )

        return result

    except Exception as e:
        return _handle_training_error(training_job_id, e, "classifier training from folder")


def _train_and_create_classifier(
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

    update_detection_run_status(training_job, "in_progress", progress=50)

    # Send training request
    success, result = send_training_request(algorithm_type, train_params)
    if not success:
        update_detection_run_status(training_job, "failed", result)
        return {"status": "error", "message": result}

    update_detection_run_status(training_job, "in_progress", progress=80)

    # Process response
    success, data = process_training_response(result)
    if not success:
        update_detection_run_status(training_job, "failed", data)
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
        update_detection_run_status(training_job, "failed", classifier_or_error)
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


def _handle_training_error(training_job_id, exception, context):
    """Handle exceptions during training and update job status."""
    from ...models.classification import ClassifierTrainingJob

    try:
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        error_msg = f"Error in {context}: {str(exception)}"
        update_detection_run_status(training_job, "failed", error_msg)
    except Exception:
        error_msg = f"Critical error in {context}: {str(exception)}"

    return {"status": "error", "message": error_msg}
