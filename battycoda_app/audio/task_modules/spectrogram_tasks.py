"""
Backward compatibility shim for spectrogram tasks.

This module provides backward compatibility by importing tasks from the new
spectrogram package structure.
"""
from .spectrogram import (generate_recording_spectrogram,
                          generate_spectrogram, generate_spectrogram_from_audio,
                          generate_spectrogram_task,
                          make_spectrogram, prefetch_spectrograms)

__all__ = [
    'make_spectrogram',
    'generate_spectrogram_task',
    'prefetch_spectrograms',
    'generate_recording_spectrogram',
    'generate_spectrogram',
    'generate_spectrogram_from_audio',
]
