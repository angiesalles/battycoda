"""
Core audio processing functions for BattyCoda.
"""

import traceback
import hashlib
import os
from django.conf import settings
from django.http import FileResponse

# Configure logging

def deliverAudioBit(file_path, onset, offset, loudness=1.0, pitch_shift=1.0):
    """
    Core function to deliver audio segments with caching and efficient extraction.
    
    Args:
        file_path: Path to the source audio file
        onset: Start time in seconds
        offset: End time in seconds  
        loudness: Volume multiplier (1.0 = original volume)
        pitch_shift: Pitch shift factor (1.0 = original pitch, 0.5 = one octave down, 2.0 = one octave up)
        
    Returns:
        Django FileResponse with the audio segment
    """
    import numpy as np
    
    # Generate cache key from parameters (include pitch_shift)
    cache_key = f"{hashlib.md5(file_path.encode()).hexdigest()}_{onset}_{offset}_{loudness}_{pitch_shift}"
    
    # Create cache directory
    cache_dir = os.path.join(settings.MEDIA_ROOT, "audio_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if cached file exists
    cached_file = os.path.join(cache_dir, f"{cache_key}.wav")
    
    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 0:
        # Return cached file
        return FileResponse(open(cached_file, "rb"), content_type="audio/wav")
    
    # Extract audio segment if not cached
    try:
        # Import here to avoid circular imports
        from ..task_modules.base import extract_audio_segment
        
        # Extract the exact time window requested
        audio_data, sample_rate = extract_audio_segment(file_path, onset, offset)
        
        # Apply pitch shift if different from 1.0
        if pitch_shift != 1.0:
            import librosa
            # Use librosa's pitch shift - preserves duration
            audio_data = librosa.effects.pitch_shift(
                audio_data.flatten(), 
                sr=sample_rate, 
                n_steps=12 * np.log2(pitch_shift)  # Convert ratio to semitones
            )
            
            # Ensure we maintain the original shape (handle stereo if needed)
            if len(audio_data.shape) == 1:
                # Convert back to column format for consistency
                audio_data = audio_data.reshape(-1, 1)
        
        # Apply loudness adjustment
        if loudness != 1.0:
            audio_data = audio_data * loudness
            # Clip to prevent distortion
            audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # Save to cache
        import soundfile as sf
        sf.write(cached_file, audio_data, sample_rate)
        
        # Return the cached file
        return FileResponse(open(cached_file, "rb"), content_type="audio/wav")
        
    except Exception as e:
        # Log error and return 500
        from django.http import HttpResponse
        return HttpResponse(f"Error extracting audio: {str(e)}", status=500)

def normal_hwin(species=None):
    """Returns the window padding as (pre_window, post_window) in milliseconds.

    Args:
        species: Optional Species model instance. If provided, uses species-specific padding.
                If None, uses default padding values.

    Returns:
        tuple: (pre_window, post_window) in milliseconds
    """
    if species is not None:
        return (species.detail_padding_start_ms, species.detail_padding_end_ms)
    return (8, 8)

def overview_hwin(species=None):
    """Returns the window padding as (pre_window, post_window) in milliseconds.

    Args:
        species: Optional Species model instance. If provided, uses species-specific padding.
                If None, uses default padding values.

    Returns:
        tuple: (pre_window, post_window) in milliseconds
    """
    if species is not None:
        return (species.overview_padding_start_ms, species.overview_padding_end_ms)
    return (500, 500)

def get_audio_bit(audio_path, call_number, window_size, extra_params=None):
    """
    Get a specific bit of audio containing a bat call.
    Primary method: Use onset/offset from Task model (passed in extra_params)
    Legacy method: Pull call data from paired pickle file (only used during TaskBatch creation)

    Args:
        audio_path: Path to the WAV file
        call_number: Which call to extract (only used for legacy pickle method)
        window_size: Size of the window around the call in milliseconds (when passed from normal_hwin/overview_hwin)
        extra_params: Dictionary of extra parameters like onset/offset from Task model

    Returns:
        tuple: (audio_data, sample_rate, hash_string)
    """
    try:
        import hashlib
        import os

        import numpy as np

        # Calculate file hash based on path (for consistency across containers)
        file_hash = hashlib.md5(audio_path.encode()).hexdigest()

        # Check if audio file exists - no alternative paths, just fail if not found
        if not os.path.exists(audio_path):

            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # If we have onset/offset data, use extract_audio_segment
        if extra_params and "onset" in extra_params and "offset" in extra_params:
            # Use onset/offset provided in parameters
            onset_time = float(extra_params["onset"])
            offset_time = float(extra_params["offset"])

            # Handle window padding (in seconds)
            pre_padding = window_size[0] / 1000  # convert ms to seconds
            post_padding = window_size[1] / 1000

            # Import the extract_audio_segment function
            from ..task_modules.base import extract_audio_segment

            # Calculate the padded segment boundaries - no need to clamp values
            # as extract_audio_segment will handle out-of-bounds conditions
            start_time = onset_time - pre_padding
            end_time = offset_time + post_padding

            # Use the optimized extract_audio_segment function
            segment, sample_rate = extract_audio_segment(audio_path, start_time, end_time)

            # Handle adding second channel for stereo (if needed)
            if segment.shape[1] == 1:
                segment = np.column_stack((segment, segment))

            # Normalize audio data (only the segment)
            std = np.std(segment)
            if std > 0:
                segment /= std

            return segment, sample_rate, file_hash
        else:
            # Legacy path for cases without onset/offset (should be rare)

            # Import the extract_audio_segment function
            from ..task_modules.base import extract_audio_segment

            # Read the entire file (0 to None means start to end)
            audiodata, sample_rate = extract_audio_segment(audio_path, 0, None)

            # Handle adding second channel for stereo (if needed)
            if audiodata.shape[1] == 1:
                audiodata = np.column_stack((audiodata, audiodata))

            # Normalize audio data
            std = np.std(audiodata)
            if std > 0:
                audiodata /= std

            return audiodata, sample_rate, file_hash
    except Exception as e:

        return None, 0, ""

# Missing imports
import os
