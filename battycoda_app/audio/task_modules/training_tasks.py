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
from .classification_utils import RServerTimeout, update_classification_run_status
from .training_utils import (
    build_model_path,
    check_r_server_and_update_status,
    cleanup_temp_dir,
    get_algorithm_type,
    train_and_create_classifier,
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
        update_classification_run_status(training_job, "in_progress", progress=5)

        # Get labeled tasks from batch
        task_batch = training_job.task_batch
        tasks = Task.objects.filter(batch=task_batch, is_done=True, label__isnull=False)
        total_tasks = tasks.count()

        if total_tasks == 0:
            error_msg = "No labeled tasks found in this batch. Tasks must be labeled to train a classifier."
            update_classification_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        # Set up model path
        model_path, model_filename = build_model_path(str(task_batch.id))
        update_classification_run_status(
            training_job, "in_progress", message=f"Extracting audio from {total_tasks} tasks...", progress=10
        )

        # Extract audio segments to temp directory
        temp_dir = os.path.join(get_local_tmp(), f"training_{os.path.basename(model_path).split('.')[0]}")
        os.makedirs(temp_dir, exist_ok=True)

        file_counter = _extract_segments_from_tasks(tasks, task_batch, temp_dir, training_job, total_tasks)

        update_classification_run_status(training_job, "in_progress", progress=55)

        if file_counter <= 1:
            error_msg = "Failed to extract any valid audio segments for training."
            update_classification_run_status(training_job, "failed", error_msg)
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        # Check R server
        server_ok, error_msg = check_r_server_and_update_status(training_job)
        if not server_ok:
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        update_classification_run_status(
            training_job, "in_progress", message="Preparing to train model...", progress=60
        )

        # Convert local paths to R server paths (R server runs in Docker with different mount)
        model_path_for_r = get_r_server_path(model_path)
        data_folder_for_r = get_r_server_path(temp_dir)

        # Train the model
        result = train_and_create_classifier(
            training_job=training_job,
            model_path=model_path_for_r,
            model_filename=model_filename,
            data_folder=data_folder_for_r,
            species=task_batch.species,
            source_task_batch=task_batch,
            name_suffix=task_batch.name,
            sample_count=file_counter - 1,
        )

        cleanup_temp_dir(temp_dir)
        return result

    except RServerTimeout as e:
        # R server may still be processing this temp dir; leave it in place so
        # we don't delete files out from under the running job.
        logger.warning(f"R server timed out; leaving temp dir {temp_dir} for later cleanup")
        return _handle_training_error(training_job_id, e, "classifier training (R server timeout)")
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return _handle_training_error(training_job_id, e, "classifier training")


def _extract_segments_from_tasks(tasks, task_batch, temp_dir, training_job, total_tasks):
    """Extract audio segments from labeled tasks and save to temp directory."""
    file_counter = 1

    for i, task in enumerate(tasks):
        if i % 5 == 0:
            progress = 10.0 + (40.0 * (i / total_tasks))
            update_classification_run_status(training_job, "in_progress", progress=min(50.0, progress))

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

        update_classification_run_status(training_job, "in_progress", progress=5)

        # Validate folder path
        if not training_job.parameters or "training_data_folder" not in training_job.parameters:
            error_msg = "No training data folder specified in job parameters"
            update_classification_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        folder_path = training_job.parameters["training_data_folder"]

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            error_msg = f"Training data folder does not exist: {folder_path}"
            update_classification_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        wav_files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]

        if len(wav_files) == 0:
            error_msg = f"No WAV files found in training data folder: {folder_path}"
            update_classification_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        update_classification_run_status(training_job, "in_progress", progress=10)

        # Set up model path
        model_path, model_filename = build_model_path("folder")
        update_classification_run_status(training_job, "in_progress", progress=30)

        # Check R server
        server_ok, error_msg = check_r_server_and_update_status(training_job)
        if not server_ok:
            return {"status": "error", "message": error_msg}

        update_classification_run_status(training_job, "in_progress", progress=40)

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
        result = train_and_create_classifier(
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


@shared_task(bind=True, name="battycoda_app.audio.task_modules.training_tasks.train_classifier_from_species")
def train_classifier_from_species(self, training_job_id, species_id):
    """
    Train a new classifier from all labeled tasks for a species.
    Aggregates labeled data across all task batches for the species.

    Args:
        training_job_id: ID of the ClassifierTrainingJob model
        species_id: ID of the Species to train on

    Returns:
        dict: Result of the training process
    """
    from ...models.classification import ClassifierTrainingJob
    from ...models.organization import Species
    from ...models.task import Task

    temp_dir = None

    try:
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        species = Species.objects.get(id=species_id)

        update_classification_run_status(training_job, "in_progress", progress=5)

        # Get all labeled tasks for this species across all batches
        all_tasks = (
            Task.objects.filter(species=species, is_done=True, label__isnull=False)
            .exclude(label="")
            .select_related("batch")
        )
        total_available = all_tasks.count()

        if total_available == 0:
            error_msg = "No labeled tasks found for this species."
            update_classification_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        # Cap training data with stratified sampling to keep R server responsive
        MAX_TRAINING_SAMPLES = 5000
        if total_available > MAX_TRAINING_SAMPLES:
            tasks = _stratified_sample(all_tasks, MAX_TRAINING_SAMPLES)
            sample_msg = f"Sampled {len(tasks)} of {total_available} tasks (stratified by label)"
            logger.info(sample_msg)
        else:
            tasks = list(all_tasks)
            sample_msg = None

        total_tasks = len(tasks)

        # Set up model path
        model_path, model_filename = build_model_path(f"species_{species_id}")
        msg = f"Extracting audio from {total_tasks} tasks..."
        if sample_msg:
            msg = f"{sample_msg}. {msg}"
        update_classification_run_status(training_job, "in_progress", message=msg, progress=10)

        # Extract audio segments to temp directory
        temp_dir = os.path.join(get_local_tmp(), f"training_{os.path.basename(model_path).split('.')[0]}")
        os.makedirs(temp_dir, exist_ok=True)

        file_counter = _extract_segments_across_batches(tasks, temp_dir, training_job, total_tasks)

        update_classification_run_status(training_job, "in_progress", progress=55)

        if file_counter <= 1:
            error_msg = "Failed to extract any valid audio segments for training."
            update_classification_run_status(training_job, "failed", error_msg)
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        # Check R server
        server_ok, error_msg = check_r_server_and_update_status(training_job)
        if not server_ok:
            cleanup_temp_dir(temp_dir)
            return {"status": "error", "message": error_msg}

        update_classification_run_status(
            training_job, "in_progress", message="Preparing to train model...", progress=60
        )

        # Convert local paths to R server paths (R server runs in Docker with different mount)
        model_path_for_r = get_r_server_path(model_path)
        data_folder_for_r = get_r_server_path(temp_dir)

        # Train the model
        result = train_and_create_classifier(
            training_job=training_job,
            model_path=model_path_for_r,
            model_filename=model_filename,
            data_folder=data_folder_for_r,
            species=species,
            source_task_batch=None,
            name_suffix=species.name,
            sample_count=file_counter - 1,
        )

        cleanup_temp_dir(temp_dir)
        return result

    except RServerTimeout as e:
        # R server may still be processing this temp dir; leave it in place so
        # we don't delete files out from under the running job.
        logger.warning(f"R server timed out; leaving temp dir {temp_dir} for later cleanup")
        return _handle_training_error(training_job_id, e, "classifier training from species (R server timeout)")
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return _handle_training_error(training_job_id, e, "classifier training from species")


def _stratified_sample(tasks_qs, max_samples):
    """Sample tasks proportionally by label so all call types are represented."""
    import random
    from collections import defaultdict

    # Group task IDs by label
    by_label = defaultdict(list)
    for task in tasks_qs.values_list("id", "label"):
        by_label[task[1]].append(task[0])

    total = sum(len(ids) for ids in by_label.values())
    sampled_ids = []

    for label, ids in by_label.items():
        # Proportional allocation, but at least 2 per label for train/test split
        n = max(2, round(len(ids) / total * max_samples))
        n = min(n, len(ids))
        sampled_ids.extend(random.sample(ids, n))

    # If we overshot, trim randomly; if under, that's fine
    if len(sampled_ids) > max_samples:
        sampled_ids = random.sample(sampled_ids, max_samples)

    return list(tasks_qs.filter(id__in=sampled_ids).select_related("batch"))


def _extract_segments_across_batches(tasks, temp_dir, training_job, total_tasks):
    """Extract audio segments from labeled tasks spanning multiple batches."""
    file_counter = 1

    for i, task in enumerate(tasks):
        if i % 5 == 0:
            progress = 10.0 + (40.0 * (i / total_tasks))
            update_classification_run_status(training_job, "in_progress", progress=min(50.0, progress))

        if not task.label:
            continue

        try:
            batch = task.batch
            if not batch or not batch.wav_file:
                logger.warning(f"Task {task.id} has no batch or batch has no wav_file")
                continue

            wav_file_path = batch.wav_file.path
            if not os.path.exists(wav_file_path):
                logger.warning(f"WAV file path does not exist: {wav_file_path}")
                continue

            segment_data, sample_rate = extract_audio_segment(wav_file_path, task.onset, task.offset)

            if segment_data is None or len(segment_data) == 0:
                logger.warning(f"No audio data extracted for task {task.id}")
                continue

            output_filename = f"{file_counter}_{task.label}.wav"
            output_path = os.path.join(temp_dir, output_filename)
            sf.write(output_path, segment_data, samplerate=sample_rate)

            file_counter += 1

        except Exception as e:
            logger.warning(f"Error extracting segment for task {task.id}: {str(e)}")
            continue

    return file_counter


def _handle_training_error(training_job_id, exception, context):
    """Handle exceptions during training and update job status."""
    from ...models.classification import ClassifierTrainingJob

    try:
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        error_msg = f"Error in {context}: {str(exception)}"
        update_classification_run_status(training_job, "failed", error_msg)
    except Exception:
        error_msg = f"Critical error in {context}: {str(exception)}"

    return {"status": "error", "message": error_msg}
