"""
Segmentation tasks for BattyCoda.
"""
import os
import traceback

from celery import shared_task

# logger import removed

@shared_task(bind=True, name="battycoda_app.audio.task_modules.segmentation_tasks.auto_segment_recording_task")
def auto_segment_recording_task(
    self, recording_id, segmentation_id, min_duration_ms=10, smooth_window=3, threshold_factor=0.5, low_freq=None, high_freq=None
):
    """
    Automatically segment a recording using the steps:
    1. Take absolute value of the signal
    2. Smooth the signal using a moving average filter
    3. Apply a threshold to detect segments
    4. Reject markings shorter than the minimum duration

    Args:
        recording_id: ID of the Recording model to segment
        segmentation_id: ID of the Segmentation model tracking this task
        min_duration_ms: Minimum segment duration in milliseconds
        smooth_window: Window size for smoothing filter (number of samples)
        threshold_factor: Threshold factor (between 0-1) relative to signal statistics

    Returns:
        dict: Result information including number of segments created and optional debug image path
    """
    from django.conf import settings
    from django.db import transaction

    from ...models.recording import Recording, Segment, Segmentation

    try:
        # Get the recording
        recording = Recording.objects.get(id=recording_id)

        # Check if recording file exists
        if not recording.wav_file or not os.path.exists(recording.wav_file.path):
            error_msg = f"WAV file not found for recording {recording_id}"

            return {"status": "error", "message": error_msg}

        # Run the automated segmentation
        try:
            # Find the segmentation record by ID - more reliable than using task_id
            segmentation = Segmentation.objects.get(id=segmentation_id)
            
            # Update task_id in the segmentation record to match what the worker sees
            if segmentation.task_id != self.request.id:
                segmentation.task_id = self.request.id
                segmentation.save(update_fields=['task_id'])

            # Determine which algorithm to use based on the segmentation's algorithm type
            algorithm = segmentation.algorithm
            algorithm_type = "threshold"  # Default

            if algorithm and hasattr(algorithm, "algorithm_type"):
                algorithm_type = algorithm.algorithm_type

            if algorithm_type == "energy":

                from ..utils import energy_based_segment_audio

                onsets, offsets = energy_based_segment_audio(
                    recording.wav_file.path,
                    min_duration_ms=min_duration_ms,
                    smooth_window=smooth_window,
                    threshold_factor=threshold_factor,
                    low_freq=low_freq,
                    high_freq=high_freq,
                )
            else:
                # Default to threshold-based

                from ..utils import auto_segment_audio

                onsets, offsets = auto_segment_audio(
                    recording.wav_file.path,
                    min_duration_ms=min_duration_ms,
                    smooth_window=smooth_window,
                    threshold_factor=threshold_factor,
                    low_freq=low_freq,
                    high_freq=high_freq,
                )
        except Exception as e:
            error_msg = f"Error during auto-segmentation: {str(e)}"

            return {"status": "error", "message": error_msg}

        # Create database segments from the detected onsets/offsets
        segments_created = 0

        with transaction.atomic():
            # The segmentation has already been retrieved by ID
            # No need to look it up again by task_id

            # Update the segmentation status to completed
            segmentation.status = "completed"
            segmentation.progress = 100
            segmentation.save()

            # Create segments for each onset/offset pair
            for i in range(len(onsets)):
                # Generate segment name
                segment_name = f"Auto Segment {i+1}"

                # Create segment and associate with the new segmentation
                segment = Segment(
                    recording=recording,
                    segmentation=segmentation,
                    name=segment_name,
                    onset=onsets[i],
                    offset=offsets[i],
                    created_by=recording.created_by,  # Use recording's creator
                    notes="Created by automated segmentation",
                )
                segment.save(manual_edit=False)  # Don't mark as manually edited for automated segmentation
                segments_created += 1

        # Return success result with details
        result = {
            "status": "success",
            "recording_id": recording_id,
            "segments_created": segments_created,
            "total_segments_found": len(onsets),
            "parameters": {
                "min_duration_ms": min_duration_ms,
                "smooth_window": smooth_window,
                "threshold_factor": threshold_factor,
            },
        }


        return result

    except Exception as e:

        return {"status": "error", "message": str(e)}
