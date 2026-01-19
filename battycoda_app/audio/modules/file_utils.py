"""
Utility functions for file handling and caching in BattyCoda audio processing.
"""

import io
import logging
import os
import pickle
import tempfile

from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Restricted Pickle Unpickler for Security
# =============================================================================

# Allowlist of safe modules and their allowed classes
# This prevents arbitrary code execution from malicious pickle files
PICKLE_SAFE_MODULES = {
    "builtins": {
        "list",
        "dict",
        "tuple",
        "set",
        "frozenset",
        "str",
        "bytes",
        "bytearray",
        "int",
        "float",
        "complex",
        "bool",
        "type",  # Needed for None
        "slice",
        "range",
    },
    "numpy": {
        "ndarray",
        "dtype",
        "array",
        # Scalar types
        "float64",
        "float32",
        "float16",
        "int64",
        "int32",
        "int16",
        "int8",
        "uint64",
        "uint32",
        "uint16",
        "uint8",
        "bool_",
        "complex64",
        "complex128",
        # For dtype reconstruction
        "str_",
        "bytes_",
        "void",
        "object_",
    },
    "numpy.core.multiarray": {
        "_reconstruct",
        "scalar",
    },
    "numpy._core.multiarray": {
        "_reconstruct",
        "scalar",
    },
    "numpy.core.numeric": {
        "*",  # Allow all - needed for array operations
    },
    "numpy._core.numeric": {
        "*",
    },
    "collections": {
        "OrderedDict",
        "defaultdict",
        "deque",
    },
}


class RestrictedUnpickler(pickle.Unpickler):
    """
    A restricted unpickler that only allows loading safe types.

    This prevents arbitrary code execution from malicious pickle files by
    only allowing a predefined set of safe modules and classes.

    Security: This class is designed to prevent pickle-based RCE attacks
    (CWE-502: Deserialization of Untrusted Data).
    """

    def find_class(self, module, name):
        """
        Override find_class to restrict which classes can be instantiated.

        Only classes in the PICKLE_SAFE_MODULES allowlist are permitted.
        """
        # Check if module is in our allowlist
        if module in PICKLE_SAFE_MODULES:
            allowed_names = PICKLE_SAFE_MODULES[module]
            if "*" in allowed_names or name in allowed_names:
                # Module and class are allowed - use standard resolution
                return super().find_class(module, name)

        # Log the blocked attempt for security monitoring
        logger.warning(f"Blocked pickle load attempt: {module}.{name}")

        raise pickle.UnpicklingError(
            f"Restricted unpickler blocked loading '{module}.{name}'. "
            f"Only basic Python types and numpy arrays are allowed."
        )


def safe_pickle_load(file_obj):
    """
    Safely load a pickle file using the restricted unpickler.

    Args:
        file_obj: A file-like object containing pickle data

    Returns:
        The unpickled data

    Raises:
        pickle.UnpicklingError: If the pickle contains disallowed types
        Exception: For other unpickling errors
    """
    return RestrictedUnpickler(file_obj).load()


def safe_pickle_loads(data):
    """
    Safely load pickle data from bytes using the restricted unpickler.

    Args:
        data: Bytes containing pickle data

    Returns:
        The unpickled data

    Raises:
        pickle.UnpicklingError: If the pickle contains disallowed types
        Exception: For other unpickling errors
    """
    return RestrictedUnpickler(io.BytesIO(data)).load()


def appropriate_file(path, args, folder_only=False):
    """
    Generate an appropriate file path for storing processed audio or images.
    This is a cache path generation function to keep processed files organized.

    Args:
        path: Path to the original audio file
        args: Dict of arguments that affect the processing
        folder_only: If True, return only the folder path, not the file path

    Returns:
        str: Path where the processed file should be stored
    """
    # Clean path for cache file
    # Replace '/' with '_' to avoid nested directories beyond a certain point
    if "/" in path:
        parts = path.split("/")
        # Use the last two parts for directory structure to keep it simpler
        dir_path = "_".join(parts[-2:]) if len(parts) > 1 else parts[0]
    else:
        dir_path = path

    # Create a safe directory name (remove problematic characters)
    safe_dir = "".join(c if c.isalnum() or c in "_-." else "_" for c in dir_path)

    # Create a unique filename based on args
    args_string = "_".join([f"{k}={v}" for k, v in sorted(args.items()) if k != "hash"])

    # Set up the cache directory in the media folder
    cache_dir = os.path.join(settings.MEDIA_ROOT, "audio_cache", safe_dir)
    os.makedirs(cache_dir, exist_ok=True)

    if folder_only:
        return cache_dir

    # Add file extension based on args
    if args.get("overview") in ["1", "True", True]:
        ext = ".overview.png" if "contrast" in args else ".overview.wav"
    else:
        ext = ".normal.png" if "contrast" in args else ".normal.wav"

    # Add detail flag if present
    if args.get("detail") == "1":
        ext = ".detail.png"

    # Combine into final path
    filename = f"{args_string}{ext}"

    # Log the cache path for debugging
    logging.debug(f"Cache path for {path}: {os.path.join(cache_dir, filename)}")

    return os.path.join(cache_dir, filename)


def process_pickle_file(pickle_file, max_duration=None):
    """Process a pickle file that contains onset and offset data.

    Args:
        pickle_file: A file-like object containing pickle-serialized data
        max_duration: Optional maximum duration in seconds. If provided, validates that
                     all segments are within recording bounds.

    Returns:
        tuple: (onsets, offsets) as lists of floats

    Raises:
        ValueError: If the pickle file format is not recognized, contains invalid data,
                   or has segments exceeding the recording duration
        Exception: For any other errors during processing
    """
    # Get the filename for error reporting
    filename = getattr(pickle_file, "name", "unknown")

    try:
        import numpy as np

        # Load the pickle file using restricted unpickler for security
        # This prevents arbitrary code execution from malicious pickle files
        pickle_data = safe_pickle_load(pickle_file)

        # Extract onsets and offsets based on data format
        if isinstance(pickle_data, dict):
            onsets = pickle_data.get("onsets", [])
            offsets = pickle_data.get("offsets", [])
        elif isinstance(pickle_data, list) and len(pickle_data) >= 2:
            # Assume first item is onsets, second is offsets
            onsets = pickle_data[0]
            offsets = pickle_data[1]
        elif isinstance(pickle_data, tuple) and len(pickle_data) >= 2:
            # Assume first item is onsets, second is offsets
            onsets = pickle_data[0]
            offsets = pickle_data[1]
        else:
            # Unrecognized format
            raise ValueError(
                f"Pickle file '{os.path.basename(filename)}' format not recognized. Expected a dictionary with 'onsets' and 'offsets' keys, or a list/tuple with at least 2 elements."
            )

        # Convert to lists if they're NumPy arrays or other iterables
        if isinstance(onsets, np.ndarray):
            onsets = onsets.tolist()
        elif not isinstance(onsets, list):
            onsets = list(onsets)

        if isinstance(offsets, np.ndarray):
            offsets = offsets.tolist()
        elif not isinstance(offsets, list):
            offsets = list(offsets)

        # Validate data
        if len(onsets) == 0 or len(offsets) == 0:
            raise ValueError(
                f"Pickle file '{os.path.basename(filename)}' does not contain required onset and offset lists."
            )

        # Check if lists are the same length
        if len(onsets) != len(offsets):
            raise ValueError(
                f"In pickle file '{os.path.basename(filename)}': Onsets and offsets lists must have the same length."
            )

        # Convert numpy types to Python native types if needed
        onsets = [float(onset) for onset in onsets]
        offsets = [float(offset) for offset in offsets]

        # Validate segments against recording duration if provided
        if max_duration is not None:
            for i, (onset, offset) in enumerate(zip(onsets, offsets)):
                # Check if onset is valid
                if onset < 0:
                    raise ValueError(
                        f"Pickle file '{os.path.basename(filename)}': Segment {i + 1} has negative onset ({onset:.3f}s)"
                    )

                # Check if segment exceeds recording duration
                if onset >= max_duration:
                    raise ValueError(
                        f"Pickle file '{os.path.basename(filename)}': Segment {i + 1} onset ({onset:.3f}s) exceeds recording duration ({max_duration:.3f}s)"
                    )

                if offset > max_duration:
                    raise ValueError(
                        f"Pickle file '{os.path.basename(filename)}': Segment {i + 1} offset ({offset:.3f}s) exceeds recording duration ({max_duration:.3f}s)"
                    )

                # Check if onset < offset
                if onset >= offset:
                    raise ValueError(
                        f"Pickle file '{os.path.basename(filename)}': Segment {i + 1} has invalid onset >= offset ({onset:.3f}s >= {offset:.3f}s)"
                    )

        return onsets, offsets

    except Exception as e:
        # Create a more informative error message that includes the filename
        if isinstance(e, ValueError):
            # Re-raise with the existing message that already includes the filename
            raise
        else:
            # Wrap other exceptions with filename information
            import traceback

            logging.error(
                f"Error processing pickle file '{os.path.basename(filename)}': {str(e)}\n{traceback.format_exc()}"
            )
            raise Exception(f"Error processing pickle file '{os.path.basename(filename)}': {str(e)}") from e


def get_audio_duration(audio_file_path):
    """
    Get the duration of an audio file in seconds.

    Args:
        audio_file_path: Path to the audio file

    Returns:
        float: Duration in seconds

    Raises:
        Exception: If the file cannot be read
    """
    import soundfile as sf

    try:
        info = sf.info(audio_file_path)
        return info.duration
    except Exception as e:
        raise Exception(f"Error getting audio duration: {str(e)}") from e


def split_audio_file(audio_file_path, chunk_duration_seconds=60):
    """
    Split an audio file into chunks of specified duration.

    Args:
        audio_file_path: Path to the audio file to split
        chunk_duration_seconds: Duration of each chunk in seconds (default: 60)

    Returns:
        list: List of paths to the chunk files (temporary files that should be cleaned up by caller)

    Raises:
        Exception: If the file cannot be split
    """
    import numpy as np
    import soundfile as sf

    try:
        # Read the audio file
        data, samplerate = sf.read(audio_file_path)

        # Calculate total duration and number of chunks needed
        total_duration = len(data) / samplerate
        num_chunks = int(np.ceil(total_duration / chunk_duration_seconds))

        # Calculate samples per chunk
        samples_per_chunk = int(chunk_duration_seconds * samplerate)

        # Create temporary directory for chunks
        temp_dir = tempfile.mkdtemp()
        chunk_paths = []

        # Get the original filename for naming chunks
        original_name = os.path.splitext(os.path.basename(audio_file_path))[0]

        # Split into chunks
        for i in range(num_chunks):
            start_sample = i * samples_per_chunk
            end_sample = min((i + 1) * samples_per_chunk, len(data))

            # Extract chunk data
            if len(data.shape) > 1:
                # Multi-channel audio
                chunk_data = data[start_sample:end_sample, :]
            else:
                # Mono audio
                chunk_data = data[start_sample:end_sample]

            # Create chunk filename
            chunk_filename = f"{original_name}_chunk_{i + 1:03d}.wav"
            chunk_path = os.path.join(temp_dir, chunk_filename)

            # Write chunk to file
            sf.write(chunk_path, chunk_data, samplerate)
            chunk_paths.append(chunk_path)

            logging.info(f"Created chunk {i + 1}/{num_chunks}: {chunk_filename} ({len(chunk_data) / samplerate:.2f}s)")

        return chunk_paths

    except Exception as e:
        logging.error(f"Error splitting audio file: {str(e)}")
        raise Exception(f"Error splitting audio file: {str(e)}") from e
