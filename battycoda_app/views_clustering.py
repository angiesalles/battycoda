"""
Views for the clustering module of BattyCoda.

This module provides views for the unsupervised clustering system,
which allows discovery of patterns in audio data without requiring
prior species associations.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
from django.contrib import messages

from .models import Segmentation, Segment, Call
from .models.clustering import (
    ClusteringAlgorithm, 
    ClusteringRun, 
    Cluster, 
    SegmentCluster,
    ClusterCallMapping
)
from .models.organization import Species
from .audio.task_modules.clustering.tasks import run_clustering


@login_required
def dashboard(request):
    """Display a list of clustering runs for the user's group."""
    # Get user's group
    group = request.user.profile.group
    
    # Get clustering runs for this group
    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by('-created_at')
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get available clustering algorithms
    if group:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            group=group
        ).order_by('name')
    else:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            created_by=request.user
        ).order_by('name')
    
    # Add system-wide algorithms
    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(
            is_active=True, 
            group__isnull=True
        ).exclude(id__in=[a.id for a in algorithms])
    )
    
    context = {
        'clustering_runs': clustering_runs,
        'algorithms': algorithms,
    }
    return render(request, 'clustering/dashboard.html', context)


@login_required
def create_clustering_run(request):
    """Form for creating a new clustering run."""
    # Get user's group
    group = request.user.profile.group
    
    # Get available segmentations
    if group:
        segmentations = Segmentation.objects.filter(
            recording__group=group
        ).order_by('-created_at')
    else:
        segmentations = Segmentation.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
    
    # Get available clustering algorithms
    if group:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            group=group
        ).order_by('name')
    else:
        algorithms = ClusteringAlgorithm.objects.filter(
            is_active=True
        ).filter(
            created_by=request.user
        ).order_by('name')
    
    # Add system-wide algorithms
    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(
            is_active=True, 
            group__isnull=True
        ).exclude(id__in=[a.id for a in algorithms])
    )
    
    # Handle form submission
    if request.method == 'POST':
        # Validate form data
        segmentation_id = request.POST.get('segmentation')
        algorithm_id = request.POST.get('algorithm')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        n_clusters = request.POST.get('n_clusters')
        feature_method = request.POST.get('feature_method', 'mfcc')
        
        # Validate required fields
        if not all([segmentation_id, algorithm_id, name]):
            messages.error(request, "Please fill in all required fields")
            return redirect('battycoda_app:create_clustering_run')
        
        # Get the segmentation and algorithm
        segmentation = get_object_or_404(Segmentation, id=segmentation_id)
        algorithm = get_object_or_404(ClusteringAlgorithm, id=algorithm_id)
        
        # Create the clustering run
        clustering_run = ClusteringRun.objects.create(
            name=name,
            description=description,
            segmentation=segmentation,
            algorithm=algorithm,
            n_clusters=int(n_clusters) if n_clusters else None,
            feature_extraction_method=feature_method,
            created_by=request.user,
            group=group,
            status='pending',
            progress=0.0
        )
        
        # Launch the appropriate clustering task based on algorithm
        from celery import current_app
        
        # Get the celery task name for this algorithm
        task_name = algorithm.celery_task
        
        # Get the task function and launch it
        task_func = current_app.tasks.get(task_name)
        if task_func:
            task = task_func.delay(clustering_run.id)
        else:
            # Fallback to the default clustering task for older algorithms
            task = run_clustering.delay(clustering_run.id)
            
        clustering_run.task_id = task.id
        clustering_run.save()
        
        messages.success(request, f"Clustering run '{name}' created and submitted")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)
    
    context = {
        'segmentations': segmentations,
        'algorithms': algorithms,
    }
    return render(request, 'clustering/create_run.html', context)


@login_required
def clustering_run_detail(request, run_id):
    """Display details of a clustering run."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
    
    # Get clusters if run is completed
    clusters = []
    if clustering_run.status == 'completed':
        clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')
    
    context = {
        'clustering_run': clustering_run,
        'clusters': clusters,
    }
    return render(request, 'clustering/run_detail.html', context)


@login_required
def clustering_run_status(request, run_id):
    """Check the status of a clustering run."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    # Return JSON response with run status
    return JsonResponse({
        'status': clustering_run.status,
        'progress': clustering_run.progress,
        'clusters_created': clustering_run.num_clusters_created,
    })


@login_required
def cluster_explorer(request, run_id):
    """Interactive visualization of clusters for a clustering run."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
    
    # Check if run is completed
    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)
    
    # Get clusters
    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')
    
    context = {
        'clustering_run': clustering_run,
        'clusters': clusters,
    }
    return render(request, 'clustering/cluster_explorer.html', context)


@login_required
def mapping_interface(request, run_id):
    """Interface for mapping clusters to call types."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to view this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
    
    # Check if run is completed
    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)
    
    # Get clusters
    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')
    
    # Get available species
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
    
    # Get existing mappings
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
def export_clusters(request, run_id):
    """Export cluster data as CSV."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
    
    # Check if run is completed
    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)
    
    # Get clusters
    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')
    
    # Get segment memberships
    segment_clusters = SegmentCluster.objects.filter(
        cluster__clustering_run=clustering_run
    ).select_related('segment', 'cluster')
    
    # Create CSV data
    csv_data = "segment_id,segment_onset,segment_offset,cluster_id,cluster_label,confidence\n"
    for sc in segment_clusters:
        segment = sc.segment
        cluster = sc.cluster
        csv_data += f"{segment.id},{segment.onset},{segment.offset},{cluster.cluster_id},"
        csv_data += f"\"{cluster.label or ''}\",{sc.confidence}\n"
    
    # Create HTTP response
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clusters_{run_id}.csv"'
    return response


@login_required
def export_mappings(request, run_id):
    """Export cluster-call mappings as CSV."""
    # Get the clustering run
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)
    
    # Check if user has permission to view this run
    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
        
        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')
    
    # Get mappings
    mappings = ClusterCallMapping.objects.filter(
        cluster__clustering_run=clustering_run
    ).select_related('cluster', 'call', 'call__species')
    
    # Create CSV data
    csv_data = "cluster_id,cluster_label,species_name,call_name,confidence\n"
    for mapping in mappings:
        cluster = mapping.cluster
        call = mapping.call
        csv_data += f"{cluster.cluster_id},\"{cluster.label or ''}\","
        csv_data += f"\"{call.species.name}\",\"{call.short_name}\",{mapping.confidence}\n"
    
    # Create HTTP response
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mappings_{run_id}.csv"'
    return response


@login_required
def get_cluster_data(request):
    """API endpoint to get data for a specific cluster."""
    cluster_id = request.GET.get('cluster_id')
    if not cluster_id:
        return JsonResponse({'status': 'error', 'message': 'No cluster ID provided'})
    
    # Get the cluster
    cluster = get_object_or_404(Cluster, id=cluster_id)
    
    # Check if user has permission to view this cluster
    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this cluster'})
        
        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this cluster'})
    
    # Get mappings for this cluster
    mappings = ClusterCallMapping.objects.filter(cluster=cluster).select_related('call', 'call__species')
    
    # Get spectrogram URL for representative segment
    representative_spectrogram_url = None
    representative_audio_url = None
    if cluster.representative_segment:
        representative_spectrogram_url = reverse('segment_spectrogram', args=[cluster.representative_segment.id])
        representative_audio_url = reverse('segment_audio', args=[cluster.representative_segment.id])
    
    # Create response data
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
    
    # Add mappings
    for mapping in mappings:
        response_data['mappings'].append({
            'id': mapping.id,
            'species_name': mapping.call.species.name,
            'call_name': mapping.call.short_name,
            'confidence': mapping.confidence,
        })
    
    return JsonResponse(response_data)


@login_required
@require_POST
def update_cluster_label(request):
    """API endpoint to update a cluster's label."""
    cluster_id = request.POST.get('cluster_id')
    label = request.POST.get('label')
    description = request.POST.get('description', '')
    
    if not cluster_id:
        return JsonResponse({'status': 'error', 'message': 'No cluster ID provided'})
    
    # Get the cluster
    cluster = get_object_or_404(Cluster, id=cluster_id)
    
    # Check if user has permission to edit this cluster
    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})
        
        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})
    
    # Update the cluster
    cluster.label = label
    cluster.description = description
    cluster.is_labeled = bool(label)
    cluster.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Cluster label updated'
    })


@login_required
@require_POST
def create_cluster_mapping(request):
    """API endpoint to create a new cluster-call mapping."""
    cluster_id = request.POST.get('cluster_id')
    call_id = request.POST.get('call_id')
    confidence = request.POST.get('confidence')
    notes = request.POST.get('notes', '')
    
    if not all([cluster_id, call_id, confidence]):
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
    
    # Get the cluster and call
    cluster = get_object_or_404(Cluster, id=cluster_id)
    call = get_object_or_404(Call, id=call_id)
    
    # Check if user has permission to edit this cluster
    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})
        
        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})
    
    # Check if mapping already exists
    existing_mapping = ClusterCallMapping.objects.filter(cluster=cluster, call=call).first()
    if existing_mapping:
        # Update existing mapping
        existing_mapping.confidence = float(confidence)
        existing_mapping.notes = notes
        existing_mapping.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Mapping updated',
            'mapping_id': existing_mapping.id,
            'call_id': call.id,
            'new_count': ClusterCallMapping.objects.filter(call=call).count()
        })
    
    # Create new mapping
    mapping = ClusterCallMapping.objects.create(
        cluster=cluster,
        call=call,
        confidence=float(confidence),
        notes=notes,
        created_by=request.user
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'Mapping created',
        'mapping_id': mapping.id,
        'call_id': call.id,
        'new_count': ClusterCallMapping.objects.filter(call=call).count()
    })


@login_required
@require_POST
def delete_cluster_mapping(request):
    """API endpoint to delete a cluster-call mapping."""
    mapping_id = request.POST.get('mapping_id')
    
    if not mapping_id:
        return JsonResponse({'status': 'error', 'message': 'No mapping ID provided'})
    
    # Get the mapping
    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)
    
    # Check if user has permission to delete this mapping
    if not request.user.is_staff:
        if mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to delete this mapping'})
        
        if not mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to delete this mapping'})
    
    # Store call ID before deleting
    call_id = mapping.call.id
    
    # Delete the mapping
    mapping.delete()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Mapping deleted',
        'call_id': call_id,
        'new_count': ClusterCallMapping.objects.filter(call_id=call_id).count()
    })


@login_required
@require_POST
def update_mapping_confidence(request):
    """API endpoint to update a mapping's confidence score."""
    mapping_id = request.POST.get('mapping_id')
    confidence = request.POST.get('confidence')
    
    if not all([mapping_id, confidence]):
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
    
    # Get the mapping
    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)
    
    # Check if user has permission to edit this mapping
    if not request.user.is_staff:
        if mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this mapping'})
        
        if not mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this mapping'})
    
    # Update the mapping
    mapping.confidence = float(confidence)
    mapping.save()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Confidence updated'
    })


@login_required
def get_segment_data(request):
    """API endpoint to get data for a specific segment."""
    segment_id = request.GET.get('segment_id')
    
    if not segment_id:
        return JsonResponse({'status': 'error', 'message': 'No segment ID provided'})
    
    # Get the segment
    segment = get_object_or_404(Segment, id=segment_id)
    
    # Check if user has permission to view this segment
    if not request.user.is_staff:
        if segment.recording.group and segment.recording.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this segment'})
        
        if not segment.recording.group and segment.recording.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to view this segment'})
    
    # Create response data
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