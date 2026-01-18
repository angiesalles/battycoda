"""
R server communication for classification.

Handles preparing audio segments and sending them to the R server for classification.
"""

import logging
import os

import requests
import soundfile as sf

from ....utils_modules.cleanup import safe_cleanup_dir
from ....utils_modules.path_utils import get_local_tmp, get_r_server_path
from ..base import extract_audio_segment

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
    """
    Process a single batch of segments for classification.

    Args:
        batch_index: Index of the current batch
        batch_segments: List of Segment objects to process
        classification_run: ClassificationRun instance
        recording: Recording instance
        classifier: Classifier instance
        service_url: Base URL of the R server
        endpoint: Full endpoint URL for classification
        model_path_for_r_server: Path to model file accessible by R server
        segment_list_start_idx: Starting index in the full segment list

    Returns:
        Tuple of (batch_results, segment_map, features_file)
        - batch_results: List of (segment_id, result_data, segment_metadata) tuples
        - segment_map: Dict mapping filenames to segment metadata
        - features_file: Path to features CSV file, or None
    """
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
