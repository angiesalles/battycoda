"""
Pickle segmentation upload API views.
Handles uploading pickle files to create segmentations for existing recordings.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .auth import api_key_required
from ..models import Recording
from ..models import Segmentation, Segment
from ..audio.utils import process_pickle_file


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def upload_pickle_segmentation(request, recording_id):
    """Upload a pickle file to create segmentation for an existing recording"""
    user = request.api_user
    
    try:
        # Get the recording
        recording = Recording.objects.get(id=recording_id)
        
        # Check permissions - user must be in same group or be the creator
        if recording.group != user.profile.group and recording.created_by != user:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied: Cannot modify this recording'
            }, status=403)
        
        # Get the pickle file
        pickle_file = request.FILES.get('pickle_file')
        if not pickle_file:
            return JsonResponse({
                'success': False,
                'error': 'Missing required field: pickle_file'
            }, status=400)
        
        # Optional segmentation name
        segmentation_name = request.POST.get('name', 'API Pickle Upload')
        
        # Process the pickle file and create segmentation
        with transaction.atomic():
            try:
                # Get recording duration for validation
                recording_duration = None
                if recording.spectrogram_file:
                    import h5py
                    import os
                    from django.conf import settings
                    h5_path = os.path.join(settings.MEDIA_ROOT, 'spectrograms', 'recordings', recording.spectrogram_file)
                    if os.path.exists(h5_path):
                        with h5py.File(h5_path, 'r') as f:
                            recording_duration = float(f.attrs['duration'])

                # Process the pickle file to extract onsets and offsets with validation
                onsets, offsets = process_pickle_file(pickle_file, max_duration=recording_duration)
                
                # Create a new segmentation
                segmentation = Segmentation.objects.create(
                    recording=recording,
                    name=segmentation_name,
                    algorithm=None,  # Manual/imported segmentation
                    status="completed",
                    created_by=user,
                    segments_created=len(onsets)
                )
                
                # Create individual segments
                segments_created = 0
                for i, (onset, offset) in enumerate(zip(onsets, offsets)):
                    Segment.objects.create(
                        recording=recording,
                        segmentation=segmentation,
                        name=f"Segment {i + 1}",
                        onset=float(onset),
                        offset=float(offset),
                        created_by=user
                    )
                    segments_created += 1
                
                # Update segments count
                segmentation.segments_created = segments_created
                segmentation.save()
                
                return JsonResponse({
                    'success': True,
                    'recording': {
                        'id': recording.id,
                        'name': recording.name
                    },
                    'segmentation': {
                        'id': segmentation.id,
                        'name': segmentation.name,
                        'segments_count': segments_created,
                        'created_at': segmentation.created_at.isoformat()
                    }
                })
                
            except Exception as pickle_error:
                return JsonResponse({
                    'success': False,
                    'error': f'Pickle file processing failed: {str(pickle_error)}'
                }, status=400)
                
    except Recording.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Recording with ID {recording_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)