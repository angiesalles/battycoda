"""
Views for previewing segmentation results on audio recordings.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models.recording import Recording, SegmentationAlgorithm


@login_required
def preview_segmentation_view(request, recording_id):
    """Preview segmentation on a 10-second stretch of audio"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST requests allowed"}, status=405)

    try:
        # Get parameters from request
        algorithm_id = request.POST.get("algorithm")
        min_duration_ms = int(request.POST.get("min_duration_ms", 10))
        smooth_window = int(request.POST.get("smooth_window", 3))
        threshold_factor = float(request.POST.get("threshold_factor", 0.5))
        start_time = float(request.POST.get("start_time", 0))  # Default to beginning

        # Validate parameters
        if min_duration_ms < 1:
            raise ValueError("Minimum duration must be at least 1ms")
        if smooth_window < 1:
            raise ValueError("Smooth window must be at least 1 sample")
        if threshold_factor <= 0 or threshold_factor > 10:
            raise ValueError("Threshold factor must be between 0 and 10")
        if start_time < 0:
            raise ValueError("Start time must be non-negative")

        # Get algorithm
        algorithm = get_object_or_404(SegmentationAlgorithm, id=int(algorithm_id), is_active=True)

        # Check algorithm access permission
        if algorithm.group and (not profile.group or algorithm.group != profile.group):
            return JsonResponse({"success": False, "error": "You don't have permission to use this algorithm"}, status=403)

        # Import the segmentation functions
        from battycoda_app.audio.modules.segmentation import auto_segment_audio, energy_based_segment_audio
        import librosa
        import numpy as np

        # Load the audio file for the preview window
        audio_path = recording.wav_file.path
        
        # Load 10 seconds of audio starting from start_time
        preview_duration = 10.0  # seconds
        y, sr = librosa.load(audio_path, sr=None, offset=start_time, duration=preview_duration)
        
        # Ensure we have audio data
        if len(y) == 0:
            return JsonResponse({"success": False, "error": "No audio data in the selected time range"})

        # Apply the appropriate segmentation algorithm
        if algorithm.algorithm_type == "energy":
            segments = energy_based_segment_audio(
                y, sr, 
                min_duration_ms=min_duration_ms,
                smooth_window=smooth_window, 
                threshold_factor=threshold_factor
            )
        else:  # threshold-based (default)
            segments = auto_segment_audio(
                y, sr, 
                min_duration_ms=min_duration_ms,
                smooth_window=smooth_window, 
                threshold_factor=threshold_factor
            )

        # Adjust segment times to account for the start offset
        adjusted_segments = []
        for onset, offset in segments:
            adjusted_segments.append({
                "onset": onset + start_time,
                "offset": offset + start_time,
                "duration": offset - onset
            })

        # Calculate some statistics
        total_segments = len(adjusted_segments)
        total_duration = sum(seg["duration"] for seg in adjusted_segments)
        avg_duration = total_duration / total_segments if total_segments > 0 else 0

        response_data = {
            "success": True,
            "algorithm_name": algorithm.name,
            "algorithm_type": algorithm.get_algorithm_type_display(),
            "preview_start": start_time,
            "preview_end": start_time + preview_duration,
            "preview_duration": preview_duration,
            "segments": adjusted_segments,
            "stats": {
                "total_segments": total_segments,
                "total_duration": round(total_duration, 3),
                "avg_duration": round(avg_duration, 3),
                "segment_density": round(total_segments / preview_duration, 2)  # segments per second
            },
            "parameters": {
                "min_duration_ms": min_duration_ms,
                "smooth_window": smooth_window,
                "threshold_factor": threshold_factor
            }
        }

        return JsonResponse(response_data)

    except ValueError as e:
        return JsonResponse({"success": False, "error": f"Invalid parameter: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Preview failed: {str(e)}"}, status=500)