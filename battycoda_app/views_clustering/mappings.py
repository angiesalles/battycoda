"""Cluster mapping and export operations."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from ..models import Call
from ..models.clustering import (Cluster, ClusterCallMapping, ClusteringRun,
                                 SegmentCluster)


@login_required
def export_clusters(request, run_id):
    """Export cluster data as CSV."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

    if clustering_run.status != 'completed':
        messages.error(request, "Clustering run is not yet completed")
        return redirect('battycoda_app:clustering_run_detail', run_id=clustering_run.id)

    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by('cluster_id')

    segment_clusters = SegmentCluster.objects.filter(
        cluster__clustering_run=clustering_run
    ).select_related('segment', 'cluster')

    csv_data = "segment_id,segment_onset,segment_offset,cluster_id,cluster_label,confidence\n"
    for sc in segment_clusters:
        segment = sc.segment
        cluster = sc.cluster
        csv_data += f"{segment.id},{segment.onset},{segment.offset},{cluster.cluster_id},"
        csv_data += f"\"{cluster.label or ''}\",{sc.confidence}\n"

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clusters_{run_id}.csv"'
    return response


@login_required
def export_mappings(request, run_id):
    """Export cluster-call mappings as CSV."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    if not request.user.is_staff:
        if clustering_run.group and clustering_run.group != request.user.profile.group:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

        if not clustering_run.group and clustering_run.created_by != request.user:
            messages.error(request, "You don't have permission to export this clustering run")
            return redirect('battycoda_app:clustering_dashboard')

    mappings = ClusterCallMapping.objects.filter(
        cluster__clustering_run=clustering_run
    ).select_related('cluster', 'call', 'call__species')

    csv_data = "cluster_id,cluster_label,species_name,call_name,confidence\n"
    for mapping in mappings:
        cluster = mapping.cluster
        call = mapping.call
        csv_data += f"{cluster.cluster_id},\"{cluster.label or ''}\","
        csv_data += f"\"{call.species.name}\",\"{call.short_name}\",{mapping.confidence}\n"

    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mappings_{run_id}.csv"'
    return response


@login_required
@require_POST
def update_cluster_label(request):
    """API endpoint to update a cluster's label."""
    cluster_id = request.POST.get('cluster_id')
    label = request.POST.get('label')
    description = request.POST.get('description', '')

    if not cluster_id:
        return JsonResponse({'status': 'error', 'message': 'No cluster ID provided'})

    cluster = get_object_or_404(Cluster, id=cluster_id)

    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})

        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})

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

    cluster = get_object_or_404(Cluster, id=cluster_id)
    call = get_object_or_404(Call, id=call_id)

    if not request.user.is_staff:
        if cluster.clustering_run.group and cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})

        if not cluster.clustering_run.group and cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this cluster'})

    existing_mapping = ClusterCallMapping.objects.filter(cluster=cluster, call=call).first()
    if existing_mapping:
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

    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)

    if not request.user.is_staff:
        if mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to delete this mapping'})

        if not mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to delete this mapping'})

    call_id = mapping.call.id

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

    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)

    if not request.user.is_staff:
        if mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.group != request.user.profile.group:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this mapping'})

        if not mapping.cluster.clustering_run.group and mapping.cluster.clustering_run.created_by != request.user:
            return JsonResponse({'status': 'error', 'message': 'You don\'t have permission to edit this mapping'})

    mapping.confidence = float(confidence)
    mapping.save()

    return JsonResponse({
        'status': 'success',
        'message': 'Confidence updated'
    })
