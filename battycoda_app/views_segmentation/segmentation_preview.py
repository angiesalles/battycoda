"""
Views for previewing segmentation results on audio recordings.
"""
import os
import tempfile
import concurrent.futures

# Cache directories are configured in settings.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models import Recording, SegmentationAlgorithm
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
        duration = float(request.POST.get("duration", 1.0))
        
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
        
        from battycoda_app.models import SegmentationAlgorithm
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
        from battycoda_app.models import Segmentation
        preview_segmentation = Segmentation.objects.create(
            name=f"Preview Segmentation for {preview_name}",
            recording=hidden_recording,
            algorithm=algorithm,
            created_by=request.user,
            status='in_progress',  # Will be updated when task starts
            progress=0
        )
        
        # Run spectrogram generation and segmentation in parallel
        def generate_spectrogram_for_recording():
            """Generate HDF5 spectrogram for the preview recording."""
            try:
                from battycoda_app.audio.task_modules.spectrogram.hdf5_generation import generate_recording_spectrogram
                from celery import current_app

                # Call the existing task synchronously (not via Celery delay)
                task = current_app.tasks['battycoda_app.audio.task_modules.spectrogram.hdf5_generation.generate_recording_spectrogram']
                result = task(hidden_recording.id)

                if result.get('status') == 'success':
                    return True
                else:
                    print(f"Warning: Spectrogram generation returned non-success: {result}")
                    return False

            except Exception as e:
                print(f"Warning: Failed to generate spectrogram for preview recording: {e}")
                return False

        def run_segmentation_task():
            """Run segmentation task for the preview recording."""
            try:
                from battycoda_app.audio.task_modules.segmentation_tasks import auto_segment_recording_task
                
                # Run segmentation task directly
                result = auto_segment_recording_task(
                    hidden_recording.id, preview_segmentation.id, min_duration_ms, 
                    smooth_window, threshold_factor, low_freq, high_freq
                )
                
                # Check the result
                if result.get("status") != "success":
                    raise ValueError(f"Segmentation failed: {result.get('message', 'Unknown error')}")
                
                return result
                
            except Exception as e:
                # If segmentation fails, mark as failed
                preview_segmentation.status = 'failed'
                preview_segmentation.save()
                raise ValueError(f"Failed to complete segmentation task: {str(e)}")

        # Run both tasks in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            spectrogram_future = executor.submit(generate_spectrogram_for_recording)
            segmentation_future = executor.submit(run_segmentation_task)
            
            # Wait for both to complete
            spectrogram_success = spectrogram_future.result(timeout=60)
            segmentation_result = segmentation_future.result(timeout=60)
        
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