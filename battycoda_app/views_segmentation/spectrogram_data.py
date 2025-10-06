"""
Views for serving spectrogram data for client-side rendering.
"""
import json
import os
import struct

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models.recording import Recording


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

        with h5py.File(h5_file_path, 'r') as f:
            # Get metadata
            sample_rate = float(f.attrs['sample_rate'])
            hop_length = int(f.attrs['hop_length'])
            n_fft = int(f.attrs['n_fft'])
            duration = float(f.attrs['duration'])
            n_frames = int(f.attrs['n_frames'])
            n_freq_bins = int(f.attrs['n_freq_bins'])

            # Load spectrogram data
            spectrogram_data = f['spectrogram'][:]

        # Create metadata JSON
        metadata = {
            "sample_rate": sample_rate,
            "hop_length": hop_length,
            "n_fft": n_fft,
            "duration": duration,
            "n_frames": n_frames,
            "n_freq_bins": n_freq_bins,
            "time_resolution": hop_length / sample_rate,
            "freq_resolution": sample_rate / n_fft
        }
        metadata_json = json.dumps(metadata).encode('utf-8')
        metadata_length = len(metadata_json)

        # Create response with binary data
        # Format: [4 bytes: metadata length][metadata JSON][binary float16 array]
        response = HttpResponse(content_type='application/octet-stream')

        # Add caching headers - spectrogram data doesn't change
        # Cache for 1 year (31536000 seconds)
        response['Cache-Control'] = 'public, max-age=31536000, immutable'

        # Add ETag based on file modification time for efficient revalidation
        import time
        file_mtime = os.path.getmtime(h5_file_path)
        etag = f'"{recording.id}-{int(file_mtime)}"'
        response['ETag'] = etag

        # Write metadata length as 4-byte integer
        response.write(struct.pack('<I', metadata_length))

        # Write metadata JSON
        response.write(metadata_json)

        # Write binary spectrogram data (float16, little-endian)
        # Ensure it's C-contiguous for efficient transfer
        if not spectrogram_data.flags['C_CONTIGUOUS']:
            spectrogram_data = np.ascontiguousarray(spectrogram_data)
        response.write(spectrogram_data.tobytes())

        return response

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Error loading spectrogram data: {str(e)}"}, status=500)