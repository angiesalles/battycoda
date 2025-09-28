"""
AJAX endpoints for segment management operations.
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from battycoda_app.models.recording import Recording, Segment, Segmentation


@login_required
def load_segments_ajax(request, segmentation_id):
    """AJAX endpoint to load segments within a specific time range for waveform display"""
    segmentation = get_object_or_404(Segmentation, id=segmentation_id)
    recording = segmentation.recording
    
    # Check if the user has permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method == "GET":
        # Use the specific segmentation
        # Get time range parameters
        start_time = request.GET.get('start_time', 0)
        end_time = request.GET.get('end_time')
        
        try:
            start_time = float(start_time)
            segments_query = Segment.objects.filter(
                segmentation=segmentation,
                onset__gte=start_time
            ).order_by("onset")
            
            if end_time:
                end_time = float(end_time)
                segments_query = segments_query.filter(offset__lte=end_time)
            
            # Limit to 500 segments maximum to prevent overload
            segments = segments_query[:500]
            
            segments_data = []
            for segment in segments:
                segments_data.append({
                    "id": segment.id,
                    "onset": segment.onset,
                    "offset": segment.offset
                })
            
            return JsonResponse({
                "success": True,
                "segments": segments_data,
                "count": len(segments_data)
            })
            
        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid time parameters"}, status=400)
    
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)