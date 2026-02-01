"""
Functions for generating tick marks for spectrograms in BattyCoda.

Uses matplotlib's MaxNLocator for intelligent tick placement - a well-tested
algorithm that chooses "nice" tick values automatically.
"""

from matplotlib.ticker import MaxNLocator


def get_nice_ticks(min_val, max_val, num_ticks=5):
    """Generate nice tick values for a given range using matplotlib's algorithm.

    Args:
        min_val: Minimum value of the range
        max_val: Maximum value of the range
        num_ticks: Approximate number of ticks desired (default 5)

    Returns:
        list: List of tick values at "nice" positions
    """
    locator = MaxNLocator(nbins=num_ticks, steps=[1, 2, 2.5, 5, 10])
    ticks = locator.tick_values(min_val, max_val)
    # Filter to only include ticks within the range
    return [t for t in ticks if min_val <= t <= max_val]


def format_time(ms_value):
    """Format a time value, using seconds if >= 100ms, otherwise milliseconds.

    Args:
        ms_value: Time value in milliseconds (can be negative)

    Returns:
        str: Formatted time string with appropriate unit
    """
    abs_val = abs(ms_value)
    if abs_val >= 100:
        # Show in seconds with one decimal place
        seconds = ms_value / 1000
        return f"{seconds:.1f}s"
    else:
        # Show in milliseconds with one decimal place
        return f"{ms_value:.1f}ms"


def get_spectrogram_ticks(task, sample_rate=None, normal_window_size=None, overview_window_size=None):
    """Generate tick mark data for spectrograms.

    Args:
        task: Task model instance containing onset and offset
        sample_rate: Sample rate of the recording in Hz (optional)
        normal_window_size: Tuple of (pre_window, post_window) in milliseconds for detail view
        overview_window_size: Tuple of (pre_window, post_window) in milliseconds for overview

    Returns:
        dict: Dictionary containing x and y tick data for both detail and overview views
    """
    # Import here to avoid circular imports
    from .audio_processing import normal_hwin, overview_hwin

    # Use default window sizes if not provided
    if normal_window_size is None:
        normal_window_size = normal_hwin(task.species)
    if overview_window_size is None:
        overview_window_size = overview_hwin(task.species)

    # Calculate call duration in milliseconds
    call_duration_ms = (task.offset - task.onset) * 1000

    # Calculate the actual time spans for detail view (in ms)
    detail_left_padding = normal_window_size[0]  # Pre-window in ms
    detail_right_padding = normal_window_size[1]  # Post-window in ms
    detail_total_duration = detail_left_padding + call_duration_ms + detail_right_padding  # Total window duration in ms

    # Calculate detail view x-axis positions (percentages) based on actual time values
    detail_left_pos = 0  # Left edge
    detail_zero_pos = (detail_left_padding / detail_total_duration) * 100  # Start of sound
    detail_call_end_pos = ((detail_left_padding + call_duration_ms) / detail_total_duration) * 100  # End of sound
    detail_right_pos = 100  # Right edge

    # Calculate the actual time spans for overview (in ms)
    overview_left_padding = overview_window_size[0]  # Pre-window in ms
    overview_right_padding = overview_window_size[1]  # Post-window in ms
    overview_total_duration = overview_left_padding + overview_right_padding  # Total window duration in ms

    # Calculate overview x-axis positions (percentages) based on actual time values
    overview_left_pos = 0  # Left edge
    overview_zero_pos = (overview_left_padding / overview_total_duration) * 100  # Start of sound
    overview_right_pos = 100  # Right edge
    overview_call_end_pos = ((overview_left_padding + call_duration_ms) / overview_total_duration) * 100
    # Generate x-axis ticks data for detail view using matplotlib's nice tick algorithm
    # Time range: from -left_padding to (call_duration + right_padding)
    detail_min_time = -detail_left_padding
    detail_max_time = call_duration_ms + detail_right_padding

    # Get nice tick values for the time range (aim for ~6 ticks)
    nice_ticks_ms = get_nice_ticks(detail_min_time, detail_max_time, num_ticks=6)

    # Always include 0 (onset) if not already present
    if 0 not in nice_ticks_ms:
        nice_ticks_ms.append(0)
        nice_ticks_ms.sort()

    # Build tick list
    x_ticks_detail = []
    for i, time_ms in enumerate(nice_ticks_ms):
        # Calculate position as percentage of total duration
        position = ((time_ms + detail_left_padding) / detail_total_duration) * 100

        # Format the label
        if time_ms == 0:
            label = "0"
            tick_id = "zero-tick-detail"
        else:
            label = format_time(time_ms)
            tick_id = f"tick-detail-{i}"

        x_ticks_detail.append({"id": tick_id, "position": position, "value": label, "type": "major"})

    # Generate x-axis ticks data for overview using matplotlib's nice tick algorithm
    # Time range: from -left_padding to right_padding
    overview_min_time = -overview_left_padding
    overview_max_time = overview_right_padding

    # Get nice tick values for the overview range (aim for ~6 ticks)
    nice_ticks_overview_ms = get_nice_ticks(overview_min_time, overview_max_time, num_ticks=6)

    # Always include 0 (onset) if not already present
    if 0 not in nice_ticks_overview_ms:
        nice_ticks_overview_ms.append(0)
        nice_ticks_overview_ms.sort()

    # Build tick list for overview
    x_ticks_overview = []
    for i, time_ms in enumerate(nice_ticks_overview_ms):
        # Calculate position as percentage of total duration
        position = ((time_ms + overview_left_padding) / overview_total_duration) * 100

        # Format the label
        if time_ms == 0:
            label = "0"
            tick_id = "zero-tick-overview"
        else:
            label = format_time(time_ms)
            tick_id = f"tick-overview-{i}"

        x_ticks_overview.append({"id": tick_id, "position": position, "value": label, "type": "major"})

    # Generate y-axis ticks for frequency
    if not sample_rate:
        raise ValueError("Sample rate is required for spectrogram ticks")

    # Nyquist frequency (maximum possible frequency in the recording) is half the sample rate
    max_freq = sample_rate / 2 / 1000  # Convert to kHz

    # Increase the number of ticks for more granularity
    num_ticks = 11  # 0%, 10%, 20%, ..., 100%
    y_ticks = []

    # Generate main ticks
    for i in range(num_ticks):
        position = i * (100 / (num_ticks - 1))  # Positions from 0% to 100%
        value = max_freq - (max_freq * position / 100)  # Values from max_freq to 0 kHz

        # Add the tick with a size class for styling
        y_ticks.append(
            {
                "position": position,
                "value": int(value),  # Integer values for cleaner display
                "type": "major",  # Mark as major tick for styling
            }
        )

    # Add intermediate minor ticks between major ticks for extra precision
    if num_ticks > 2:  # Only add minor ticks if we have enough space
        for i in range(num_ticks - 1):
            # Calculate position halfway between major ticks
            position = (i * (100 / (num_ticks - 1))) + ((100 / (num_ticks - 1)) / 2)
            value = max_freq - (max_freq * position / 100)

            # Add minor tick (without displaying the value)
            y_ticks.append(
                {
                    "position": position,
                    "value": "",  # No value displayed for minor ticks
                    "type": "minor",  # Mark as minor tick for styling
                }
            )

    return {"x_ticks_detail": x_ticks_detail, "x_ticks_overview": x_ticks_overview, "y_ticks": y_ticks}
