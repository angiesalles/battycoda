"""
Spectrogram generation tasks for BattyCoda.
"""
import os
import tempfile
import time
import uuid

from django.conf import settings

import numpy as np
from celery import shared_task
from PIL import Image

from ...utils_modules.path_utils import convert_path_to_os_specific
from ..utils import appropriate_file, get_audio_bit, normal_hwin, overview_hwin

# Import soundfile in the functions where needed


def make_spectrogram(audio_data, sample_rate, freq_min=None, freq_max=None):
    """
    Core spectrogram generation function using librosa.display.specshow with viridis colormap.
    
    Args:
        audio_data: 1D numpy array of audio samples
        sample_rate: Sample rate of the audio
        freq_min: Minimum frequency to display (Hz), None for no limit
        freq_max: Maximum frequency to display (Hz), None for no limit
        
    Returns:
        PIL.Image: Generated spectrogram image
    """
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for headless environment
    
    import librosa
    import librosa.display
    import matplotlib.pyplot as plt
    import io
    from PIL import Image
    
    # Generate STFT exactly as specified
    stft = librosa.stft(audio_data, hop_length=512, n_fft=2048)
    spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
    
    # Create the plot with configurable size (1500x600 pixels at 100 DPI)
    plt.figure(figsize=(15, 6))
    librosa.display.specshow(spectrogram, 
                            sr=sample_rate, 
                            hop_length=512, 
                            x_axis='time', 
                            y_axis='hz',
                            cmap='viridis')
    
    # Set frequency range if specified
    if freq_min is not None or freq_max is not None:
        current_ylim = plt.ylim()
        new_ymin = freq_min if freq_min is not None else current_ylim[0]
        new_ymax = freq_max if freq_max is not None else current_ylim[1]
        plt.ylim(new_ymin, new_ymax)
    
    # Remove axes and tight layout for clean image
    plt.axis('off')
    plt.tight_layout()
    
    # Convert to PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
    buf.seek(0)
    
    # Clean up matplotlib figure
    plt.close()
    
    # Return PIL Image
    return Image.open(buf)



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
    import os
    import tempfile

    from django.conf import settings

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
        # Get the recording (use all_objects to include hidden recordings)
        from ...models.recording import Recording
        recording = Recording.all_objects.get(id=recording_id)
        update_job_progress(20, 'in_progress')

        # Get the WAV file path
        wav_path = recording.wav_file.path

        # Generate a UUID-based filename or use existing one
        if recording.spectrogram_file:
            # Use existing filename, but ensure it has .h5 extension
            base_name = recording.spectrogram_file.replace('.png', '').replace('.h5', '')
            spectrogram_filename = f"{base_name}.h5"
        else:
            # Generate new UUID-based filename
            spectrogram_filename = f"{uuid.uuid4().hex}.h5"
            recording.spectrogram_file = spectrogram_filename
            recording.save()

        # Create the output directory and full path
        output_dir = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, spectrogram_filename)

        # Check if HDF5 file already exists
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

        # Generate STFT spectrogram data
        update_job_progress(70)
        
        # Generate STFT exactly as in make_spectrogram
        import librosa
        stft = librosa.stft(audio_data, hop_length=512, n_fft=2048)
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
        
        update_job_progress(80)
        
        # Save spectrogram data to HDF5 for efficient seeking
        import h5py
        
        with h5py.File(output_path, 'w') as f:
            # Store the spectrogram data
            f.create_dataset('spectrogram', data=spectrogram, compression='gzip', compression_opts=9)
            # Store metadata
            f.attrs['sample_rate'] = effective_sample_rate
            f.attrs['hop_length'] = 512
            f.attrs['n_fft'] = 2048
            f.attrs['duration'] = len(audio_data) / effective_sample_rate
            f.attrs['n_frames'] = spectrogram.shape[1]
            f.attrs['n_freq_bins'] = spectrogram.shape[0]
        
        update_job_progress(90)
        
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


def load_spectrogram_segment(h5_file_path, start_time, end_time):
    """
    Load a time segment of spectrogram data from HDF5 file.
    
    Args:
        h5_file_path: Path to the HDF5 spectrogram file
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        tuple: (spectrogram_segment, sample_rate, hop_length) or None if error
    """
    try:
        import h5py
        
        with h5py.File(h5_file_path, 'r') as f:
            # Get metadata
            sample_rate = f.attrs['sample_rate']
            hop_length = f.attrs['hop_length']
            duration = f.attrs['duration']
            n_frames = f.attrs['n_frames']
            
            # Calculate frame indices for the time range
            frames_per_second = sample_rate / hop_length
            start_frame = int(start_time * frames_per_second)
            end_frame = int(end_time * frames_per_second)
            
            # Clamp to valid range
            start_frame = max(0, start_frame)
            end_frame = min(n_frames, end_frame)
            
            if start_frame >= end_frame:
                return None
                
            # Load only the requested time segment
            spectrogram_segment = f['spectrogram'][:, start_frame:end_frame]
            
            return spectrogram_segment, sample_rate, hop_length
            
    except Exception as e:
        print(f"Error loading spectrogram segment: {e}")
        return None


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

        # Generate spectrogram using librosa.display.specshow approach
        img = make_spectrogram(thr_x1, fs)

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
