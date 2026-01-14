
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
import logging

from .utils_modules.validation import get_int_param

logger = logging.getLogger(__name__)

@login_required
def task_spectrogram_view(request, task_id):
    """Simple spectrogram endpoint - just task ID and overview flag.

    Optional URL parameters:
    - overview: 1 for overview, 0 for detail (default: 0)
    """
    from django.shortcuts import get_object_or_404
    from django.conf import settings
    from .models.task import Task
    from .models.recording import Recording
    from .audio.modules.audio_processing import normal_hwin, overview_hwin
    from .audio.colormaps import ROSEUS_COLORMAP
    import io
    import os
    import h5py
    import numpy as np
    from PIL import Image

    task = get_object_or_404(Task, id=task_id)

    if task.created_by != request.user and (not request.user.profile.group or task.group != request.user.profile.group):
        return HttpResponse("Permission denied", status=403)

    if not task.batch or not task.batch.wav_file:
        return HttpResponse("Task has no associated audio file", status=404)

    is_overview = request.GET.get('overview', '0') == '1'
    hwin = overview_hwin(task.species) if is_overview else normal_hwin(task.species)

    start_time = task.onset - (hwin[0] / 1000)
    end_time = task.offset + (hwin[1] / 1000)

    # Will be clamped to recording duration later

    try:
        from .audio.task_modules.spectrogram.utils import ensure_hdf5_exists

        wav_path = task.batch.wav_file.path
        logger.info(f"Task {task_id}: Looking for recording with wav_file={task.batch.wav_file.name}")
        recording = Recording.all_objects.filter(wav_file=task.batch.wav_file.name).first()

        if not recording:
            logger.error(f"Task {task_id}: No recording found")
            return HttpResponse("No recording found for this task", status=404)

        logger.info(f"Task {task_id}: Found recording {recording.id}, calling ensure_hdf5_exists")
        success, error_response = ensure_hdf5_exists(recording, request.user)
        if not success:
            logger.error(f"Task {task_id}: ensure_hdf5_exists failed: {error_response}")
            return error_response

        logger.info(f"Task {task_id}: HDF5 exists, loading from {recording.spectrogram_file}")
        h5_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file)

        with h5py.File(h5_path, 'r') as f:
            sample_rate = float(f.attrs['sample_rate'])
            n_fft = int(f.attrs.get('n_fft', 512))
            hop_length = int(f.attrs.get('hop_length', n_fft // 4))
            duration = float(f.attrs['duration'])
            n_frames = int(f.attrs['n_frames'])
            n_freq_bins = int(f.attrs['n_freq_bins'])

            # Calculate frames per second
            time_per_frame = hop_length / sample_rate

            # Calculate how many frames the full requested window needs
            requested_duration = end_time - start_time
            requested_frames = int(requested_duration / time_per_frame)

            # Clamp times to valid recording boundaries
            clamped_start_time = max(0, start_time)
            clamped_end_time = min(duration, end_time)

            start_frame = int((clamped_start_time / duration) * n_frames)
            end_frame = int((clamped_end_time / duration) * n_frames)

            # Extract actual data from recording
            actual_data = f['spectrogram'][:, start_frame:end_frame]

            # Pad with silence (-80 dB) if window extends beyond recording
            pad_start = int((clamped_start_time - start_time) / time_per_frame) if start_time < 0 else 0
            pad_end = int((end_time - clamped_end_time) / time_per_frame) if end_time > duration else 0

            if pad_start > 0 or pad_end > 0:
                # Calculate total frames based on actual data size + padding to avoid rounding errors
                total_frames = pad_start + actual_data.shape[1] + pad_end
                spectrogram_data = np.full((n_freq_bins, total_frames), -80, dtype=np.float16)
                spectrogram_data[:, pad_start:pad_start + actual_data.shape[1]] = actual_data
            else:
                spectrogram_data = actual_data

        spectrogram_float = spectrogram_data.astype(np.float32)

        height, width = spectrogram_float.shape
        img = Image.new('RGB', (width, height))
        pixels = img.load()

        spec_min = spectrogram_float.min()
        spec_max = spectrogram_float.max()
        spec_range = spec_max - spec_min if spec_max > spec_min else 1

        for y in range(height):
            for x in range(width):
                value = (spectrogram_float[height - 1 - y, x] - spec_min) / spec_range
                index = int(np.clip(value * 255, 0, 255))
                color = ROSEUS_COLORMAP[index]
                pixels[x, y] = tuple(color)

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        png_data = buf.read()
        buf.close()

        return HttpResponse(png_data, content_type='image/png')

    except Exception as e:
        logger.exception(f"Task {task_id}: Exception in task_spectrogram_view: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500)

@login_required
def task_audio_snippet_view(request, task_id):
    """Simple audio snippet endpoint that only requires task ID.

    Optional URL parameters:
    - channel: Audio channel (0 or 1), defaults to 0
    - overview: True/False for overview vs detail window, defaults to False
    """
    from django.shortcuts import get_object_or_404
    from .models.task import Task
    from .audio.modules.audio_processing import get_audio_bit, normal_hwin, overview_hwin
    from .audio.utils import appropriate_file
    import os
    import numpy as np

    # Get the task
    task = get_object_or_404(Task, id=task_id)

    # Check permissions
    if task.created_by != request.user and (not request.user.profile.group or task.group != request.user.profile.group):
        return HttpResponse("Permission denied", status=403)

    # Get the wav file path
    if task.batch and task.batch.wav_file:
        wav_path = task.batch.wav_file.path
    else:
        return HttpResponse("Task has no associated audio file", status=404)

    # Get optional parameters with defaults
    channel = get_int_param(request, 'channel', default=0, min_val=0)
    overview = request.GET.get('overview', 'False') == 'True'

    # Determine window size
    hwin = overview_hwin if overview else normal_hwin

    # Build extra params for get_audio_bit
    extra_params = {
        'onset': str(task.onset),
        'offset': str(task.offset)
    }

    # Check cache first
    import hashlib
    file_hash = hashlib.md5(wav_path.encode()).hexdigest()
    file_args = {
        'call': '0',
        'channel': str(channel),
        'hash': file_hash,
        'overview': 'True' if overview else 'False',
        'onset': str(task.onset),
        'offset': str(task.offset),
        'loudness': '1.0'
    }
    cache_path = appropriate_file(wav_path, file_args)

    # Return cached file if it exists
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return FileResponse(open(cache_path, 'rb'), content_type='audio/wav')

    # Generate the audio snippet
    try:
        audio_data, sample_rate, _ = get_audio_bit(wav_path, 0, hwin(), extra_params)

        if audio_data is None or len(audio_data) == 0:
            return HttpResponse("Failed to extract audio data", status=500)

        # Extract the specific channel
        if len(audio_data.shape) > 1 and channel < audio_data.shape[1]:
            audio_data = audio_data[:, channel]
        elif len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        # Ensure 1D
        if len(audio_data.shape) > 1:
            audio_data = audio_data.flatten()

        # Apply slowdown
        slowdown = 5
        sample_rate_out = sample_rate // slowdown
        audio_data = np.repeat(audio_data, slowdown).astype('float32')

        # Ensure proper range
        if np.isnan(audio_data).any() or np.isinf(audio_data).any():
            audio_data = np.nan_to_num(audio_data)

        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val

        # Write to cache
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        import soundfile as sf
        sf.write(cache_path, audio_data, sample_rate_out)

        return FileResponse(open(cache_path, 'rb'), content_type='audio/wav')

    except Exception as e:
        return HttpResponse(f"Error generating audio: {str(e)}", status=500)

@login_required 
def simple_audio_bit_view(request):
    """Simple audio bit delivery using deliverAudioBit function"""
    # Validate required parameters
    required_params = ['file_path', 'onset', 'offset']
    for param in required_params:
        if param not in request.GET:
            return HttpResponse(f"Missing required parameter: {param}", status=400)
    
    try:
        file_path = request.GET['file_path']
        onset = float(request.GET['onset'])
        offset = float(request.GET['offset'])
        loudness = float(request.GET.get('loudness', '1.0'))
        pitch_shift = float(request.GET.get('pitch_shift', '1.0'))
        
        # Use the new deliverAudioBit function
        from .audio.modules.audio_processing import deliverAudioBit
        return deliverAudioBit(file_path, onset, offset, loudness, pitch_shift)
        
    except ValueError as e:
        return HttpResponse(f"Invalid parameter value: {str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

