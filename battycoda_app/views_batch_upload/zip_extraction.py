"""
Utilities for extracting files from ZIP archives during batch upload.
"""

import os
import zipfile


def extract_wav_files(wav_zip, temp_dir):
    """
    Extract WAV files from a ZIP archive.

    Args:
        wav_zip: The uploaded ZIP file containing WAV files
        temp_dir: Temporary directory to extract files to

    Returns:
        List of paths to extracted WAV files

    Raises:
        Exception: If ZIP extraction fails
    """
    wav_files = []
    processed_files = set()

    with zipfile.ZipFile(wav_zip, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            # Skip directories, already processed files, and macOS metadata files
            if (
                file_info.filename.endswith("/")
                or file_info.filename in processed_files
                or os.path.basename(file_info.filename).startswith("._")
            ):
                continue

            if file_info.filename.lower().endswith(".wav"):
                zip_ref.extract(file_info, temp_dir)
                extracted_path = os.path.join(temp_dir, file_info.filename)
                wav_files.append(extracted_path)
                processed_files.add(file_info.filename)

    return wav_files


def extract_pickle_files(pickle_zip, temp_dir):
    """
    Extract pickle files from a ZIP archive.

    Args:
        pickle_zip: The uploaded ZIP file containing pickle files
        temp_dir: Temporary directory to extract files to

    Returns:
        Dictionary mapping pickle basenames to their extracted paths

    Raises:
        Exception: If ZIP extraction fails
    """
    pickle_files_dict = {}
    processed_files = set()

    with zipfile.ZipFile(pickle_zip, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            # Skip directories, already processed files, and macOS metadata files
            if (
                file_info.filename.endswith("/")
                or file_info.filename in processed_files
                or os.path.basename(file_info.filename).startswith("._")
            ):
                continue

            if file_info.filename.lower().endswith(".pickle"):
                zip_ref.extract(file_info, temp_dir)
                pickle_path = os.path.join(temp_dir, file_info.filename)
                # Store with basename as key for matching
                pickle_files_dict[os.path.basename(file_info.filename)] = pickle_path
                processed_files.add(file_info.filename)

    return pickle_files_dict
