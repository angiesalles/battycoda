"""
HDF5 spectrogram generation for full recordings.
"""

import logging
import os
import uuid

from celery import shared_task
from django.conf import settings
from django.db import DatabaseError

logger = logging.getLogger(__name__)


def generate_hdf5_spectrogram(recording_id, celery_task_id=None):
    """
    Generate a full HDF5 spectrogram for a recording.

    Args:
        recording_id: ID of the Recording model
        celery_task_id: Optional Celery task ID for job tracking

    Returns:
        dict: Result with the spectrogram file path
    """

    from battycoda_app.models.recording import Recording
    from battycoda_app.models.spectrogram import SpectrogramJob

    job = None
    try:
        if celery_task_id:
            job = SpectrogramJob.objects.filter(recording_id=recording_id, celery_task_id=celery_task_id).first()
        else:
            job = SpectrogramJob.objects.filter(
                recording_id=recording_id, status__in=["pending", "in_progress"]
            ).first()
    except DatabaseError as e:
        logger.warning(f"Could not fetch SpectrogramJob for recording {recording_id}: {e}")

    def update_job_progress(progress, status=None):
        """Helper function to update job progress"""
        if job:
            try:
                job.progress = progress
                if status:
                    job.status = status
                job.save()
            except DatabaseError as e:
                logger.debug(f"Could not update job progress: {e}")

    try:
        recording = Recording.all_objects.get(id=recording_id)
        update_job_progress(20, "in_progress")

        wav_path = recording.wav_file.path

        if recording.spectrogram_file:
            base_name = recording.spectrogram_file.replace(".png", "").replace(".h5", "")
            spectrogram_filename = f"{base_name}.h5"
        else:
            spectrogram_filename = f"{uuid.uuid4().hex}.h5"
            recording.spectrogram_file = spectrogram_filename
            recording.save()

        output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, spectrogram_filename)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            update_job_progress(100, "completed")
            if job:
                job.output_file_path = output_path
                job.save()
            return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": True}

        # Use chunked processing to avoid loading entire file into memory
        from .hdf5_generation_chunked import generate_hdf5_spectrogram_chunked

        result = generate_hdf5_spectrogram_chunked(wav_path, output_path, progress_callback=update_job_progress)

        update_job_progress(90)

        update_job_progress(100, "completed")
        if job:
            job.output_file_path = output_path
            job.save()

        return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": False}

    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.save()

        return {"status": "error", "message": str(e), "recording_id": recording_id}


@shared_task(
    bind=True, name="battycoda_app.audio.task_modules.spectrogram.hdf5_generation.generate_recording_spectrogram"
)
def generate_recording_spectrogram(self, recording_id):
    """
    Celery task to generate a full HDF5 spectrogram for a recording.

    Args:
        recording_id: ID of the Recording model

    Returns:
        dict: Result with the spectrogram file path
    """
    return generate_hdf5_spectrogram(recording_id, self.request.id)
