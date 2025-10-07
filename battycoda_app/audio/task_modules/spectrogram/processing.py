"""
Spectrogram processing functions for BattyCoda.
"""
import os
from django.conf import settings
from PIL import Image

from battycoda_app.audio.utils import appropriate_file, normal_hwin, overview_hwin


def generate_spectrogram(path, args, output_path=None):
    """
    Pure function to generate a spectrogram from cached HDF5 data.

    This function now loads data from the pre-computed HDF5 spectrogram file
    and generates a PNG for the requested segment/view.

    Args:
        path: Path to the audio file (used to find the recording)
        args: Dict of parameters (call, channel, onset, offset, overview, etc.)
        output_path: Optional output path, will be generated if not provided

    Returns:
        tuple: (success, output_path, error_message)
    """
    if output_path is None:
        output_path = appropriate_file(path, args)

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Parse parameters
        overview = args.get("overview") == "1" or args.get("overview") == "True"
        channel = int(args.get("channel", 0))

        # Get onset/offset for the segment
        if "onset" in args and "offset" in args:
            onset = float(args["onset"])
            offset = float(args["offset"])
        else:
            return False, output_path, "onset and offset required"

        # Find the recording from the path to get the HDF5 file
        from battycoda_app.models.recording import Recording
        try:
            # Try to find recording by wav file path
            recording = Recording.objects.filter(wav_file__icontains=os.path.basename(path)).first()
            if not recording or not recording.spectrogram_file:
                # Fall back to generating from raw audio if no HDF5 exists
                return generate_spectrogram_from_audio(path, args, output_path)
        except Exception:
            # Fall back to generating from raw audio
            return generate_spectrogram_from_audio(path, args, output_path)

        # Load HDF5 spectrogram data
        import h5py
        h5_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", recording.spectrogram_file)

        if not os.path.exists(h5_path):
            # Trigger HDF5 generation for this recording
            from battycoda_app.audio.task_modules.spectrogram.generation import generate_recording_spectrogram
            from battycoda_app.models.spectrogram import SpectrogramJob

            # Check if there's already a job in progress
            existing_job = SpectrogramJob.objects.filter(
                recording=recording,
                status__in=['pending', 'in_progress']
            ).first()

            if not existing_job:
                # Create a job and trigger generation
                job = SpectrogramJob.objects.create(
                    recording=recording,
                    status='pending'
                )
                # Run synchronously to ensure the file is available
                result = generate_recording_spectrogram(None, recording.id)
                if result.get('status') != 'success':
                    return False, output_path, f"Failed to generate HDF5: {result.get('message', 'Unknown error')}"
            else:
                # Job in progress, fall back to raw audio for now
                return generate_spectrogram_from_audio(path, args, output_path)

            # Verify the file now exists
            if not os.path.exists(h5_path):
                return generate_spectrogram_from_audio(path, args, output_path)

        with h5py.File(h5_path, 'r') as f:
            sample_rate = f.attrs['sample_rate']
            hop_length = f.attrs['hop_length']
            duration = f.attrs['duration']

            # Load full spectrogram data
            spectrogram_data = f['spectrogram'][:]

        # Calculate time window with padding
        if overview:
            # Overview: use overview_hwin for consistent padding
            pre_win, post_win = overview_hwin()
            padding_start = pre_win / 1000.0  # Convert ms to seconds
            padding_end = post_win / 1000.0
        else:
            # Detail: show just the call with minimal padding
            time_window = offset - onset
            padding_start = padding_end = time_window * 0.3  # 30% padding on each side

        start_time = max(0, onset - padding_start)
        end_time = min(duration, offset + padding_end)

        # Convert times to frame indices
        time_per_frame = hop_length / sample_rate
        start_frame = int(start_time / time_per_frame)
        end_frame = int(end_time / time_per_frame)

        # Extract the relevant time slice
        spectrogram_slice = spectrogram_data[:, start_frame:end_frame]

        # Generate PNG using matplotlib (same as make_spectrogram but from HDF5 data)
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import librosa.display
        import io

        plt.figure(figsize=(15, 6))
        librosa.display.specshow(spectrogram_slice,
                                sr=sample_rate,
                                hop_length=hop_length,
                                x_axis='time',
                                y_axis='hz',
                                cmap='viridis')

        plt.axis('off')
        plt.tight_layout()

        # Save to PNG
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=100)
        buf.seek(0)
        plt.close()

        # Save to file
        img = Image.open(buf)
        img.save(output_path, format="PNG", compress_level=1)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, output_path, None
        else:
            return False, output_path, "Failed to create output file"

    except Exception as e:
        return False, output_path, str(e)


def generate_spectrogram_from_audio(path, args, output_path):
    """
    Fallback function to generate spectrogram directly from audio file.
    Used when HDF5 cache doesn't exist.
    """
    try:
        # Parse parameters
        call_to_do = int(args.get("call", 0))
        overview = args.get("overview") == "1" or args.get("overview") == "True"
        channel = int(args.get("channel", 0))

        # Select window size
        hwin = overview_hwin() if overview else normal_hwin()

        # Get audio data
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

        # Generate spectrogram
        img = make_spectrogram(thr_x1, fs)

        # Save
        img.save(output_path, format="PNG", compress_level=1)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True, output_path, None
        else:
            return False, output_path, "Failed to create output file"

    except Exception as e:
        return False, output_path, str(e)
