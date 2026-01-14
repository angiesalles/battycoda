"""
Main classification task for BattyCoda.

Runs automated call classification on segments using configured classifiers.
"""

import logging
import os

import requests
import soundfile as sf
from celery import shared_task
from django.conf import settings
from django.db import transaction

from ....utils_modules.cleanup import safe_cleanup_dir, safe_remove_file
from ....utils_modules.path_utils import get_local_tmp, get_r_server_path
from ..base import extract_audio_segment
from ..classification_utils import (
    check_r_server_connection,
    get_call_types,
    get_segments,
    update_classification_run_status,
)

logger = logging.getLogger(__name__)


def process_classification_batch(
    batch_index,
    batch_segments,
    classification_run,
    recording,
    classifier,
    service_url,
    endpoint,
    model_path_for_r_server,
    segment_list_start_idx,
):
    """Process a single batch of segments for classification."""
    shared_tmp_dir = get_local_tmp()
    os.makedirs(shared_tmp_dir, exist_ok=True)

    batch_dir_name = f"batch_{batch_index}_{classification_run.id}"
    batch_dir = os.path.join(shared_tmp_dir, batch_dir_name)
    os.makedirs(batch_dir, exist_ok=True)

    try:
        segment_map = {}

        for i, segment in enumerate(batch_segments):
            segment_data, sample_rate = extract_audio_segment(recording.wav_file.path, segment.onset, segment.offset)

            segment_filename = f"segment_{segment.id}.wav"
            segment_path = os.path.join(batch_dir, segment_filename)

            sf.write(segment_path, segment_data, samplerate=sample_rate)

            task_id = None
            if hasattr(segment, "task") and segment.task:
                task_id = segment.task.id

            segment_metadata = {
                "segment_id": segment.id,
                "task_id": task_id,
                "start_time": segment.onset,
                "end_time": segment.offset,
                "recording_name": recording.name,
                "wav_filename": os.path.basename(recording.wav_file.name) if recording.wav_file else "unknown.wav",
            }
            segment_map[segment_filename] = segment_metadata

        r_server_path = get_r_server_path(batch_dir)

        features_filename = f"batch_{batch_index}_{classification_run.id}_features.csv"
        features_path_local = os.path.join(shared_tmp_dir, features_filename)
        features_path_r_server = get_r_server_path(features_path_local)

        params = {
            "wav_folder": r_server_path,
            "model_path": model_path_for_r_server,
            "export_features_path": features_path_r_server,
        }

        logger.debug(f"Calling classifier service for batch {batch_index + 1} at {endpoint}")

        response = requests.post(endpoint, data=params, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(
                f"Classifier service error for batch {batch_index + 1}: Status {response.status_code} - {response.text}"
            )

        prediction_data = response.json()

        status_value = prediction_data.get("status")
        is_success = status_value == "success" or (
            isinstance(status_value, list) and len(status_value) > 0 and status_value[0] == "success"
        )

        if not is_success:
            raise ValueError(
                f"Classifier returned error for batch {batch_index + 1}: {prediction_data.get('message', 'Unknown error')}"
            )

        file_results = prediction_data.get("file_results", {})

        batch_results = []
        for filename, result_data in file_results.items():
            segment_metadata = segment_map.get(filename)
            if segment_metadata:
                segment_id = segment_metadata["segment_id"]
                processed_data = {}
                for key, value in result_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        processed_data[key] = value[0]
                    else:
                        processed_data[key] = value

                if "class_probabilities" in result_data:
                    prob_data = result_data["class_probabilities"]
                    if isinstance(prob_data, list) and len(prob_data) > 0:
                        processed_data["class_probabilities"] = prob_data[0]

                batch_results.append((segment_id, processed_data, segment_metadata))

        features_file = features_path_local if os.path.exists(features_path_local) else None

        return batch_results, segment_map, features_file

    finally:
        safe_cleanup_dir(batch_dir, f"classification batch {batch_index}")


def combine_features_files(all_features_files, all_segment_metadata, classification_run):
    """Combine all batch features files into a single enhanced export."""
    if not all_features_files:
        return None

    try:
        import pandas as pd

        shared_tmp_dir = get_local_tmp()
        features_export_filename = f"classification_run_{classification_run.id}_features.csv"
        combined_features_path = os.path.join(shared_tmp_dir, features_export_filename)

        all_features_data = []
        for features_file in all_features_files:
            try:
                df = pd.read_csv(features_file)
                all_features_data.append(df)
            except (IOError, ValueError) as read_error:
                logger.warning(f"Could not read features file {features_file}: {read_error}")

        if all_features_data:
            combined_features = pd.concat(all_features_data, ignore_index=True)

            enhanced_columns = []
            for index, row in combined_features.iterrows():
                sound_file = row["sound.files"]
                if sound_file in all_segment_metadata:
                    metadata = all_segment_metadata[sound_file]
                    enhanced_columns.append(
                        {
                            "task_id": metadata["task_id"],
                            "call_start_time": metadata["start_time"],
                            "call_end_time": metadata["end_time"],
                            "call_duration": metadata["end_time"] - metadata["start_time"],
                            "recording_name": metadata["recording_name"],
                            "original_wav_file": metadata["wav_filename"],
                        }
                    )
                else:
                    enhanced_columns.append(
                        {
                            "task_id": None,
                            "call_start_time": None,
                            "call_end_time": None,
                            "call_duration": None,
                            "recording_name": "Unknown",
                            "original_wav_file": "Unknown",
                        }
                    )

            enhanced_df = pd.DataFrame(enhanced_columns)

            original_cols = combined_features.columns.tolist()

            insert_index = 2
            if "selec" in original_cols:
                insert_index = original_cols.index("selec") + 1
            elif "sound.files" in original_cols:
                insert_index = original_cols.index("sound.files") + 1

            new_cols = [
                "task_id",
                "call_start_time",
                "call_end_time",
                "call_duration",
                "recording_name",
                "original_wav_file",
            ]
            final_cols = original_cols[:insert_index] + new_cols + original_cols[insert_index:]

            final_features = pd.concat([combined_features, enhanced_df], axis=1)
            final_features = final_features[final_cols]

            final_features.to_csv(combined_features_path, index=False)
            logger.info(f"Enhanced features exported: {combined_features_path}")

        for features_file in all_features_files:
            safe_remove_file(features_file, "batch features file")

        return combined_features_path

    except (IOError, ValueError, KeyError) as features_error:
        logger.warning(f"Error combining features files: {features_error}")
        return None


@shared_task(
    bind=True, name="battycoda_app.audio.task_modules.classification.run_classification.run_call_classification"
)
def run_call_classification(self, classification_run_id):
    """
    Run automated call classification on segments using the configured classifier.

    Processes segments in small batches for better progress tracking and reliability.
    """
    from battycoda_app.models.classification import CallProbability, ClassificationResult, ClassificationRun, Classifier

    try:
        classification_run = ClassificationRun.objects.get(id=classification_run_id)

        update_classification_run_status(classification_run, "in_progress", progress=0)

        classifier = classification_run.classifier

        if not classifier:
            try:
                classifier = Classifier.objects.get(name="KNN E. fuscus")
            except Classifier.DoesNotExist:
                try:
                    classifier = Classifier.objects.get(name="R-direct Classifier")
                except Classifier.DoesNotExist:
                    update_classification_run_status(
                        classification_run, "failed", "No classifier specified and default classifier not found"
                    )
                    return {"status": "error", "message": "No classifier specified and default classifier not found"}

        # Check if this is the Dummy Classifier - route to dummy classifier logic
        if classifier.name == "Dummy Classifier" or not classifier.service_url:
            # Run dummy classifier inline (not as a separate task)
            return run_dummy_classification_inline(self, classification_run_id, CallProbability, ClassificationResult)

        service_url = classifier.service_url
        endpoint = f"{service_url}{classifier.endpoint}"

        recording = classification_run.segmentation.recording
        if not recording.wav_file or not os.path.exists(recording.wav_file.path):
            update_classification_run_status(
                classification_run, "failed", f"WAV file not found for recording {recording.id}"
            )
            return {"status": "error", "message": "WAV file not found"}

        server_ok, error_msg = check_r_server_connection(service_url)
        if not server_ok:
            update_classification_run_status(classification_run, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        segments, seg_error = get_segments(recording, classification_run.segmentation)
        if not segments:
            update_classification_run_status(classification_run, "failed", seg_error)
            return {"status": "error", "message": seg_error}

        calls, call_error = get_call_types(recording.species)
        if not calls:
            update_classification_run_status(classification_run, "failed", call_error)
            return {"status": "error", "message": call_error}

        try:
            total_segments = segments.count()
            segment_list = list(segments)

            all_features_files = []
            all_segment_metadata = {}
            total_saved = 0

            model_path = None
            model_path_for_r_server = None
            if classifier.model_file:
                model_file_path = classifier.model_file
                model_path = os.path.join(settings.BASE_DIR, model_file_path)
                model_path_for_r_server = get_r_server_path(model_path)

                if not os.path.exists(model_path):
                    raise ValueError(f"Model file not found: {model_path}")

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
                with transaction.atomic():
                    for segment_id, result_data, _ in batch_results:
                        segment = segments.get(id=segment_id)

                        result = ClassificationResult.objects.create(
                            classification_run=classification_run, segment=segment
                        )

                        class_probabilities = result_data.get("class_probabilities", {})

                        for call in calls:
                            if call.short_name not in class_probabilities:
                                probability = 0.0
                            else:
                                probability = class_probabilities[call.short_name]
                                if not isinstance(probability, (int, float)):
                                    if (
                                        isinstance(probability, list)
                                        and len(probability) == 1
                                        and isinstance(probability[0], (int, float))
                                    ):
                                        probability = probability[0]
                                    else:
                                        probability = 0.0

                            prob_value = probability / 100.0
                            prob_value = max(0.0, min(1.0, float(prob_value)))

                            CallProbability.objects.create(
                                classification_result=result, call=call, probability=prob_value
                            )

                        total_saved += 1

                # Update progress after each batch is saved
                batch_progress = 100 * ((batch_index + 1) / num_batches)
                update_classification_run_status(classification_run, status="in_progress", progress=batch_progress)
                logger.debug(
                    f"Batch {batch_index + 1}/{num_batches} complete: {total_saved}/{total_segments} results saved"
                )

            combined_features_path = combine_features_files(
                all_features_files, all_segment_metadata, classification_run
            )

            if combined_features_path and os.path.exists(combined_features_path):
                classification_run.features_file = combined_features_path
                classification_run.save()

            update_classification_run_status(classification_run, "completed", progress=100)

            result = {
                "status": "success",
                "message": f"Successfully processed {total_segments} segments using classifier: {classifier.name}",
                "classification_run_id": classification_run_id,
            }

            if combined_features_path and os.path.exists(combined_features_path):
                result["features_file"] = combined_features_path
                result["message"] += " | Features exported to CSV file"

            return result

        except Exception as error:
            update_classification_run_status(classification_run, "failed", str(error))
            raise error

    except Exception as e:
        classification_run = ClassificationRun.objects.get(id=classification_run_id)
        update_classification_run_status(classification_run, "failed", str(e))
        return {"status": "error", "message": str(e)}
