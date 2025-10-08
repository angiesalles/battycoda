"""
Utility functions for spectrogram operations.
"""
import os
from django.conf import settings
from django.http import HttpResponse


def ensure_hdf5_exists(recording, user):
    """
    Ensure HDF5 spectrogram file exists for a recording, generating if needed.

    Args:
        recording: Recording model instance
        user: User requesting the spectrogram

    Returns:
        tuple: (success: bool, error_response: HttpResponse or None)
    """
    if not recording.spectrogram_file:
        from .hdf5_generation import generate_hdf5_spectrogram
        from battycoda_app.models.spectrogram import SpectrogramJob

        existing_job = SpectrogramJob.objects.filter(
            recording=recording,
            status__in=['pending', 'in_progress']
        ).first()

        if not existing_job:
            job = SpectrogramJob.objects.create(
                recording=recording,
                status='pending',
                name=f"Spectrogram for {recording.name}",
                created_by=user,
                group=recording.group
            )
            result = generate_hdf5_spectrogram(recording.id)
            if result.get('status') != 'success':
                return False, HttpResponse(f"Failed to generate spectrogram: {result.get('message', 'Unknown error')}", status=500)
        else:
            return False, HttpResponse("Spectrogram generation in progress, please refresh in a moment", status=202)

    h5_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file)

    if not os.path.exists(h5_path):
        from .hdf5_generation import generate_hdf5_spectrogram
        from battycoda_app.models.spectrogram import SpectrogramJob

        job = SpectrogramJob.objects.create(
            recording=recording,
            status='pending',
            name=f"Spectrogram for {recording.name}",
            created_by=user,
            group=recording.group
        )
        result = generate_hdf5_spectrogram(recording.id)
        if result.get('status') != 'success':
            return False, HttpResponse(f"Failed to generate spectrogram: {result.get('message', 'Unknown error')}", status=500)

    return True, None
