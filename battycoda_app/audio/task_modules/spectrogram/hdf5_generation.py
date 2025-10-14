"""
HDF5 spectrogram generation for full recordings.
"""
import os
import uuid

from django.conf import settings

import numpy as np
from celery import shared_task


def generate_hdf5_spectrogram(recording_id, celery_task_id=None):
    """
    Generate a full HDF5 spectrogram for a recording.

    Args:
        recording_id: ID of the Recording model
        celery_task_id: Optional Celery task ID for job tracking

    Returns:
        dict: Result with the spectrogram file path
    """
    import soundfile as sf

    from battycoda_app.models.recording import Recording
    from battycoda_app.models.spectrogram import SpectrogramJob

    job = None
    try:
        if celery_task_id:
            job = SpectrogramJob.objects.filter(
                recording_id=recording_id,
                celery_task_id=celery_task_id
            ).first()
        else:
            job = SpectrogramJob.objects.filter(
                recording_id=recording_id,
                status__in=['pending', 'in_progress']
            ).first()
    except:
        pass

    def update_job_progress(progress, status=None):
        """Helper function to update job progress"""
        if job:
            try:
                job.progress = progress
                if status:
                    job.status = status
                job.save()
            except:
                pass

    try:
        recording = Recording.all_objects.get(id=recording_id)
        update_job_progress(20, 'in_progress')

        wav_path = recording.wav_file.path

        if recording.spectrogram_file:
            base_name = recording.spectrogram_file.replace('.png', '').replace('.h5', '')
            spectrogram_filename = f"{base_name}.h5"
        else:
            spectrogram_filename = f"{uuid.uuid4().hex}.h5"
            recording.spectrogram_file = spectrogram_filename
            recording.save()

        output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, spectrogram_filename)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            update_job_progress(100, 'completed')
            if job:
                job.output_file_path = output_path
                job.save()
            return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": True}

        update_job_progress(30)
        audio_data, sample_rate = sf.read(wav_path)
        update_job_progress(50)

        max_duration_samples = 10 * 60 * sample_rate
        if len(audio_data) > max_duration_samples:
            downsample_factor = int(len(audio_data) / max_duration_samples) + 1
            audio_data = audio_data[::downsample_factor]
            effective_sample_rate = sample_rate / downsample_factor
        else:
            effective_sample_rate = sample_rate

        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)

        update_job_progress(70)

        import librosa
        stft = librosa.stft(audio_data, hop_length=512, n_fft=2048)
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)

        max_freq_hz = 128000
        freq_per_bin = (effective_sample_rate / 2) / (2048 / 2)
        max_bin = int(max_freq_hz / freq_per_bin)
        spectrogram = spectrogram[:max_bin, :]

        spectrogram = spectrogram.astype(np.float16)

        update_job_progress(80)

        import h5py

        with h5py.File(output_path, 'w') as f:
            f.create_dataset('spectrogram', data=spectrogram, dtype='float16', compression='gzip', compression_opts=9)
            f.attrs['sample_rate'] = effective_sample_rate
            f.attrs['hop_length'] = 512
            f.attrs['n_fft'] = 2048
            f.attrs['duration'] = len(audio_data) / effective_sample_rate
            f.attrs['n_frames'] = spectrogram.shape[1]
            f.attrs['n_freq_bins'] = spectrogram.shape[0]

        update_job_progress(90)

        update_job_progress(100, 'completed')
        if job:
            job.output_file_path = output_path
            job.save()

        return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": False}

    except Exception as e:
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()

        return {"status": "error", "message": str(e), "recording_id": recording_id}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.spectrogram.hdf5_generation.generate_recording_spectrogram")
def generate_recording_spectrogram(self, recording_id):
    """
    Celery task to generate a full HDF5 spectrogram for a recording.

    Args:
        recording_id: ID of the Recording model

    Returns:
        dict: Result with the spectrogram file path
    """
    return generate_hdf5_spectrogram(recording_id, self.request.id)
