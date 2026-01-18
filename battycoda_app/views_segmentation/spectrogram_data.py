"""
Views and utilities for spectrogram data.
"""

import json
import os
import struct

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models import SpectrogramJob
from battycoda_app.models.recording import Recording


def get_spectrogram_status(recording):
    """
    Get comprehensive spectrogram status for a recording.

    Returns:
        dict: Contains 'status', 'url', 'job', 'progress' information
    """
    try:
        # Check if recording has spectrogram file stored in database
        if recording.spectrogram_file:
            spectrogram_path = os.path.join(
                settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file
            )

            # Check if spectrogram file actually exists
            if os.path.exists(spectrogram_path) and os.path.getsize(spectrogram_path) > 0:
                return {
                    "status": "available",
                    "url": f"/media/spectrograms/recordings/{recording.spectrogram_file}",
                    "job": None,
                    "progress": 100,
                }

        # Check for existing jobs
        active_job = SpectrogramJob.objects.filter(recording=recording, status__in=["pending", "in_progress"]).first()

        if active_job:
            return {"status": "generating", "url": None, "job": active_job, "progress": active_job.progress}

        # Check for completed jobs with file
        completed_job = (
            SpectrogramJob.objects.filter(recording=recording, status="completed").order_by("-created_at").first()
        )

        if completed_job and completed_job.output_file_path and os.path.exists(completed_job.output_file_path):
            # Extract the relative URL from the full path
            relative_path = str(completed_job.output_file_path).replace(settings.MEDIA_ROOT, "").lstrip("/")
            return {"status": "available", "url": f"/media/{relative_path}", "job": completed_job, "progress": 100}

        # No spectrogram available, no active jobs
        return {"status": "not_available", "url": None, "job": None, "progress": 0}

    except Exception as e:
        return {"status": "error", "url": None, "job": None, "progress": 0, "error": str(e)}


@login_required
def get_spectrogram_data_view(request, recording_id):
    """
    API endpoint to serve spectrogram data for client-side rendering.
    Returns binary float16 data with metadata header.
    """
    recording = get_object_or_404(Recording.all_objects, id=recording_id)

    # Check permissions
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    try:
        # Check if HDF5 spectrogram file exists
        if not recording.spectrogram_file:
            return JsonResponse({"success": False, "error": "No spectrogram data available"}, status=404)

        h5_file_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file)

        if not os.path.exists(h5_file_path):
            return JsonResponse({"success": False, "error": "Spectrogram file not found"}, status=404)

        # Load spectrogram data as binary
        import h5py
        import numpy as np

        with h5py.File(h5_file_path, "r") as f:
            # Get metadata
            sample_rate = float(f.attrs["sample_rate"])
            n_fft = int(f.attrs["n_fft"])
            hop_length = int(f.attrs.get("hop_length", n_fft // 4))
            duration = float(f.attrs["duration"])
            n_frames = int(f.attrs["n_frames"])
            n_freq_bins = int(f.attrs["n_freq_bins"])

            # Load spectrogram data
            spectrogram_data = f["spectrogram"][:]

        # Create metadata JSON
        metadata = {
            "sample_rate": sample_rate,
            "hop_length": hop_length,
            "n_fft": n_fft,
            "duration": duration,
            "n_frames": n_frames,
            "n_freq_bins": n_freq_bins,
            "time_resolution": hop_length / sample_rate,
            "freq_resolution": sample_rate / n_fft,
        }
        metadata_json = json.dumps(metadata).encode("utf-8")
        metadata_length = len(metadata_json)

        # Create response with binary data
        # Format: [4 bytes: metadata length][metadata JSON][binary float16 array]
        response = HttpResponse(content_type="application/octet-stream")

        # Add caching headers - spectrogram data doesn't change
        # Cache for 1 year (31536000 seconds)
        response["Cache-Control"] = "public, max-age=31536000, immutable"

        # Add ETag based on file modification time for efficient revalidation

        file_mtime = os.path.getmtime(h5_file_path)
        etag = f'"{recording.id}-{int(file_mtime)}"'
        response["ETag"] = etag

        # Write metadata length as 4-byte integer
        response.write(struct.pack("<I", metadata_length))

        # Write metadata JSON
        response.write(metadata_json)

        # Write binary spectrogram data (float16, little-endian)
        # Ensure it's C-contiguous for efficient transfer
        if not spectrogram_data.flags["C_CONTIGUOUS"]:
            spectrogram_data = np.ascontiguousarray(spectrogram_data)
        response.write(spectrogram_data.tobytes())

        return response

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Error loading spectrogram data: {str(e)}"}, status=500)
