"""
Views for handling batch uploads of recordings.
"""

import os
import tempfile

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..forms import RecordingForm
from ..models.user import UserProfile
from .file_processing import (
    create_recording_from_wav,
    create_segmentation_from_pickle,
    process_wav_with_splitting,
)
from .zip_extraction import extract_pickle_files, extract_wav_files


@login_required
def batch_upload_recordings_view(request):
    """Handle batch upload of recordings with optional pickle segmentation files from ZIP archives."""

    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if not profile.group:
        messages.error(request, "You must be assigned to a group to upload recordings")
        return redirect("battycoda_app:recording_list")

    if request.method == "POST":
        form = RecordingForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            metadata = {
                "species": form.cleaned_data.get("species"),
                "project": form.cleaned_data.get("project"),
                "recorded_date": form.cleaned_data.get("recorded_date"),
                "location": form.cleaned_data.get("location"),
                "equipment": form.cleaned_data.get("equipment"),
                "environmental_conditions": form.cleaned_data.get("environmental_conditions"),
            }

            wav_zip = request.FILES.get("wav_zip")
            pickle_zip = request.FILES.get("pickle_zip")

            if not wav_zip:
                messages.error(request, "Please select a ZIP file with WAV recordings to upload")
                return redirect("battycoda_app:batch_upload_recordings")

            split_long_files = request.POST.get("split_long_files") == "on"
            result = _process_batch_upload(wav_zip, pickle_zip, metadata, request.user, profile, split_long_files)

            _show_result_messages(request, result)
            return redirect("battycoda_app:recording_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = RecordingForm(user=request.user)

    return render(request, "recordings/batch_upload_recordings.html", {"form": form})


def _process_batch_upload(wav_zip, pickle_zip, metadata, user, profile, split_long_files):
    """
    Process the batch upload of WAV and pickle files.

    Returns:
        Dict with counts: success_count, error_count, segmented_count, split_count
    """
    result = {"success_count": 0, "error_count": 0, "segmented_count": 0, "split_count": 0}

    with tempfile.TemporaryDirectory() as wav_temp_dir, tempfile.TemporaryDirectory() as pickle_temp_dir:
        # Extract WAV files
        try:
            wav_files = extract_wav_files(wav_zip, wav_temp_dir)
        except Exception as e:
            return {"error": f"Failed to extract WAV ZIP file: {str(e)}"}

        # Extract pickle files if provided
        pickle_files_dict = {}
        if pickle_zip:
            try:
                pickle_files_dict = extract_pickle_files(pickle_zip, pickle_temp_dir)
            except Exception:
                # Continue with WAV files even if pickle extraction fails
                pass

        # Process each WAV file
        for wav_path in wav_files:
            try:
                _process_single_wav(wav_path, pickle_files_dict, metadata, user, profile, split_long_files, result)
            except Exception:
                result["error_count"] += 1
                import traceback

                traceback.print_exc()

    return result


def _process_single_wav(wav_path, pickle_files_dict, metadata, user, profile, split_long_files, result):
    """Process a single WAV file, optionally splitting and adding segmentation."""
    wav_file_name = os.path.basename(wav_path)

    # Try splitting if enabled
    if split_long_files:
        count, was_split = process_wav_with_splitting(wav_path, metadata, user, profile)
        if was_split:
            result["success_count"] += count
            result["split_count"] += 1
            return

    # Normal processing (file ≤ 60s or splitting disabled/failed)
    recording = create_recording_from_wav(wav_path, metadata, user, profile)

    # Check for matching pickle file
    pickle_filename = f"{wav_file_name}.pickle"
    pickle_path = pickle_files_dict.get(pickle_filename)

    if pickle_path:
        segments_created = create_segmentation_from_pickle(recording, pickle_path, pickle_filename, user)
        if segments_created > 0:
            result["segmented_count"] += 1

    result["success_count"] += 1


def _show_result_messages(request, result):
    """Display appropriate success/error messages based on upload results."""
    if "error" in result:
        messages.error(request, result["error"])
        return

    if result["success_count"] > 0:
        success_msg = f"Successfully uploaded {result['success_count']} recordings"
        if result["split_count"] > 0:
            success_msg += f" ({result['split_count']} files split into 1-minute chunks)"
        if result["segmented_count"] > 0:
            success_msg += f" with {result['segmented_count']} segmented automatically from pickle files"
        messages.success(request, success_msg)

    if result["error_count"] > 0:
        messages.error(request, f"Failed to upload {result['error_count']} recordings. See logs for details.")
