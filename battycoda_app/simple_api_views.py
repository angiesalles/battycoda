"""
Simple API views for BattyCoda - using API key authentication.
These are designed to be super simple for R scripts to use.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json

from .models import Recording, Project, Task, TaskBatch
from .models.organization import Species
from .models.user import UserProfile


def get_user_from_api_key(api_key):
    """Get user from API key, return None if invalid"""
    if not api_key:
        return None
    try:
        profile = UserProfile.objects.get(api_key=api_key)
        return profile.user
    except UserProfile.DoesNotExist:
        return None


def api_key_required(view_func):
    """Decorator to require valid API key"""
    def wrapper(request, *args, **kwargs):
        # Handle both GET and POST, and handle list values from QueryDict
        api_key = request.GET.get('api_key') or request.POST.get('api_key')
        
        # Django QueryDict.get() returns the last value, but just in case it's a list
        if isinstance(api_key, list):
            api_key = api_key[0] if api_key else None
            
        user = get_user_from_api_key(api_key)
        if not user:
            return JsonResponse({'error': 'Invalid or missing API key'}, status=401)
        request.api_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


@require_http_methods(["GET"])
@api_key_required
def simple_species_list(request):
    """List all species available to the user"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        # Get species available to this group AND system species (no group)
        from django.db.models import Q
        species = Species.objects.filter(
            Q(group=user_group) | Q(group__isnull=True)
        )
    else:
        # Fallback to user's own species and system species
        from django.db.models import Q
        species = Species.objects.filter(
            Q(created_by=user) | Q(group__isnull=True)
        )
    
    # Convert to simple format
    species_data = []
    for s in species:
        species_data.append({
            'id': s.id,
            'name': s.name,
            'description': s.description or ''
        })
    
    return JsonResponse({
        'success': True,
        'species': species_data,
        'count': len(species_data)
    })


@require_http_methods(["GET"])
@api_key_required
def simple_projects_list(request):
    """List all projects available to the user"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        projects = Project.objects.filter(group=user_group)
    else:
        projects = Project.objects.filter(created_by=user)
    
    projects_data = []
    for p in projects:
        projects_data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description or '',
            'species_name': p.species.name,
            'species_id': p.species.id
        })
    
    return JsonResponse({
        'success': True,
        'projects': projects_data,
        'count': len(projects_data)
    })


@require_http_methods(["GET"])
@api_key_required
def simple_recordings_list(request):
    """List all recordings available to the user"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        recordings = Recording.objects.filter(group=user_group).order_by('-created_at')
    else:
        recordings = Recording.objects.filter(created_by=user).order_by('-created_at')
    
    recordings_data = []
    for r in recordings:
        recordings_data.append({
            'id': r.id,
            'name': r.name,
            'duration': r.duration,
            'location': r.location or '',
            'recorded_date': r.recorded_date.isoformat() if r.recorded_date else None,
            'species_name': r.species.name,
            'project_name': r.project.name if r.project else '',
            'created_at': r.created_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'recordings': recordings_data,
        'count': len(recordings_data)
    })


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
            from django.db.models import Q
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


@require_http_methods(["GET"])
@api_key_required
def simple_user_info(request):
    """Get basic user info including API key status"""
    user = request.api_user
    
    return JsonResponse({
        'success': True,
        'user': {
            'username': user.username,
            'email': user.email,
            'group_name': user.profile.group.name if user.profile.group else None,
            'is_group_admin': user.profile.is_current_group_admin,
            'api_key_active': bool(user.profile.api_key)
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def simple_generate_api_key(request):
    """Generate a new API key for the user"""
    user = request.api_user
    new_key = user.profile.generate_api_key()
    
    return JsonResponse({
        'success': True,
        'message': 'New API key generated successfully',
        'api_key': new_key
    })