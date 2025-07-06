"""
File upload API views.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .auth import api_key_required
from ..models import Recording, Project
from ..models.organization import Species


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_upload_recording(request):
    """Upload a WAV recording with minimal required fields"""
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
        
        if not all([name, species_id, wav_file]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: name, species_id, wav_file'
            }, status=400)
        
        species_id = int(species_id)
        
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
        
        # Create the recording
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
        
        return JsonResponse({
            'success': True,
            'recording': {
                'id': recording.id,
                'name': recording.name,
                'duration': recording.duration,
                'species_name': recording.species.name,
                'project_name': recording.project.name if recording.project else None,
                'created_at': recording.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)