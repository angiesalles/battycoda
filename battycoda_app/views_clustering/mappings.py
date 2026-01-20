"""Cluster mapping and export operations."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from ..models import Call
from ..models.clustering import Cluster, ClusterCallMapping, ClusteringRun, SegmentCluster
from .permissions import check_clustering_permission


def _generate_clusters_csv(clustering_run):
    """Generator for streaming cluster CSV data."""
    is_project_scope = clustering_run.scope == "project"

    # Yield header
    if is_project_scope:
        yield "segment_id,recording_id,recording_name,segment_onset,segment_offset,cluster_id,cluster_label,confidence\n"
    else:
        yield "segment_id,segment_onset,segment_offset,cluster_id,cluster_label,confidence\n"

    # Stream data in chunks using iterator() for memory efficiency
    segment_clusters = (
        SegmentCluster.objects.filter(cluster__clustering_run=clustering_run)
        .select_related("segment", "segment__segmentation__recording", "cluster")
        .iterator(chunk_size=1000)
    )

    for sc in segment_clusters:
        segment = sc.segment
        cluster = sc.cluster
        if is_project_scope:
            recording = segment.segmentation.recording if segment.segmentation else None
            recording_id = recording.id if recording else ""
            recording_name = recording.name if recording else ""
            yield f'{segment.id},{recording_id},"{recording_name}",'
            yield f"{segment.onset},{segment.offset},{cluster.cluster_id},"
            yield f'"{cluster.label}",{sc.confidence}\n'
        else:
            yield f"{segment.id},{segment.onset},{segment.offset},{cluster.cluster_id},"
            yield f'"{cluster.label}",{sc.confidence}\n'


@login_required
def export_clusters(request, run_id):
    """Export cluster data as streaming CSV."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to export this clustering run"
    )
    if error:
        return error

    if clustering_run.status != "completed":
        messages.error(request, "Clustering run is not yet completed")
        return redirect("battycoda_app:clustering_run_detail", run_id=clustering_run.id)

    response = StreamingHttpResponse(_generate_clusters_csv(clustering_run), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="clusters_{run_id}.csv"'
    return response


def _generate_mappings_csv(clustering_run):
    """Generator for streaming mappings CSV data."""
    yield "cluster_id,cluster_label,species_name,call_name,confidence\n"

    mappings = (
        ClusterCallMapping.objects.filter(cluster__clustering_run=clustering_run)
        .select_related("cluster", "call", "call__species")
        .iterator(chunk_size=500)
    )

    for mapping in mappings:
        cluster = mapping.cluster
        call = mapping.call
        yield f'{cluster.cluster_id},"{cluster.label}",'
        yield f'"{call.species.name}","{call.short_name}",{mapping.confidence}\n'


@login_required
def export_mappings(request, run_id):
    """Export cluster-call mappings as streaming CSV."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to export this clustering run"
    )
    if error:
        return error

    response = StreamingHttpResponse(_generate_mappings_csv(clustering_run), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="mappings_{run_id}.csv"'
    return response


@login_required
@require_POST
def update_cluster_label(request):
    """API endpoint to update a cluster's label."""
    cluster_id = request.POST.get("cluster_id")
    label = request.POST.get("label")
    description = request.POST.get("description", "")

    if not cluster_id:
        return JsonResponse({"success": False, "error": "No cluster ID provided"})

    cluster = get_object_or_404(Cluster, id=cluster_id)

    error = check_clustering_permission(
        request, cluster, json_response=True, error_message="You don't have permission to edit this cluster"
    )
    if error:
        return error

    cluster.label = label
    cluster.description = description
    cluster.is_labeled = bool(label)
    cluster.save()

    return JsonResponse({"success": True, "message": "Cluster label updated"})


@login_required
@require_POST
def create_cluster_mapping(request):
    """API endpoint to create a new cluster-call mapping."""
    cluster_id = request.POST.get("cluster_id")
    call_id = request.POST.get("call_id")
    confidence = request.POST.get("confidence")
    notes = request.POST.get("notes", "")

    if not all([cluster_id, call_id, confidence]):
        return JsonResponse({"success": False, "error": "Missing required fields"})

    cluster = get_object_or_404(Cluster, id=cluster_id)
    call = get_object_or_404(Call, id=call_id)

    error = check_clustering_permission(
        request, cluster, json_response=True, error_message="You don't have permission to edit this cluster"
    )
    if error:
        return error

    existing_mapping = ClusterCallMapping.objects.filter(cluster=cluster, call=call).first()
    if existing_mapping:
        existing_mapping.confidence = float(confidence)
        existing_mapping.notes = notes
        existing_mapping.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Mapping updated",
                "mapping_id": existing_mapping.id,
                "call_id": call.id,
                "new_count": ClusterCallMapping.objects.filter(call=call).count(),
            }
        )

    mapping = ClusterCallMapping.objects.create(
        cluster=cluster, call=call, confidence=float(confidence), notes=notes, created_by=request.user
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Mapping created",
            "mapping_id": mapping.id,
            "call_id": call.id,
            "new_count": ClusterCallMapping.objects.filter(call=call).count(),
        }
    )


@login_required
@require_POST
def delete_cluster_mapping(request):
    """API endpoint to delete a cluster-call mapping."""
    mapping_id = request.POST.get("mapping_id")

    if not mapping_id:
        return JsonResponse({"success": False, "error": "No mapping ID provided"})

    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)

    error = check_clustering_permission(
        request, mapping, json_response=True, error_message="You don't have permission to delete this mapping"
    )
    if error:
        return error

    call_id = mapping.call.id

    mapping.delete()

    return JsonResponse(
        {
            "success": True,
            "message": "Mapping deleted",
            "call_id": call_id,
            "new_count": ClusterCallMapping.objects.filter(call_id=call_id).count(),
        }
    )


@login_required
@require_POST
def update_mapping_confidence(request):
    """API endpoint to update a mapping's confidence score."""
    mapping_id = request.POST.get("mapping_id")
    confidence = request.POST.get("confidence")

    if not all([mapping_id, confidence]):
        return JsonResponse({"success": False, "error": "Missing required fields"})

    mapping = get_object_or_404(ClusterCallMapping, id=mapping_id)

    error = check_clustering_permission(
        request, mapping, json_response=True, error_message="You don't have permission to edit this mapping"
    )
    if error:
        return error

    mapping.confidence = float(confidence)
    mapping.save()

    return JsonResponse({"success": True, "message": "Confidence updated"})
