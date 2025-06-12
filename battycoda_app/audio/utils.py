"""
Utility functions for audio processing in BattyCoda.

This module re-exports functions from the specialized audio modules
to maintain backward compatibility with existing code.
"""

# Configure logging

import wave
from pathlib import Path

import soundfile as sf

from .modules.audio_processing import get_audio_bit, normal_hwin, overview_hwin

# Re-export functions from specialized modules
from .modules.file_utils import appropriate_file, process_pickle_file
from .modules.visualization import auto_segment_audio, energy_based_segment_audio, get_spectrogram_ticks

# Export all functions with their original names
__all__ = [
    "appropriate_file",
    "process_pickle_file",
    "get_audio_bit",
    "normal_hwin",
    "overview_hwin",
    "get_spectrogram_ticks",
    "auto_segment_audio",
    "energy_based_segment_audio",
]


def probe_audio(p) -> tuple[int, float]:
    """
    Return (sample_rate, duration_seconds) for audio file…
    Accepts str, Path, or file-like.
    """
    p = Path(p)  # normalise once
    path_str = str(p)  # wave/soundfile want a plain string

    # Fast-path for WAV
    if p.suffix.lower() == ".wav":
        with wave.open(path_str, "rb") as w:
            sr = w.getframerate()
            dur = w.getnframes() / sr
            return sr, dur

    # Fallback for everything libsndfile can handle
    with sf.SoundFile(path_str) as f:
        return f.samplerate, len(f) / f.samplerate
