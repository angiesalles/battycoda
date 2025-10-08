"""
Backward compatibility shim for spectrogram tasks.

This module provides backward compatibility by importing tasks from the new
spectrogram package structure.
"""
from .spectrogram import generate_hdf5_spectrogram, generate_recording_spectrogram

__all__ = [
    'generate_recording_spectrogram',
    'generate_hdf5_spectrogram',
]
