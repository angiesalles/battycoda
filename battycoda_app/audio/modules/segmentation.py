"""
Functions for audio segmentation and event detection in BattyCoda.
"""

import numpy as np
import soundfile as sf
from scipy import signal


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
            sos = signal.butter(4, [low_freq, high_freq], btype="band", fs=sample_rate, output="sos")
            return signal.sosfilt(sos, audio_data)
    elif low_freq is not None:
        # High-pass filter only
        sos = signal.butter(4, low_freq, btype="high", fs=sample_rate, output="sos")
        return signal.sosfilt(sos, audio_data)
    elif high_freq is not None:
        # Low-pass filter only
        sos = signal.butter(4, high_freq, btype="low", fs=sample_rate, output="sos")
        return signal.sosfilt(sos, audio_data)

    return audio_data


def _load_and_filter_audio(audio_path, low_freq=None, high_freq=None):
    """
    Load audio file, convert to mono if needed, and apply bandpass filter.

    Args:
        audio_path: Path to the audio file
        low_freq: High-pass filter frequency in Hz (optional)
        high_freq: Low-pass filter frequency in Hz (optional)

    Returns:
        tuple: (filtered_audio_data, sample_rate)
    """
    audio_data, sample_rate = sf.read(audio_path)

    # For stereo files, use the first channel
    if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
        audio_data = audio_data[:, 0]

    # Apply bandpass filter if specified
    audio_data = apply_bandpass_filter(audio_data, sample_rate, low_freq, high_freq)

    return audio_data, sample_rate


def _find_segments_from_mask(binary_mask, sample_rate, min_duration_ms):
    """
    Find segment onsets/offsets from a binary mask and filter short segments.

    Args:
        binary_mask: Boolean array where True indicates signal above threshold
        sample_rate: Sample rate in Hz
        min_duration_ms: Minimum segment duration in milliseconds

    Returns:
        tuple: (onsets, offsets) as lists of floats in seconds
    """
    # Guard against empty input
    if len(binary_mask) == 0:
        return [], []

    # Find transitions in the binary mask (0->1 and 1->0)
    transitions = np.diff(binary_mask.astype(int))
    onset_samples = np.where(transitions == 1)[0] + 1
    offset_samples = np.where(transitions == -1)[0] + 1

    # Handle edge cases
    if binary_mask[0]:
        onset_samples = np.insert(onset_samples, 0, 0)
    if binary_mask[-1]:
        offset_samples = np.append(offset_samples, len(binary_mask) - 1)

    # Ensure we have the same number of onsets and offsets
    min_len = min(len(onset_samples), len(offset_samples))
    onset_samples = onset_samples[:min_len]
    offset_samples = offset_samples[:min_len]

    # Filter segments shorter than minimum duration
    min_samples = int((min_duration_ms / 1000) * sample_rate)
    valid = (offset_samples - onset_samples) >= min_samples

    onsets = (onset_samples[valid] / sample_rate).tolist()
    offsets = (offset_samples[valid] / sample_rate).tolist()

    return onsets, offsets


def auto_segment_audio(
    audio_path, min_duration_ms=10, smooth_window=3, threshold_factor=0.5, low_freq=None, high_freq=None
):
    """
    Automatically segment audio using amplitude threshold detection.

    Steps:
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
    audio_data, sample_rate = _load_and_filter_audio(audio_path, low_freq, high_freq)

    # Take absolute value of the signal
    abs_signal = np.abs(audio_data)

    # Smooth with moving average filter
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        smoothed_signal = np.convolve(abs_signal, kernel, mode="same")
    else:
        smoothed_signal = abs_signal

    # Apply adaptive threshold
    signal_mean = np.mean(smoothed_signal)
    signal_std = np.std(smoothed_signal)
    threshold = signal_mean + (threshold_factor * signal_std)

    binary_mask = smoothed_signal > threshold
    return _find_segments_from_mask(binary_mask, sample_rate, min_duration_ms)


def energy_based_segment_audio(
    audio_path, min_duration_ms=10, smooth_window=3, threshold_factor=0.5, low_freq=None, high_freq=None
):
    """
    Segment audio based on short-time energy levels.

    Steps:
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
    audio_data, sample_rate = _load_and_filter_audio(audio_path, low_freq, high_freq)

    # Calculate short-time energy (0.4ms frames for precise onset detection)
    frame_size = int(0.0004 * sample_rate)
    num_frames = len(audio_data) // frame_size
    energy = np.zeros(num_frames)

    for i in range(num_frames):
        start = i * frame_size
        end = min(start + frame_size, len(audio_data))
        frame = audio_data[start:end]
        energy[i] = np.sum(frame**2) / len(frame)

    # Interpolate energy back to signal length
    energy_full = np.interp(np.linspace(0, len(energy), len(audio_data)), np.arange(len(energy)), energy)

    # Smooth the energy curve
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        smoothed_energy = np.convolve(energy_full, kernel, mode="same")
    else:
        smoothed_energy = energy_full

    # Apply adaptive threshold
    energy_mean = np.mean(smoothed_energy)
    energy_std = np.std(smoothed_energy)
    threshold = energy_mean + (threshold_factor * energy_std)

    binary_mask = smoothed_energy > threshold
    return _find_segments_from_mask(binary_mask, sample_rate, min_duration_ms)
