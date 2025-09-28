"""
Spectrogram generation tasks for BattyCoda.
"""
import os
import tempfile
import time

from django.conf import settings

import numpy as np
from celery import shared_task
from PIL import Image

from ...utils_modules.path_utils import convert_path_to_os_specific
from ..utils import appropriate_file, get_audio_bit, normal_hwin, overview_hwin

# Import soundfile in the functions where needed


def make_spectrogram(audio_data, sample_rate, nperseg=512, noverlap=None, use_mel=True, n_mels=128):
    """
    Core spectrogram generation function with mel scale and logarithmic color scaling.
    
    Args:
        audio_data: 1D numpy array of audio samples
        sample_rate: Sample rate of the audio
        nperseg: Window size for spectrogram
        noverlap: Overlap size (defaults to nperseg//2 if None)
        use_mel: Whether to use mel scale (default True)
        n_mels: Number of mel bins if using mel scale
        
    Returns:
        tuple: (frequencies, times, spectrogram_data) where spectrogram_data is log-scaled
    """
    import librosa
    
    if noverlap is None:
        noverlap = nperseg // 2
    
    if use_mel:
        # Use mel-scale spectrogram for better frequency representation
        hop_length = nperseg - noverlap
        mel_spectrogram = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sample_rate,
            n_fft=nperseg,
            hop_length=hop_length,
            n_mels=n_mels,
            fmax=sample_rate/2
        )
        
        # Convert to format similar to scipy output
        spectrogram_data = mel_spectrogram
        times = np.linspace(0, len(audio_data)/sample_rate, mel_spectrogram.shape[1])
        frequencies = librosa.mel_frequencies(n_mels=n_mels, fmax=sample_rate/2)
    else:
        # Use standard linear frequency spectrogram
        from scipy import signal
        frequencies, times, spectrogram_data = signal.spectrogram(
            audio_data, 
            fs=sample_rate,
            nperseg=nperseg,
            noverlap=noverlap
        )
    
    return frequencies, times, spectrogram_data


def roseus_colormap(val):
    """Convert value [0,1] to roseus (pink-rose-purple) RGB"""
    r = np.interp(val, [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                 [0.1, 0.3, 0.7, 0.9, 0.95, 1.0])
    g = np.interp(val, [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                 [0.0, 0.1, 0.3, 0.6, 0.8, 0.9])
    b = np.interp(val, [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                 [0.2, 0.4, 0.6, 0.7, 0.8, 0.9])
    return r, g, b


def apply_logarithmic_color_scaling_and_colormap(spectrogram_data, contrast=1.0):
    """
    Apply logarithmic color scaling and roseus colormap to spectrogram data.
    
    Args:
        spectrogram_data: 2D numpy array of spectrogram power values
        contrast: Contrast enhancement factor
        
    Returns:
        numpy.ndarray: RGB image data (height, width, 3) with values 0-255
    """
    # Apply logarithmic color scaling for better dynamic range visualization
    # First convert to dB scale
    sxx_db = 10 * np.log10(spectrogram_data + 1e-10)
    
    # Apply contrast enhancement with logarithmic scaling
    temocontrast = 10**contrast
    processed_data = np.arctan(temocontrast * sxx_db)
    
    # Apply additional logarithmic scaling to colors for better contrast
    log_scaled = np.log10(processed_data - np.min(processed_data) + 1)
    
    # Normalize to 0-255 range with logarithmic scaling
    normalized_data = (log_scaled - log_scaled.min()) / (log_scaled.max() - log_scaled.min()) * 255
    
    # Flip vertically (frequencies should go from low to high, bottom to top)
    normalized_data = np.flipud(normalized_data)
    
    # Convert to 8-bit unsigned integer
    img_data = normalized_data.astype(np.uint8)
    
    # Apply roseus colormap
    height, width = img_data.shape
    rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i in range(height):
        for j in range(width):
            val = img_data[i, j] / 255.0
            r, g, b = roseus_colormap(val)
            rgb_data[i, j, 0] = int(255 * r)
            rgb_data[i, j, 1] = int(255 * g)
            rgb_data[i, j, 2] = int(255 * b)
    
    return rgb_data

@shared_task(
    bind=True,
    name="battycoda_app.audio.task_modules.spectrogram_tasks.generate_spectrogram_task",
    max_retries=3,
    retry_backoff=True,
)
def generate_spectrogram_task(self, path, args, output_path=None):
    """
    Task to generate a spectrogram image.

    Args:
        path: Path to the audio file
        args: Dict of parameters (call, channel, etc.)
        output_path: Optional explicit output path

    Returns:
        dict: Result information
    """
    # Time tracking removed

    # Create minimal task identifier for logging
    call = args.get("call", "?")
    channel = args.get("channel", "?")
    task_id = f"Call {call} Ch {channel}"

    try:
        # Skip state updates to reduce logs

        # Get file paths
        if output_path is None:
            output_path = appropriate_file(path, args)

        # Convert URL path to OS path (if not already converted)
        if path.startswith("home/"):
            os_path = convert_path_to_os_specific(path)
        else:
            os_path = path

        # Generate the spectrogram
        success, output_file, error = generate_spectrogram(os_path, args, output_path)

        # Only log results for failures
        # Skip failure logging
        
        if success:
            return {"status": "success", "file_path": output_file, "original_path": path, "args": args}
        else:
            return {
                "status": "error",
                "error": error if error else "Failed to generate spectrogram",
                "file_path": output_file,
            }

    except Exception as e:
        # Only log full errors for catastrophic failures

        # Retry the task if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2**self.request.retries)

        return {"status": "error", "error": str(e), "path": path, "args": args}

@shared_task(bind=True, name="audio.prefetch_spectrograms")
def prefetch_spectrograms(self, path, base_args, call_range):
    """
    Prefetch multiple spectrograms for a range of calls.
    DISABLED - This function now does nothing to reduce server load

    Args:
        path: Path to the audio file
        base_args: Base arguments dict
        call_range: Tuple of (start_call, end_call)

    Returns:
        dict: Status indicating the function is disabled
    """

    # Return a summary indicating prefetch is disabled
    return {"status": "disabled", "message": "Prefetching is disabled for performance reasons"}

@shared_task(bind=True, name="battycoda_app.audio.task_modules.spectrogram_tasks.generate_recording_spectrogram")
def generate_recording_spectrogram(self, recording_id):
    """
    Generate a full spectrogram for a recording.

    Args:
        recording_id: ID of the Recording model

    Returns:
        dict: Result with the spectrogram file path
    """
    import hashlib
    import os
    import tempfile

    from django.conf import settings

    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    import soundfile as sf
    from PIL import Image

    from ...models.recording import Recording
    from ...models.spectrogram import SpectrogramJob

    # Get the SpectrogramJob associated with this task
    job = None
    try:
        job = SpectrogramJob.objects.filter(
            recording_id=recording_id,
            celery_task_id=self.request.id
        ).first()
    except:
        pass  # Job tracking is optional

    def update_job_progress(progress, status=None):
        """Helper function to update job progress"""
        if job:
            try:
                job.progress = progress
                if status:
                    job.status = status
                job.save()
            except:
                pass  # Don't fail if job update fails

    try:
        # Get the recording
        recording = Recording.objects.get(id=recording_id)
        update_job_progress(20, 'in_progress')

        # Get the WAV file path
        wav_path = recording.wav_file.path

        # Create a hash of the file path for caching
        file_hash = hashlib.md5(wav_path.encode()).hexdigest()

        # Create the output directory and filename
        output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{file_hash}.png")

        # Check if file already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            update_job_progress(100, 'completed')
            if job:
                job.output_file_path = output_path
                job.save()
            return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": True}

        # Load the audio file
        update_job_progress(30)
        audio_data, sample_rate = sf.read(wav_path)
        update_job_progress(50)

        # For very long recordings, downsample to improve performance
        max_duration_samples = 10 * 60 * sample_rate  # 10 minutes maximum
        if len(audio_data) > max_duration_samples:
            # Downsample by taking every nth sample
            downsample_factor = int(len(audio_data) / max_duration_samples) + 1
            audio_data = audio_data[::downsample_factor]
            effective_sample_rate = sample_rate / downsample_factor

        else:
            effective_sample_rate = sample_rate

        # If stereo, convert to mono by averaging channels
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)

        # Generate spectrogram using scipy directly
        update_job_progress(70)
        
        # Generate spectrogram using shared function
        nperseg = 512
        noverlap = nperseg // 2
        frequencies, times, spectrogram_data = make_spectrogram(
            audio_data, effective_sample_rate, nperseg, noverlap, use_mel=True, n_mels=128
        )
        
        # Apply logarithmic color scaling and roseus colormap
        rgb_image = apply_logarithmic_color_scaling_and_colormap(spectrogram_data, contrast=1.0)
        
        update_job_progress(80)
        
        # Calculate target image dimensions
        duration_seconds = len(audio_data) / effective_sample_rate
        target_width = max(800, int(duration_seconds * 50))  # ~50 pixels per second minimum
        target_height = 400  # Fixed height for good frequency resolution
        
        # Create PIL image and resize to target dimensions
        pil_image = Image.fromarray(rgb_image)
        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        update_job_progress(90)
        
        # Save directly as PNG
        pil_image.save(output_path, format="PNG", optimize=True)
        
        # Update job completion
        update_job_progress(100, 'completed')
        if job:
            job.output_file_path = output_path
            job.save()

        return {"status": "success", "file_path": output_path, "recording_id": recording_id, "cached": False}

    except Exception as e:
        # Update job as failed
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
        
        return {"status": "error", "message": str(e), "recording_id": recording_id}

def generate_spectrogram(path, args, output_path=None):
    """
    Pure function to generate a spectrogram.

    Args:
        path: Path to the audio file
        args: Dict of parameters (call, channel, etc.)
        output_path: Optional output path, will be generated if not provided

    Returns:
        tuple: (success, output_path, error_message)
    """
    # Time tracking removed

    if output_path is None:
        output_path = appropriate_file(path, args)

    # Extract basic parameters for minimal task ID
    call = args.get("call", "0")
    channel = args.get("channel", "0")
    task_id = f"Call {call} Ch {channel}"

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Parse parameters
        call_to_do = int(args.get("call", 0))
        overview = args.get("overview") == "1" or args.get("overview") == "True"
        channel = int(args.get("channel", 0))
        contrast = float(args.get("contrast", 4))
        low_overlap = args.get("low_overlap") == "1" or args.get("low_overlap") == "True"

        # Select window size
        hwin = overview_hwin() if overview else normal_hwin()

        # Get audio data with direct segment loading if possible
        extra_params = None
        if "onset" in args and "offset" in args:
            extra_params = {"onset": args["onset"], "offset": args["offset"]}

        thr_x1, fs, hashof = get_audio_bit(path, call_to_do, hwin, extra_params)

        # Validate audio data
        if thr_x1 is None or thr_x1.size == 0:
            return False, output_path, "Audio data is empty"

        # Check channel is valid
        if channel >= thr_x1.shape[1]:
            return False, output_path, f"Channel index {channel} is out of bounds"

        # Extract channel
        thr_x1 = thr_x1[:, channel]

        # OPTIMIZATION: Skip hash validation to reduce overhead
        # This is safe because we're using file paths that are already validated

        # Use high-quality spectrogram parameters for better visual detail
        # - Higher nperseg for better frequency resolution
        # - Higher overlap for smoother time transitions
        # - Larger nfft for better frequency bins
        if overview:
            # For overview, use very high detail since we're showing more
            nperseg = 2**9  # 512
            if low_overlap:
                # Use 50% overlap for memory efficiency (e.g., for previews)
                noverlap = nperseg // 2  # 50% overlap
            else:
                noverlap = int(nperseg * 0.99)  # 99% overlap for highest quality
            nfft = 2**10  # 1024 for excellent frequency resolution
        else:
            # For call detail view, use high quality parameters
            nperseg = 2**8  # 256
            noverlap = 254
            nfft = 2**8

        # Generate spectrogram using shared function
        n_mels = 128 if overview else 64  # More mel bins for overview
        f, t, sxx = make_spectrogram(
            thr_x1, fs, nperseg=nfft, noverlap=noverlap, use_mel=True, n_mels=n_mels
        )

        # Apply logarithmic color scaling and roseus colormap using shared function
        rgb_data = apply_logarithmic_color_scaling_and_colormap(sxx, contrast=contrast)

        # Performance logging removed

        # Create and save image - measure time
        # Time tracking removed

        # Create PIL Image and save
        img = Image.fromarray(rgb_data)

        # Resize to standard dimensions (800x600)
        img = img.resize((800, 600), Image.Resampling.LANCZOS)

        # Save with minimal compression for speed
        img.save(output_path, format="PNG", compress_level=1)

        # Performance logging removed

        # Verify the file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            # Performance logging removed
            return True, output_path, None
        else:

            return False, output_path, "Failed to create output file"

    except Exception as e:

        # Simply return the error, no attempt to create error image
        return False, output_path, str(e)
