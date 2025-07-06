"""
Data listing API views for species, projects, recordings.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count

from .auth import api_key_required
from ..models import Recording, Project
from ..models.organization import Species


@require_http_methods(["GET"])
@api_key_required
def simple_species_list(request):
    """List all species available to the user"""
    user = request.api_user
    user_group = user.profile.group
    
    if user_group:
        # Get species available to this group AND system species (no group)
        species = Species.objects.filter(
            Q(group=user_group) | Q(group__isnull=True)
        )
    else:
        # Fallback to user's own species and system species
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
        # Get the primary species for this project (most common species in recordings)
        species_counts = (
            p.recordings.values('species__id', 'species__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        primary_species = species_counts.first() if species_counts else None
        
        projects_data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description or '',
            'species_name': primary_species['species__name'] if primary_species else 'No recordings',
            'species_id': primary_species['species__id'] if primary_species else None,
            'recording_count': p.recordings.count()
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
    
    # Apply project filter if provided
    project_id = request.GET.get('project_id')
    if project_id:
        try:
            project_id = int(project_id)
            recordings = recordings.filter(project_id=project_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid project_id format'
            }, status=400)
    
    recordings_data = []
    for r in recordings:
        # Check if recording has any segmentations
        has_segmentation = r.segmentations.exists()
        
        recordings_data.append({
            'id': r.id,
            'name': r.name,
            'duration': r.duration,
            'location': r.location or '',
            'recorded_date': r.recorded_date.isoformat() if r.recorded_date else None,
            'species_name': r.species.name,
            'species_id': r.species.id,
            'project_name': r.project.name if r.project else '',
            'project_id': r.project.id if r.project else None,
            'created_at': r.created_at.isoformat(),
            'has_segmentation': has_segmentation,
            'segmentation_count': r.segmentations.count()
        })
    
    return JsonResponse({
        'success': True,
        'recordings': recordings_data,
        'count': len(recordings_data)
    })