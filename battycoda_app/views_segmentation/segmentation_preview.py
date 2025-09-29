"""
Views for previewing segmentation results on audio recordings.
"""
import os
import tempfile

# Configure librosa and numba cache before any imports
os.environ['LIBROSA_CACHE_DIR'] = '/tmp/librosa_cache'
os.environ['LIBROSA_CACHE_LEVEL'] = '0'  # Disable caching
os.environ['NUMBA_CACHE_DIR'] = '/tmp/numba_cache'
os.environ['NUMBA_DISABLE_JIT'] = '1'  # Disable JIT compilation entirely
os.environ['NUMBA_DISABLE_PERFORMANCE_WARNINGS'] = '1'
os.environ['NUMBA_DISABLE_INTEL_SVML'] = '1'
# Create the cache directories if they don't exist
os.makedirs('/tmp/librosa_cache', exist_ok=True)
os.makedirs('/tmp/numba_cache', exist_ok=True)

# Monkey patch numba to completely disable JIT before any imports
try:
    import numba
    def no_jit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    
    numba.jit = no_jit
    numba.njit = no_jit
    if hasattr(numba, 'vectorize'):
        numba.vectorize = no_jit
    if hasattr(numba, 'guvectorize'):
        numba.guvectorize = no_jit
except ImportError:
    pass

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models.recording import Recording, SegmentationAlgorithm
import hashlib
import os
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.urls import reverse

# Import librosa with caching disabled
import librosa
import numpy as np
import soundfile as sf


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
        
        # Get bandpass filter parameters
        low_freq = request.POST.get("low_freq")
        high_freq = request.POST.get("high_freq")
        
        # Convert frequency parameters to integers or None
        if low_freq and low_freq.strip():
            low_freq = int(low_freq)
        else:
            low_freq = None
            
        if high_freq and high_freq.strip():
            high_freq = int(high_freq)
        else:
            high_freq = None

        # Validate parameters
        if min_duration_ms < 1:
            raise ValueError("Minimum duration must be at least 1ms")
        if smooth_window < 1:
            raise ValueError("Smooth window must be at least 1 sample")
        if threshold_factor <= 0 or threshold_factor > 10:
            raise ValueError("Threshold factor must be between 0 and 10")
        if start_time < 0:
            raise ValueError("Start time must be non-negative")
        if low_freq is not None and low_freq <= 0:
            raise ValueError("Low frequency must be positive")
        if high_freq is not None and high_freq <= 0:
            raise ValueError("High frequency must be positive")
        if low_freq is not None and high_freq is not None and low_freq >= high_freq:
            raise ValueError("Low frequency must be less than high frequency")

        # Get algorithm
        algorithm = get_object_or_404(SegmentationAlgorithm, id=int(algorithm_id), is_active=True)

        # Check algorithm access permission
        if algorithm.group and (not profile.group or algorithm.group != profile.group):
            return JsonResponse({"success": False, "error": "You don't have permission to use this algorithm"}, status=403)

        # Import the segmentation functions
        from battycoda_app.audio.modules.segmentation import auto_segment_audio, energy_based_segment_audio

        # Load the audio file for the preview window
        audio_path = recording.wav_file.path
        
        # Load 10 seconds of audio starting from start_time
        preview_duration = 10.0  # seconds
        y, sr = librosa.load(audio_path, sr=None, offset=start_time, duration=preview_duration)
        
        # Ensure we have audio data
        if len(y) == 0:
            return JsonResponse({"success": False, "error": "No audio data in the selected time range"})

        # Create a temporary audio file with the preview data
        temp_audio_file = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_audio_file = temp_file.name
                
            # Write audio data to temporary file
            sf.write(temp_audio_file, y, sr)

            # Apply the appropriate segmentation algorithm
            if algorithm.algorithm_type == "energy":
                segments = energy_based_segment_audio(
                    temp_audio_file,
                    min_duration_ms=min_duration_ms,
                    smooth_window=smooth_window, 
                    threshold_factor=threshold_factor,
                    low_freq=low_freq,
                    high_freq=high_freq
                )
            else:  # threshold-based (default)
                segments = auto_segment_audio(
                    temp_audio_file,
                    min_duration_ms=min_duration_ms,
                    smooth_window=smooth_window, 
                    threshold_factor=threshold_factor,
                    low_freq=low_freq,
                    high_freq=high_freq
                )

            # Extract onset and offset lists from the returned tuple
            # Functions return (onsets, offsets) or (onsets, offsets, debug_path)
            if len(segments) == 3:
                onsets, offsets, debug_path = segments
            else:
                onsets, offsets = segments
            
            # Adjust segment times to account for the start offset
            adjusted_segments = []
            for onset, offset in zip(onsets, offsets):
                adjusted_segments.append({
                    "onset": onset + start_time,
                    "offset": offset + start_time,
                    "duration": offset - onset
                })

            # Calculate some statistics
            total_segments = len(adjusted_segments)
            total_duration = sum(seg["duration"] for seg in adjusted_segments)
            avg_duration = total_duration / total_segments if total_segments > 0 else 0

            # Try to get existing spectrogram or trigger async generation
            preview_spectrogram_url = get_or_generate_preview_spectrogram(recording, start_time, preview_duration)
            
            response_data = {
                "success": True,
                "recording_id": recording.id,
                "algorithm_name": algorithm.name,
                "algorithm_type": algorithm.get_algorithm_type_display(),
                "preview_start": start_time,
                "preview_end": start_time + preview_duration,
                "preview_duration": preview_duration,
                "segments": adjusted_segments,
                "spectrogram_url": preview_spectrogram_url,
                "audio_url": f"/audio/bit/?file_path={recording.wav_file.path}&onset={start_time}&offset={start_time + preview_duration}&loudness=1.0" if recording.wav_file else None,
                "stats": {
                    "total_segments": total_segments,
                    "total_duration": round(total_duration, 3),
                    "avg_duration": round(avg_duration, 3),
                    "segment_density": round(total_segments / preview_duration, 2)  # segments per second
                },
                "parameters": {
                    "min_duration_ms": min_duration_ms,
                    "smooth_window": smooth_window,
                    "threshold_factor": threshold_factor,
                    "low_freq": low_freq,
                    "high_freq": high_freq
                }
            }
            
            return JsonResponse(response_data)
        
        finally:
            # Clean up temporary file
            if temp_audio_file and os.path.exists(temp_audio_file):
                try:
                    os.unlink(temp_audio_file)
                except OSError:
                    pass  # Ignore cleanup errors

    except ValueError as e:
        return JsonResponse({"success": False, "error": f"Invalid parameter: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Preview failed: {str(e)}"}, status=500)


def get_or_generate_preview_spectrogram(recording, start_time, duration):
    """
    Get existing preview spectrogram or trigger async generation.
    
    Args:
        recording: Recording model instance
        start_time: Start time in seconds
        duration: Duration in seconds
        
    Returns:
        str: URL to the spectrogram image, or None if not available yet
    """
    try:
        from battycoda_app.audio.utils import appropriate_file
        from battycoda_app.audio.task_modules.spectrogram_tasks import generate_spectrogram_task
        
        # Set up parameters for the existing spectrogram system
        args = {
            "call": "0",  # Use 0 for preview
            "channel": "0",  # Use first channel
            "contrast": "4.0",  # Default contrast
            "overview": "1",  # Use overview mode for time windows
            "low_overlap": "1",  # Use 50% overlap for memory efficiency in previews
            "onset": str(start_time),
            "offset": str(start_time + duration),
            "generated_on_fly": "1",  # Use preview colormap
        }
        
        # Get the audio file path
        audio_path = recording.wav_file.path
        
        # Generate spectrogram path using existing system
        output_path = appropriate_file(audio_path, args)
        
        # Check if spectrogram already exists
        if os.path.exists(output_path):
            # Convert file path to URL
            relative_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
            return f"/media/{relative_path.replace(os.sep, '/')}"
        
        # If not exists, trigger async generation
        print(f"Triggering async spectrogram generation for preview at {start_time}s")
        generate_spectrogram_task.delay(audio_path, args, output_path)
        
        # Return None for now - frontend will fall back to simulated
        return None
        
    except Exception as e:
        print(f"Failed to setup preview spectrogram generation: {e}")
        return None


@login_required
def create_preview_recording_view(request, recording_id):
    """
    Create a hidden preview recording with a 10-second audio segment,
    then redirect to the segmentation detail view for maximum code reuse.
    """
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Only POST requests allowed"}, status=405)
    
    # Get the original recording
    recording = get_object_or_404(Recording.all_objects, id=recording_id)  # Use all_objects in case original is hidden
    
    # Check permissions
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    try:
        # Get parameters
        start_time = float(request.POST.get("start_time", 0))
        duration = float(request.POST.get("duration", 10.0))
        
        # Get segmentation parameters 
        algorithm_id = request.POST.get("algorithm")
        min_duration_ms = int(request.POST.get("min_duration_ms", 10))
        smooth_window = int(request.POST.get("smooth_window", 3))
        threshold_factor = float(request.POST.get("threshold_factor", 0.5))
        
        # Get bandpass filter parameters
        low_freq = request.POST.get("low_freq")
        high_freq = request.POST.get("high_freq")
        
        # Convert frequency parameters to integers or None
        if low_freq and low_freq.strip():
            low_freq = int(low_freq)
        else:
            low_freq = None
            
        if high_freq and high_freq.strip():
            high_freq = int(high_freq)
        else:
            high_freq = None
        
        # Validate parameters
        if start_time < 0:
            raise ValueError("Start time must be non-negative")
        if duration <= 0 or duration > 60:
            raise ValueError("Duration must be between 0 and 60 seconds")
        if min_duration_ms < 1:
            raise ValueError("Minimum duration must be at least 1ms")
        if smooth_window < 1:
            raise ValueError("Smooth window must be at least 1 sample")
        if threshold_factor <= 0 or threshold_factor > 10:
            raise ValueError("Threshold factor must be between 0 and 10")
        if low_freq is not None and low_freq <= 0:
            raise ValueError("Low frequency must be positive")
        if high_freq is not None and high_freq <= 0:
            raise ValueError("High frequency must be positive")
        if low_freq is not None and high_freq is not None and low_freq >= high_freq:
            raise ValueError("Low frequency must be less than high frequency")
        
        # Get and validate algorithm
        if not algorithm_id:
            raise ValueError("Algorithm is required")
        
        from battycoda_app.models.recording import SegmentationAlgorithm
        try:
            algorithm = SegmentationAlgorithm.objects.get(id=int(algorithm_id), is_active=True)
        except SegmentationAlgorithm.DoesNotExist:
            raise ValueError(f"Algorithm with ID {algorithm_id} not found")
        
        # Check algorithm access permission
        if algorithm.group and (not profile.group or algorithm.group != profile.group):
            raise ValueError("You don't have permission to use this algorithm")
        
        # Load the audio segment
        audio_path = recording.wav_file.path
        y, sr = librosa.load(audio_path, sr=None, offset=start_time, duration=duration)
        
        if len(y) == 0:
            return JsonResponse({"success": False, "error": "No audio data in the selected time range"})
        
        # Calculate actual duration from loaded audio
        actual_duration = len(y) / sr
        
        # Create temporary audio file in memory
        import io
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, y, sr, format='WAV', subtype='PCM_16')
        audio_buffer.seek(0)
        audio_content = ContentFile(audio_buffer.read())
        
        # Create hidden preview recording
        preview_name = f"Preview {recording.name} ({start_time:.1f}s-{start_time+actual_duration:.1f}s)"
        preview_filename = f"preview_{uuid.uuid4().hex}.wav"
        
        hidden_recording = Recording.all_objects.create(
            name=preview_name,
            description=f"Preview of {recording.name} from {start_time:.1f}s to {start_time+actual_duration:.1f}s",
            duration=actual_duration,  # Use actual duration from loaded audio
            sample_rate=int(sr),  # Ensure it's an integer
            file_ready=True,
            hidden=True,  # Mark as hidden so it doesn't appear in normal lists
            species=recording.species,
            project=recording.project,
            group=recording.group,
            created_by=request.user,
            # Copy metadata
            recorded_date=recording.recorded_date,
            location=recording.location,
            equipment=recording.equipment,
            environmental_conditions=recording.environmental_conditions,
        )
        
        # Save the audio file - ensure it's saved properly
        hidden_recording.wav_file.save(preview_filename, audio_content, save=False)
        hidden_recording.save()  # Save the recording after file is attached
        
        # Create a segmentation for the hidden recording
        from battycoda_app.models.recording import Segmentation
        preview_segmentation = Segmentation.objects.create(
            name=f"Preview Segmentation for {preview_name}",
            recording=hidden_recording,
            algorithm=algorithm,
            is_active=True,
            created_by=request.user,
            status='in_progress',  # Will be updated when task starts
            progress=0
        )
        
        # First, generate spectrogram for the hidden recording
        try:
            from battycoda_app.audio.task_modules.spectrogram_tasks import generate_recording_spectrogram
            
            # Generate spectrogram synchronously for the preview
            spectrogram_filename = f"spectrogram_{uuid.uuid4().hex}.png"
            hidden_recording.spectrogram_file = spectrogram_filename
            hidden_recording.save()
            
            # Generate the spectrogram (this will run synchronously)
            generate_recording_spectrogram(hidden_recording.id)
            
        except Exception as e:
            # If spectrogram generation fails, continue anyway but log the error
            print(f"Warning: Failed to generate spectrogram for preview recording: {e}")
        
        # Automatically trigger the segmentation task and wait for completion
        try:
            from celery import current_app
            from celery.result import AsyncResult
            import time
            
            # Launch Celery task with the same parameters as the normal segmentation
            task = current_app.send_task(
                algorithm.celery_task,
                args=[hidden_recording.id, preview_segmentation.id, min_duration_ms, smooth_window, threshold_factor, low_freq, high_freq],
            )
            
            # Update the segmentation with the actual task ID
            preview_segmentation.task_id = task.id
            preview_segmentation.save(update_fields=['task_id'])
            
            # Wait for task completion (with timeout for safety)
            result = AsyncResult(task.id)
            timeout = 30  # 30 seconds timeout for 10s audio segment
            start_time = time.time()
            
            while not result.ready():
                if time.time() - start_time > timeout:
                    raise ValueError("Segmentation task timed out")
                time.sleep(0.5)  # Check every 500ms
            
            # Check if task completed successfully
            if result.successful():
                task_result = result.get()
                if task_result.get("status") != "success":
                    raise ValueError(f"Segmentation failed: {task_result.get('message', 'Unknown error')}")
            else:
                raise ValueError(f"Segmentation task failed: {str(result.result)}")
            
        except Exception as e:
            # If task launching or completion fails, mark segmentation as failed
            preview_segmentation.status = 'failed'
            preview_segmentation.save()
            raise ValueError(f"Failed to complete segmentation task: {str(e)}")
        
        # Redirect to the segmentation detail view
        segmentation_url = reverse('battycoda_app:segmentation_detail', kwargs={'segmentation_id': preview_segmentation.id})
        return JsonResponse({
            "success": True,
            "preview_url": segmentation_url,
            "preview_recording_id": hidden_recording.id,
            "preview_segmentation_id": preview_segmentation.id,
            "message": "Preview recording created successfully"
        })
        
    except ValueError as e:
        return JsonResponse({"success": False, "error": f"Invalid parameter: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Failed to create preview: {str(e)}"}, status=500)