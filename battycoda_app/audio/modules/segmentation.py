"""
Functions for audio segmentation and event detection in BattyCoda.
"""

import traceback

# Configure logging

def apply_bandpass_filter(audio_data, sample_rate, low_freq=None, high_freq=None):
    """
    Apply bandpass filter to audio data.
    
    Args:
        audio_data: Audio signal array
        sample_rate: Sample rate in Hz
        low_freq: High-pass filter frequency in Hz (optional)
        high_freq: Low-pass filter frequency in Hz (optional)
    
    Returns:
        Filtered audio data
    """
    if low_freq is None and high_freq is None:
        return audio_data
    
    from scipy import signal
    
    # Ensure we have valid frequency bounds
    nyquist_freq = sample_rate / 2
    if low_freq is not None:
        low_freq = min(low_freq, nyquist_freq - 1)
    if high_freq is not None:
        high_freq = min(high_freq, nyquist_freq - 1)
    
    # Apply appropriate filter
    if low_freq is not None and high_freq is not None:
        # Bandpass filter
        if low_freq < high_freq:
            sos = signal.butter(4, [low_freq, high_freq], btype='band', fs=sample_rate, output='sos')
            return signal.sosfilt(sos, audio_data)
    elif low_freq is not None:
        # High-pass filter only
        sos = signal.butter(4, low_freq, btype='high', fs=sample_rate, output='sos')
        return signal.sosfilt(sos, audio_data)
    elif high_freq is not None:
        # Low-pass filter only
        sos = signal.butter(4, high_freq, btype='low', fs=sample_rate, output='sos')
        return signal.sosfilt(sos, audio_data)
    
    return audio_data

def auto_segment_audio(
    audio_path, min_duration_ms=10, smooth_window=3, threshold_factor=0.5, low_freq=None, high_freq=None
):
    """
    Automatically segment audio using the following steps:
    1. Take absolute value of the signal
    2. Smooth the signal using a moving average filter
    3. Apply a threshold to detect segments
    4. Reject markings shorter than the minimum duration

    Args:
        audio_path: Path to the audio file
        min_duration_ms: Minimum segment duration in milliseconds
        smooth_window: Window size for smoothing filter
        threshold_factor: Threshold factor (between 0-1) to apply
        low_freq: High-pass filter frequency in Hz (optional)
        high_freq: Low-pass filter frequency in Hz (optional)

    Returns:
        tuple: (onsets, offsets) as lists of floats in seconds
    """
    import os

    import numpy as np
    import soundfile as sf


    # Load the audio file
    audio_data, sample_rate = sf.read(audio_path)

    # For stereo files, use the first channel for detection
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        audio_data = audio_data[:, 0]
    
    # Apply bandpass filter if specified
    audio_data = apply_bandpass_filter(audio_data, sample_rate, low_freq, high_freq)

    # Step 1: Take absolute value of the signal
    abs_signal = np.abs(audio_data)

    # Step 2: Smooth the signal with a moving average filter
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        smoothed_signal = np.convolve(abs_signal, kernel, mode="same")
    else:
        smoothed_signal = abs_signal

    # Step 3: Apply threshold
    # Calculate adaptive threshold based on the signal statistics
    signal_mean = np.mean(smoothed_signal)
    signal_std = np.std(smoothed_signal)
    threshold = signal_mean + (threshold_factor * signal_std)
    # Auto-segmentation thresholds - Mean: {signal_mean:.6f}, Std: {signal_std:.6f}, Threshold: {threshold:.6f}

    # Create binary mask where signal exceeds threshold
    binary_mask = smoothed_signal > threshold

    # Find transitions in the binary mask (0->1 and 1->0)
    # Transitions from 0->1 indicate segment onsets
    # Transitions from 1->0 indicate segment offsets
    transitions = np.diff(binary_mask.astype(int))
    onset_samples = np.where(transitions == 1)[0] + 1  # +1 because diff reduces length by 1
    offset_samples = np.where(transitions == -1)[0] + 1

    # Handle edge cases
    if binary_mask[0]:
        # Signal starts above threshold, insert onset at sample 0
        onset_samples = np.insert(onset_samples, 0, 0)

    if binary_mask[-1]:
        # Signal ends above threshold, append offset at the last sample
        offset_samples = np.append(offset_samples, len(binary_mask) - 1)

    # Ensure we have the same number of onsets and offsets
    if len(onset_samples) > len(offset_samples):
        # More onsets than offsets - trim extra onsets
        onset_samples = onset_samples[: len(offset_samples)]
    elif len(offset_samples) > len(onset_samples):
        # More offsets than onsets - trim extra offsets
        offset_samples = offset_samples[: len(onset_samples)]

    # Convert sample indices to time in seconds
    onsets = onset_samples / sample_rate
    offsets = offset_samples / sample_rate

    # Step 4: Reject segments shorter than the minimum duration
    min_samples = int((min_duration_ms / 1000) * sample_rate)
    valid_segments = []

    for i in range(len(onsets)):
        duration_samples = offset_samples[i] - onset_samples[i]
        if duration_samples >= min_samples:
            valid_segments.append(i)

    # Filter onsets and offsets to only include valid segments
    filtered_onsets = [onsets[i] for i in valid_segments]
    filtered_offsets = [offsets[i] for i in valid_segments]

    return filtered_onsets, filtered_offsets

def energy_based_segment_audio(
    audio_path, min_duration_ms=10, smooth_window=3, threshold_factor=0.5, low_freq=None, high_freq=None
):
    """
    Segment audio based on energy levels using the following steps:
    1. Calculate the short-time energy of the signal
    2. Smooth the energy curve
    3. Apply an adaptive threshold based on the energy statistics
    4. Reject markings shorter than the minimum duration

    Args:
        audio_path: Path to the audio file
        min_duration_ms: Minimum segment duration in milliseconds
        smooth_window: Window size for smoothing filter
        threshold_factor: Threshold factor (between 0-1) to apply to energy detection
        low_freq: High-pass filter frequency in Hz (optional)
        high_freq: Low-pass filter frequency in Hz (optional)

    Returns:
        tuple: (onsets, offsets) as lists of floats in seconds
    """
    import os

    import numpy as np
    import soundfile as sf


    # Load the audio file
    audio_data, sample_rate = sf.read(audio_path)

    # For stereo files, use the first channel for detection
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        audio_data = audio_data[:, 0]
    
    # Apply bandpass filter if specified
    audio_data = apply_bandpass_filter(audio_data, sample_rate, low_freq, high_freq)

    # Step 1: Calculate short-time energy
    # Set the frame size for energy calculation (adjust based on expected call frequency)
    frame_size = int(0.0004 * sample_rate)  # 0.4ms frames for precise onset detection
    energy = np.zeros(len(audio_data) // frame_size)

    for i in range(len(energy)):
        # Calculate energy for each frame
        start = i * frame_size
        end = min(start + frame_size, len(audio_data))
        frame = audio_data[start:end]
        # Energy is sum of squared amplitudes
        energy[i] = np.sum(frame**2) / len(frame)

    # Interpolate energy back to signal length for easier visualization
    energy_full = np.interp(np.linspace(0, len(energy), len(audio_data)), np.arange(len(energy)), energy)

    # Step 2: Smooth the energy curve with a moving average filter
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        smoothed_energy = np.convolve(energy_full, kernel, mode="same")
    else:
        smoothed_energy = energy_full

    # Step 3: Apply threshold
    # Calculate adaptive threshold based on the energy statistics
    energy_mean = np.mean(smoothed_energy)
    energy_std = np.std(smoothed_energy)
    threshold = energy_mean + (threshold_factor * energy_std)
    # Energy segmentation thresholds - Mean: {energy_mean:.6f}, Std: {energy_std:.6f}, Threshold: {threshold:.6f}

    # Create binary mask where energy exceeds threshold
    binary_mask = smoothed_energy > threshold

    # Find transitions in the binary mask (0->1 and 1->0)
    transitions = np.diff(binary_mask.astype(int))
    onset_samples = np.where(transitions == 1)[0] + 1  # +1 because diff reduces length by 1
    offset_samples = np.where(transitions == -1)[0] + 1

    # Handle edge cases
    if binary_mask[0]:
        # Signal starts above threshold, insert onset at sample 0
        onset_samples = np.insert(onset_samples, 0, 0)

    if binary_mask[-1]:
        # Signal ends above threshold, append offset at the last sample
        offset_samples = np.append(offset_samples, len(binary_mask) - 1)

    # Ensure we have the same number of onsets and offsets
    if len(onset_samples) > len(offset_samples):
        # More onsets than offsets - trim extra onsets
        onset_samples = onset_samples[: len(offset_samples)]
    elif len(offset_samples) > len(onset_samples):
        # More offsets than onsets - trim extra offsets
        offset_samples = offset_samples[: len(onset_samples)]

    # Convert sample indices to time in seconds
    onsets = onset_samples / sample_rate
    offsets = offset_samples / sample_rate

    # Step 4: Reject segments shorter than the minimum duration
    min_samples = int((min_duration_ms / 1000) * sample_rate)
    valid_segments = []

    for i in range(len(onsets)):
        duration_samples = offset_samples[i] - onset_samples[i]
        if duration_samples >= min_samples:
            valid_segments.append(i)

    # Filter onsets and offsets to only include valid segments
    filtered_onsets = [onsets[i] for i in valid_segments]
    filtered_offsets = [offsets[i] for i in valid_segments]

    return filtered_onsets, filtered_offsets
