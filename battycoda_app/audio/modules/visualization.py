"""
Visualization and spectrogram generation functions for BattyCoda.

This module re-exports functions from specialized visualization modules
to maintain backward compatibility for imports.
"""

# Configure logging

from .segmentation import auto_segment_audio, energy_based_segment_audio

# Re-export functions from specialized modules
from .tick_generation import get_spectrogram_ticks

__all__ = [
    "get_spectrogram_ticks",
    "auto_segment_audio",
    "energy_based_segment_audio",
]
