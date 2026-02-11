"""
Validation utilities for request parameter handling.
"""


def get_int_param(request, param_name, default=None, min_val=None, max_val=None):
    """
    Safely get an integer query parameter from a request.

    Args:
        request: Django request object
        param_name: Name of the GET parameter
        default: Default value if param is missing or invalid
        min_val: Minimum allowed value (clamp if lower)
        max_val: Maximum allowed value (clamp if higher)

    Returns:
        The integer value, clamped to min/max if specified, or default if invalid.
    """
    value = request.GET.get(param_name)
    if value is None:
        return default
    try:
        result = int(value)
        if min_val is not None and result < min_val:
            result = min_val
        if max_val is not None and result > max_val:
            result = max_val
        return result
    except (ValueError, TypeError):
        return default


def safe_int(value, default=None):
    """
    Safely convert a value to an integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        The integer value, or default if conversion fails.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=None):
    """
    Safely convert a value to a float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        The float value, or default if conversion fails.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
