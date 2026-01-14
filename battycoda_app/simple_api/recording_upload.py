"""
Recording upload API views.
Handles WAV file uploads with optional pickle segmentation data.
"""
import logging
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.db import transaction

from .auth import api_key_required
from ..models import Recording, Project
from ..models.organization import Species
from ..models import Segmentation, Segment
from ..audio.utils import process_pickle_file
from ..utils_modules.cleanup import safe_remove_file, safe_cleanup_dir
from ..utils_modules.validation import safe_int

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def upload_recording(request):
    """Upload a WAV recording with optional pickle segmentation data"""
    user = request.api_user
    
    # Check if user has a group
    if not user.profile.group:
        return JsonResponse({
            'success': False,
            'error': 'User must be assigned to a group to upload recordings'
        }, status=400)
    
    # Get required fields
    try:
        name = request.POST.get('name')
        species_id = request.POST.get('species_id')
        wav_file = request.FILES.get('wav_file')
        pickle_file = request.FILES.get('pickle_file')  # Optional segmentation data

        if not all([name, species_id, wav_file]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: name, species_id, wav_file'
            }, status=400)

        species_id = safe_int(species_id)
        if species_id is None:
            return JsonResponse({
                'success': False,
                'error': 'species_id must be a valid integer'
            }, status=400)
        
        # Get optional fields
        description = request.POST.get('description', '')
        location = request.POST.get('location', '')
        project_id = request.POST.get('project_id')
        recorded_date = request.POST.get('recorded_date')  # YYYY-MM-DD format
        
        # Validate species exists and user has access
        try:
            user_group = user.profile.group
            
            if user_group:
                # User has a group - can access group species AND system species
                species = Species.objects.get(
                    Q(id=species_id) & (Q(group=user_group) | Q(group__isnull=True))
                )
            else:
                # User has no group - can access their own species AND system species
                species = Species.objects.get(
                    Q(id=species_id) & (Q(created_by=user) | Q(group__isnull=True))
                )
        except Species.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Species with ID {species_id} not found or not accessible'
            }, status=400)
        
        # Validate project if provided
        project = None
        if project_id:
            try:
                project_id = int(project_id)
                project = Project.objects.get(id=project_id, group=user.profile.group)
            except (ValueError, Project.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': f'Project with ID {project_id} not found or not accessible'
                }, status=400)
        
        # Parse date if provided
        parsed_date = None
        if recorded_date:
            try:
                from datetime import datetime
                parsed_date = datetime.strptime(recorded_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=400)
        
        # Check if file should be split
        import tempfile
        from ..audio.utils import get_audio_duration, split_audio_file
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Save uploaded file to temporary location to check duration
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            for chunk in wav_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # Check duration
            duration = get_audio_duration(temp_file_path)

            recordings_created = []

            # If duration > 60 seconds, split into 1-minute chunks
            if duration > 60:
                chunk_paths = split_audio_file(temp_file_path, chunk_duration_seconds=60)

                # Create a recording for each chunk
                for i, chunk_path in enumerate(chunk_paths):
                    with open(chunk_path, 'rb') as chunk_file:
                        chunk_name = f"{name} (Part {i+1}/{len(chunk_paths)})"
                        chunk_django_file = SimpleUploadedFile(
                            os.path.basename(chunk_path),
                            chunk_file.read(),
                            content_type='audio/wav'
                        )

                        with transaction.atomic():
                            recording = Recording.objects.create(
                                name=chunk_name,
                                description=description,
                                wav_file=chunk_django_file,
                                location=location,
                                recorded_date=parsed_date,
                                species=species,
                                project=project,
                                group=user.profile.group,
                                created_by=user,
                                file_ready=True
                            )
                            recordings_created.append(recording)

                # Clean up chunk files
                for chunk_path in chunk_paths:
                    safe_remove_file(chunk_path, "audio chunk file")
                    safe_cleanup_dir(os.path.dirname(chunk_path), "chunk directory")

                # Return response for split recordings
                return JsonResponse({
                    'success': True,
                    'split': True,
                    'original_duration': duration,
                    'chunks_created': len(recordings_created),
                    'recordings': [{
                        'id': rec.id,
                        'name': rec.name,
                        'created_at': rec.created_at.isoformat()
                    } for rec in recordings_created]
                })

            else:
                # File is ≤ 60 seconds, create single recording
                # Reset file pointer
                wav_file.seek(0)

                with transaction.atomic():
                    recording = Recording.objects.create(
                        name=name,
                        description=description,
                        wav_file=wav_file,
                        location=location,
                        recorded_date=parsed_date,
                        species=species,
                        project=project,
                        group=user.profile.group,
                        created_by=user,
                        file_ready=True
                    )
            
            # Process pickle file if provided
            segmentation_info = None
            if pickle_file:
                try:
                    # Reset file pointer to beginning (important for file processing)
                    pickle_file.seek(0)

                    # Process the pickle file to extract onsets and offsets
                    onsets, offsets = process_pickle_file(pickle_file)

                    # Create a new segmentation
                    segmentation = Segmentation.objects.create(
                        recording=recording,
                        name="API Upload Segmentation",
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

                    segmentation_info = {
                        'id': segmentation.id,
                        'name': segmentation.name,
                        'segments_count': segments_created,
                        'created_at': segmentation.created_at.isoformat()
                    }
                    
                except Exception as pickle_error:
                    # If pickle processing fails, still return the recording but note the error
                    segmentation_info = {
                        'error': f'Pickle file processing failed: {str(pickle_error)}'
                    }

            # Prepare response (only for non-split files)
            response_data = {
                'success': True,
                'split': False,
                'recording': {
                    'id': recording.id,
                    'name': recording.name,
                    'duration': recording.duration,
                    'species_name': recording.species.name,
                    'project_name': recording.project.name if recording.project else None,
                    'created_at': recording.created_at.isoformat()
                }
            }

            # Add segmentation info if pickle file was processed
            if segmentation_info:
                response_data['segmentation'] = segmentation_info

            return JsonResponse(response_data)

        finally:
            # Clean up temporary file
            safe_remove_file(temp_file_path, "temporary upload file")
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)