"""
Base utilities for BattyCoda audio processing tasks.
"""

import time

# Configure logging


def log_performance(start_time, message):
    """Log performance with elapsed time - only for total task time"""
    # Only log total task completions to reduce log volume
    if "TOTAL" in message:
        elapsed = time.time() - start_time


def extract_audio_segment(wav_path, onset, offset=None):
    """
    Extract a segment of audio from a WAV file.
    Uses efficient seek operation to read only the needed segment without loading the entire file.
    Handles out-of-bounds requests by padding with zeros.

    Args:
        wav_path: Path to the WAV file
        onset: Start time in seconds (can be negative, will be zero-padded)
        offset: End time in seconds, or None to read until the end of the file
                (if greater than file duration, will be zero-padded)

    Returns:
        tuple: (audio_data, sample_rate)
    """
    try:
        import numpy as np
        import soundfile as sf

        # Get file info without reading all data
        info = sf.info(wav_path)
        sample_rate = info.samplerate
        duration = info.duration
        n_channels = info.channels

        # Brief log of file details

        # Handle case where offset is None (read to the end)
        if offset is None:
            offset = duration

        # Calculate sample positions
        req_start_sample = int(onset * sample_rate)
        req_end_sample = int(offset * sample_rate)
        req_num_samples = req_end_sample - req_start_sample

        # Calculate valid sample range (within file bounds)
        valid_start_sample = max(0, req_start_sample)
        valid_end_sample = min(int(duration * sample_rate), req_end_sample)

        # Check if padding is needed
        needs_padding = valid_start_sample > req_start_sample or valid_end_sample < req_end_sample

        if needs_padding:
            # Handle padding for out-of-bounds requests
            valid_num_samples = valid_end_sample - valid_start_sample

            if valid_num_samples <= 0:
                # Entire request is outside file bounds - return zeros
                segment = np.zeros((req_num_samples, n_channels), dtype=np.float32)

            else:
                # Read valid portion and add padding
                with sf.SoundFile(wav_path) as f:
                    f.seek(valid_start_sample)
                    valid_segment = f.read(valid_num_samples, dtype="float32")

                # Handle mono audio consistently
                if len(valid_segment.shape) == 1:
                    valid_segment = valid_segment.reshape(-1, 1)

                # Create padded segment
                segment = np.zeros((req_num_samples, valid_segment.shape[1]), dtype=np.float32)

                # Insert valid data at the correct position
                insert_pos = max(0, -req_start_sample)
                segment[insert_pos : insert_pos + valid_segment.shape[0]] = valid_segment

        else:
            # No padding needed, just read the segment efficiently
            with sf.SoundFile(wav_path) as f:
                f.seek(valid_start_sample)
                segment = f.read(valid_end_sample - valid_start_sample, dtype="float32")

            # Handle mono audio consistently
            if len(segment.shape) == 1 and segment.size > 0:
                segment = segment.reshape(-1, 1)

        return segment, sample_rate
    except Exception:
        raise
