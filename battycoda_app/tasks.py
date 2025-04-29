from celery import shared_task

@shared_task
def process_audio_file(file_path):
    """
    Process an uploaded audio file

    This is a placeholder task that can be expanded for audio processing
    """

    # TODO: Implement actual audio processing
    return True

@shared_task
def calculate_audio_duration(recording_id):
    """
    Calculate and update the duration and sample rate for a recording.
    
    This task should only be triggered when file_ready=True, ensuring that
    the file is fully committed to disk before processing.
    """
    import os
    import logging

    import soundfile as sf

    from .models.recording import Recording
    
    logger = logging.getLogger(__name__)

    try:
        # Get the recording from the database
        recording = Recording.objects.get(id=recording_id)

        # Skip if both duration and sample rate are already set
        if recording.duration and recording.sample_rate:
            logger.info(f"Recording {recording_id} already has duration and sample rate set")
            return True

        # Double-check that file_ready is True
        if not recording.file_ready:
            logger.warning(f"Task called for recording {recording_id} with file_ready=False, skipping")
            return False

        # Check if file exists (should exist since file_ready=True)
        if not os.path.exists(recording.wav_file.path):
            logger.error(f"File missing for recording {recording_id} despite file_ready=True: {recording.wav_file.path}")
            return False

        # Extract audio information from file
        info = sf.info(recording.wav_file.path)
        duration = info.duration
        sample_rate = info.samplerate
        
        logger.info(f"Audio info for recording {recording_id}: duration={duration}s, sample_rate={sample_rate}Hz")

        # Update the recording
        update_fields = []

        # Only update duration if it's not already set
        if not recording.duration:
            recording.duration = duration
            update_fields.append("duration")

        # Only update sample_rate if it's not already set
        if not recording.sample_rate:
            recording.sample_rate = sample_rate
            update_fields.append("sample_rate")

        # Use update_fields to avoid triggering save signal again
        if update_fields:
            recording.save(update_fields=update_fields)
            logger.info(f"Successfully updated recording {recording_id} with duration {duration}s and sample rate {sample_rate}Hz")

        return True

    except Recording.DoesNotExist:
        logger.error(f"Recording {recording_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Error calculating audio duration for recording {recording_id}: {str(e)}")
        return False

@shared_task
def generate_spectrogram(file_path, output_path=None):
    """
    Generate a spectrogram from an audio file

    This is a placeholder task that can be expanded for spectrogram generation
    """

    # TODO: Implement actual spectrogram generation
    return True