"""Validation for annotation times, before adding playback window padding."""

import math


def validate_audio_interval(onset, offset, max_duration=None):
    """Raise ValueError when an annotation cannot describe a recording segment."""
    if not math.isfinite(onset) or not math.isfinite(offset):
        raise ValueError("Start and end times must be finite numbers.")
    if onset < 0:
        raise ValueError(f"Start time must not be negative ({onset:.3f}s).")
    if offset <= onset:
        raise ValueError(f"End time must be after start time ({onset:.3f}s to {offset:.3f}s).")
    if max_duration is not None:
        if not math.isfinite(max_duration) or max_duration <= 0:
            raise ValueError("Recording duration must be a positive finite number.")
        if onset >= max_duration or offset > max_duration:
            raise ValueError(
                f"Segment ({onset:.3f}s to {offset:.3f}s) exceeds recording duration ({max_duration:.3f}s)."
            )
