"""Cluster exploration and visualization views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import Segment
from ..models.clustering import Cluster, ClusterCallMapping, ClusteringRun
from ..models.organization import Species


@login_required
def cluster_explorer(request, run_id):
    """Interactive visualization of clusters for a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)

    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')

    context = {
        'clustering_run': clustering_run,
        'clusters': clusters,
    }
    return render(request, 'clustering/cluster_explorer.html', context)


@login_required
def mapping_interface(request, run_id):
    """Interface for mapping clusters to call types."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)

    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')

    if clustering_run.group:
        available_species = Species.objects.filter(
            models.Q(is_system=True) |
            models.Q(group=clustering_run.group)
        ).order_by('name')
    else:
        available_species = Species.objects.filter(
            models.Q(is_system=True) |
            models.Q(created_by=request.user, group__isnull=True)
        ).order_by('name')

    existing_mappings = ClusterCallMapping.objects.filter(
        cluster__clustering_run=clustering_run
    ).order_by('-confidence')

    context = {
        'clustering_run': clustering_run,
        'clusters': clusters,
        'available_species': available_species,
        'existing_mappings': existing_mappings,
    }
    return render(request, 'clustering/mapping_interface.html', context)


@login_required
def get_cluster_data(request):
    """API endpoint to get data for a specific cluster."""
    cluster_id = request.GET.get('cluster_id')
    if not cluster_id:
        return JsonResponse({'status': 'error', 'message': 'No cluster ID provided'})

    cluster = get_object_or_404(Cluster, id=cluster_id)

    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this cluster'})

        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this cluster'})

    mappings = ClusterCallMapping.objects.filter(cluster=cluster).select_related('call', 'call__species')

    representative_spectrogram_url = None
    representative_audio_url = None
    if cluster.representative_segment:
        representative_spectrogram_url = reverse('segment_spectrogram', args=[cluster.representative_segment.id])
        representative_audio_url = reverse('segment_audio', args=[cluster.representative_segment.id])

    response_data = {
        'status': 'success',
        'cluster_id': cluster.cluster_id,
        'label': cluster.label,
        'description': cluster.description,
        'is_labeled': cluster.is_labeled,
        'size': cluster.size,
        'coherence': cluster.coherence,
        'representative_spectrogram_url': representative_spectrogram_url,
        'representative_audio_url': representative_audio_url,
        'mappings': []
    }

    for mapping in mappings:
        response_data['mappings'].append({
            'id': mapping.id,
            'species_name': mapping.call.species.name,
            'call_name': mapping.call.short_name,
            'confidence': mapping.confidence,
        })

    return JsonResponse(response_data)


@login_required
def get_segment_data(request):
    """API endpoint to get data for a specific segment."""
    segment_id = request.GET.get('segment_id')

    if not segment_id:
        return JsonResponse({'status': 'error', 'message': 'No segment ID provided'})

    segment = get_object_or_404(Segment, id=segment_id)

    if not request.user.is_staff:
        if segment.recording.group and segment.recording.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this segment'})

        if not segment.recording.group and segment.recording.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this segment'})

    response_data = {
        'status': 'success',
        'segment_id': segment.id,
        'recording_name': segment.recording.name,
        'onset': segment.onset,
        'offset': segment.offset,
        'duration': segment.offset - segment.onset,
        'spectrogram_url': reverse('segment_spectrogram', args=[segment.id]),
        'audio_url': reverse('segment_audio', args=[segment.id])
    }

    return JsonResponse(response_data)
