"""
Result processing for classification.

Handles combining features files and saving classification results to the database.
"""

import logging
import os

from django.db import transaction

from ....utils_modules.cleanup import safe_remove_file
from ....utils_modules.path_utils import get_local_tmp

logger = logging.getLogger(__name__)


def combine_features_files(all_features_files, all_segment_metadata, classification_run):
    """
    Combine all batch features files into a single enhanced export.

    Args:
        all_features_files: List of paths to batch feature CSV files
        all_segment_metadata: Dict mapping filenames to segment metadata
        classification_run: ClassificationRun instance

    Returns:
        Path to combined features file, or None if no files to combine
    """
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
            for _index, row in combined_features.iterrows():
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


def save_batch_results(batch_results, classification_run, segments, calls):
    """
    Save a batch of classification results to the database.

    Args:
        batch_results: List of (segment_id, result_data, segment_metadata) tuples
        classification_run: ClassificationRun instance
        segments: QuerySet of Segment objects
        calls: QuerySet of Call objects

    Returns:
        Number of results saved
    """
    from battycoda_app.models.classification import CallProbability, ClassificationResult

    saved_count = 0

    with transaction.atomic():
        for segment_id, result_data, _ in batch_results:
            segment = segments.get(id=segment_id)

            result = ClassificationResult.objects.create(classification_run=classification_run, segment=segment)

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

                CallProbability.objects.create(classification_result=result, call=call, probability=prob_value)

            saved_count += 1

    return saved_count
