"""
Views for audio file processing and visualization in BattyCoda.
"""
import json

import os
import traceback

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse

import numpy as np
from celery.result import AsyncResult

from ..utils_modules.path_utils import convert_path_to_os_specific

# Removed unused imports
from .utils import appropriate_file, get_audio_bit, normal_hwin, overview_hwin

# Configure logging

@login_required
def handle_spectrogram(request):
    """
    Handle spectrogram generation and serving for bat calls using Celery.

    Required URL parameters:
    - wav_path: Path to the WAV file
    - channel: Audio channel to use
    - call: Call number
    - numcalls: Total number of calls
    - hash: Hash of the audio file for validation
    - overview: Whether to generate overview (0 or 1)
    - contrast: Contrast setting

    Returns:
        Django response with the spectrogram image or task status
    """
    # Log request for debugging

    # Validate required parameters
    required_args = ["wav_path", "channel", "call", "numcalls", "hash", "overview"]
    for arg in required_args:
        if arg not in request.GET:

            return HttpResponse(f"Error: Missing required argument: {arg}", content_type="text/plain", status=400)

    # Extract path and args
    path = request.GET.get("wav_path")
    mod_path = convert_path_to_os_specific(path)
    args_dict = {k: v for k, v in request.GET.items()}

    # Check for async mode (used for client-side error handling)
    async_mode = request.GET.get("async", "false").lower() == "true"

    # Log the request details for debugging

    try:
        # Create unique file paths for caching based on the parameters
        args_for_file = request.GET.copy()
        file_args = {k: v for k, v in args_for_file.items() if k != "wav_path"}

        # Generate file paths
        file_path = appropriate_file(path, file_args)
        alt_file_path = appropriate_file(mod_path, file_args)

        # Check if image already exists
        paths_to_check = [file_path, alt_file_path]
        for check_path in paths_to_check:
            if os.path.exists(check_path) and os.path.getsize(check_path) > 0:

                return FileResponse(open(check_path, "rb"), content_type="image/png")

        # Create directories if needed
        folder_path = os.path.dirname(file_path)
        os.makedirs(folder_path, exist_ok=True)

        # Image doesn't exist, need to generate it

        # Add a flag to indicate this is dynamically generated
        args_dict["generated_on_fly"] = "1"

        # Launch Celery task to generate the image
        from celery import current_app

        task = current_app.send_task(
            "battycoda_app.audio.task_modules.spectrogram_tasks.generate_spectrogram_task",
            args=[path, args_dict, file_path],
        )

        # Always use async mode - simpler approach
        if async_mode:
            response_data = {
                "status": "queued",
                "task_id": task.id,
                "poll_url": reverse("battycoda_app:task_status", kwargs={"task_id": task.id}),
            }
            return JsonResponse(response_data)

        # Wait for task to complete with a timeout of 10 seconds
        # This is a simpler approach - wait longer to get more direct successes
        try:
            result = task.get(timeout=10.0)

            # Check if task succeeded
            if result and result.get("status") == "success":
                # Check both possible file paths
                for check_path in paths_to_check:
                    if os.path.exists(check_path) and os.path.getsize(check_path) > 0:

                        return FileResponse(open(check_path, "rb"), content_type="image/png")

                # Task reported success but file not found
                return HttpResponse(
                    "Error: Image generation succeeded but file was not found.", content_type="text/plain", status=404
                )
            else:
                # Task failed
                error_msg = result.get("error", "Unknown error")

                return HttpResponse(
                    f"Error: Failed to generate image: {error_msg}", content_type="text/plain", status=500
                )

        except Exception as e:
            # If we hit a timeout, return an error message

            return HttpResponse(
                f"Error: Timeout generating image. Try refreshing.", content_type="text/plain", status=504
            )

    except Exception as e:

        return HttpResponse(f"Error: Server error: {str(e)}", content_type="text/plain", status=500)

@login_required
def task_status(request, task_id):
    """
    Check the status of a task.

    Args:
        request: Django request
        task_id: ID of the Celery task

    Returns:
        JSON response with task status
    """

    task_result = AsyncResult(task_id)

    # Log the raw task state for debugging

    # Check for ready but forgotten task
    # Skip forgotten task check
    
    # Simple status responses
    if task_result.state == "PENDING":
        response = {"status": "pending", "message": "Task is pending", "task_id": task_id}
    elif task_result.state == "FAILURE":
        response = {
            "status": "error",
            "message": str(task_result.info) if hasattr(task_result, "info") else "Task failed",
            "task_id": task_id,
        }
    elif task_result.state == "SUCCESS":
        # For successful tasks, create URL for direct image access
        if task_result.info and "status" in task_result.info:
            if task_result.info["status"] == "success":
                # Get file path and args from task result
                file_path = task_result.info.get("file_path")
                original_args = task_result.info.get("args", {})

                if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    # Create URL parameters
                    params = {
                        "wav_path": original_args.get("wav_path", ""),
                        "call": original_args.get("call", "0"),
                        "channel": original_args.get("channel", "0"),
                        "numcalls": original_args.get("numcalls", "1"),
                        "hash": original_args.get("hash", ""),
                        "overview": original_args.get("overview", "0"),
                        "contrast": original_args.get("contrast", "4.0"),
                    }

                    # Build URL for direct image access
                    import urllib.parse

                    query_string = urllib.parse.urlencode(params)
                    spectrogram_url = request.build_absolute_uri(
                        f"{reverse('battycoda_app:spectrogram')}?{query_string}"
                    )

                    response = {
                        "status": "success",
                        "file_path": spectrogram_url,
                        "message": "Task completed successfully",
                    }
                else:
                    # File not found or empty

                    response = {"status": "error", "message": "Task completed but image file not found"}
            else:
                # Task reported error
                response = {"status": "error", "message": task_result.info.get("error", "Unknown error")}
        else:
            # Task completed but no status info
            response = {"status": "success", "message": "Task completed but no image info available"}
    else:
        # Other states (like PROCESSING)
        response = {"status": "processing", "message": f"Task is {task_result.state.lower()}", "task_id": task_id}

    return JsonResponse(response)

@login_required
def handle_audio_snippet(request):
    """
    Handle audio snippet generation and serving for bat calls.

    Required URL parameters:
    - wav_path: Path to the WAV file
    - channel: Audio channel to use
    - call: Call number
    - hash: Hash of the audio file for validation
    - overview: Whether to generate overview (True or False)
    - loudness: Volume level

    Optional parameters:
    - onset: Start time in seconds (if providing direct timing)
    - offset: End time in seconds (if providing direct timing)

    Returns:
        Django response with the audio snippet
    """
    # Validate required parameters
    required_args = ["wav_path", "channel", "call", "hash", "overview", "loudness"]
    for arg in required_args:
        if arg not in request.GET:

            return HttpResponse(f"Missing required parameter: {arg}", status=400)

    # Extract and convert path
    path = request.GET.get("wav_path")

    # Fix duplicate /app/media in paths
    if path.startswith("/app/media"):
        path = path.replace("/app/media/", "/", 1)

    mod_path = convert_path_to_os_specific(path)

    # Log the request details for debugging

    try:
        # Create unique file paths for caching based on the parameters
        args_for_file = request.GET.copy()
        # Remove wav_path from args to avoid duplicating it in the file name
        file_args = {k: v for k, v in args_for_file.items() if k != "wav_path"}

        # Generate file paths for caching
        file_path = appropriate_file(path, file_args)
        alt_file_path = appropriate_file(mod_path, file_args)

        # Check if file already exists
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:

            return FileResponse(open(file_path, "rb"), content_type="audio/wav")
        elif os.path.exists(alt_file_path) and os.path.getsize(alt_file_path) > 0:

            return FileResponse(open(alt_file_path, "rb"), content_type="audio/wav")

        # Create directory if needed for generation
        slowdown = 5

        # Create directories if needed
        folder_path = appropriate_file(mod_path, file_args, folder_only=True)

        os.makedirs(folder_path, exist_ok=True)

        # Process audio
        call_to_do = int(request.GET["call"])
        overview = request.GET["overview"] == "True"
        hwin = overview_hwin if overview else normal_hwin

        # Prepare extra parameters for onset/offset from request
        extra_params = None
        if "onset" in request.GET and "offset" in request.GET:
            extra_params = {"onset": request.GET["onset"], "offset": request.GET["offset"]}

        # Get audio data
        # Check if the path is already in media directory
        if "task_batches" in mod_path and mod_path.startswith("/app/"):
            audio_path = mod_path  # Use the path as is if it starts with /app/
        else:
            # Convert path separators for non-absolute paths
            audio_path = os.sep.join(mod_path.split("/"))

            # For media files, make sure we're using the correct path within the Docker container
            if not os.path.exists(audio_path) and "task_batches" in audio_path:
                audio_path = os.path.join("/app/media", audio_path.lstrip("/"))

        thr_x1, fs, hashof = get_audio_bit(audio_path, call_to_do, hwin(), extra_params)

        # Validate hash - skipping for now 
        # if request.GET["hash"] != hashof:
        #    return HttpResponse("Hash validation failed", status=400)
        
        # Check for valid audio data
        if thr_x1 is None or len(thr_x1) == 0:
            return HttpResponse("Failed to extract audio data", status=500)

        # Extract the specific channel with error handling
        try:
            channel_idx = int(request.GET["channel"])
            if len(thr_x1.shape) > 1 and channel_idx < thr_x1.shape[1]:
                # Multi-channel audio, extract specific channel
                thr_x1 = thr_x1[:, channel_idx]
            else:
                # Single channel or invalid channel index
                thr_x1 = thr_x1 if len(thr_x1.shape) == 1 else thr_x1[:, 0]

            # Ensure audio data is 1D
            if len(thr_x1.shape) > 1:
                thr_x1 = thr_x1.flatten()

            # Get loudness with error handling
            try:
                loudness = float(request.GET["loudness"])
            except (ValueError, TypeError):

                loudness = 1.0

            # Write audio file with error handling
            try:
                # Create destination directory if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Ensure we have a valid sample rate
                sample_rate = fs // slowdown if fs > 0 else abs(fs) // slowdown
                if sample_rate <= 0:
                    sample_rate = 44100 // slowdown

                # Ensure we have valid audio data
                audio_data = thr_x1.astype("float32")

                # Audio data details for debugging

                # Adjust and ensure proper range for audio data
                if np.isnan(audio_data).any() or np.isinf(audio_data).any():

                    audio_data = np.nan_to_num(audio_data)

                # Scale audio data to be between -1 and 1
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val

                # Apply slowdown and loudness adjustment
                audio_data = np.repeat(audio_data, slowdown) * loudness

                # Ensure the data has at least a few samples
                if len(audio_data) < 100:

                    # Check dimensions to create appropriate padding
                    if len(audio_data.shape) > 1:
                        # Multi-channel data
                        padding = np.zeros((1000, audio_data.shape[1]), dtype=np.float32)
                    else:
                        # Single channel data
                        padding = np.zeros(1000, dtype=np.float32)
                    audio_data = np.concatenate([audio_data, padding])

                # Use soundfile for reliable audio writing
                import soundfile as sf

                sf.write(file_path, audio_data, sample_rate)

                # Verify the file was created correctly
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:

                    return HttpResponse("Failed to create audio file", status=500)

            except Exception as e:

                return HttpResponse(f"Error writing audio file: {str(e)}", status=500)

        except Exception as e:

            return HttpResponse(f"Error processing audio: {str(e)}", status=500)

        return FileResponse(open(file_path, "rb"), content_type="audio/wav")

    except Exception as e:

        return HttpResponse(str(e), status=500)
