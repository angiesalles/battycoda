
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

# Set up logging

@login_required
def spectrogram_view(request):
    """Handle spectrogram generation and serving"""
    from .audio.views import handle_spectrogram

    return handle_spectrogram(request)

@login_required
def audio_snippet_view(request):
    """Handle audio snippet generation and serving"""
    from .audio.views import handle_audio_snippet

    return handle_audio_snippet(request)

@login_required 
def simple_audio_bit_view(request):
    """Simple audio bit delivery using deliverAudioBit function"""
    # Validate required parameters
    required_params = ['file_path', 'onset', 'offset']
    for param in required_params:
        if param not in request.GET:
            return HttpResponse(f"Missing required parameter: {param}", status=400)
    
    try:
        file_path = request.GET['file_path']
        onset = float(request.GET['onset'])
        offset = float(request.GET['offset'])
        loudness = float(request.GET.get('loudness', '1.0'))
        pitch_shift = float(request.GET.get('pitch_shift', '1.0'))
        
        # Use the new deliverAudioBit function
        from .audio.modules.audio_processing import deliverAudioBit
        return deliverAudioBit(file_path, onset, offset, loudness, pitch_shift)
        
    except ValueError as e:
        return HttpResponse(f"Invalid parameter value: {str(e)}", status=400)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

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
    from .audio.views import task_status as audio_task_status

    return audio_task_status(request, task_id)
