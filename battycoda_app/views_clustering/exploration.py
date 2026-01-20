"""Cluster exploration and visualization views."""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import Segment
from ..models.clustering import Cluster, ClusterCallMapping, ClusteringRun, SegmentCluster
from ..models.organization import Species
from ..utils_modules.validation import get_int_param
from .permissions import check_clustering_permission


@login_required
def cluster_explorer(request, run_id):
    """Interactive visualization of clusters for a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to view this clustering run"
    )
    if error:
        return error

    if clustering_run.status != "completed":
        messages.error(request, "Clustering run is not yet completed")
        return redirect("battycoda_app:clustering_run_detail", run_id=clustering_run.id)

    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by("cluster_id")

    # Serialize clusters for JavaScript (used by json_script template tag)
    clusters_json = [
        {
            "id": cluster.id,
            "cluster_id": cluster.cluster_id,
            "label": cluster.label or "",
            "description": cluster.description or "",
            "is_labeled": cluster.is_labeled,
            "size": cluster.size,
            "coherence": float(cluster.coherence) if cluster.coherence else 0,
            "vis_x": float(cluster.vis_x) if cluster.vis_x else 0,
            "vis_y": float(cluster.vis_y) if cluster.vis_y else 0,
        }
        for cluster in clusters
    ]

    context = {
        "clustering_run": clustering_run,
        "clusters": clusters,
        "clusters_json": clusters_json,
        "is_project_scope": clustering_run.scope == "project",
    }
    return render(request, "clustering/cluster_explorer.html", context)


@login_required
def mapping_interface(request, run_id):
    """Interface for mapping clusters to call types."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to view this clustering run"
    )
    if error:
        return error

    if clustering_run.status != "completed":
        messages.error(request, "Clustering run is not yet completed")
        return redirect("battycoda_app:clustering_run_detail", run_id=clustering_run.id)

    clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by("cluster_id")

    if clustering_run.group:
        available_species = Species.objects.filter(
            models.Q(is_system=True) | models.Q(group=clustering_run.group)
        ).order_by("name")
    else:
        available_species = Species.objects.filter(
            models.Q(is_system=True) | models.Q(created_by=request.user, group__isnull=True)
        ).order_by("name")

    existing_mappings = ClusterCallMapping.objects.filter(cluster__clustering_run=clustering_run).order_by(
        "-confidence"
    )

    # Serialize existing mappings for JavaScript (used by json_script template tag)
    existing_mappings_json = json.dumps(
        [
            {
                "id": m.id,
                "clusterId": m.cluster.id,
                "callId": m.call.id,
                "confidence": float(m.confidence),
                "speciesName": m.call.species.name,
                "callName": m.call.short_name,
            }
            for m in existing_mappings.select_related("cluster", "call", "call__species")
        ]
    )

    context = {
        "clustering_run": clustering_run,
        "clusters": clusters,
        "available_species": available_species,
        "existing_mappings": existing_mappings,
        "existing_mappings_json": existing_mappings_json,
    }
    return render(request, "clustering/mapping_interface.html", context)


@login_required
def get_cluster_data(request):
    """API endpoint to get data for a specific cluster."""
    cluster_id = request.GET.get("cluster_id")
    if not cluster_id:
        return JsonResponse({"success": False, "error": "No cluster ID provided"})

    cluster = get_object_or_404(Cluster, id=cluster_id)

    error = check_clustering_permission(
        request, cluster, json_response=True, error_message="You don't have permission to view this cluster"
    )
    if error:
        return error

    mappings = ClusterCallMapping.objects.filter(cluster=cluster).select_related("call", "call__species")

    representative_spectrogram_url = None
    representative_audio_url = None
    if cluster.representative_segment:
        representative_spectrogram_url = reverse("segment_spectrogram", args=[cluster.representative_segment.id])
        representative_audio_url = reverse("segment_audio", args=[cluster.representative_segment.id])

    response_data = {
        "success": True,
        "cluster_id": cluster.cluster_id,
        "label": cluster.label,
        "description": cluster.description,
        "is_labeled": cluster.is_labeled,
        "size": cluster.size,
        "coherence": cluster.coherence,
        "representative_spectrogram_url": representative_spectrogram_url,
        "representative_audio_url": representative_audio_url,
        "mappings": [],
    }

    for mapping in mappings:
        response_data["mappings"].append(
            {
                "id": mapping.id,
                "species_name": mapping.call.species.name,
                "call_name": mapping.call.short_name,
                "confidence": mapping.confidence,
            }
        )

    return JsonResponse(response_data)


@login_required
def get_segment_data(request):
    """API endpoint to get data for a specific segment."""
    segment_id = request.GET.get("segment_id")

    if not segment_id:
        return JsonResponse({"success": False, "error": "No segment ID provided"})

    segment = get_object_or_404(Segment, id=segment_id)

    error = check_clustering_permission(
        request, segment, json_response=True, error_message="You don't have permission to view this segment"
    )
    if error:
        return error

    response_data = {
        "success": True,
        "segment_id": segment.id,
        "recording_id": segment.recording.id,
        "recording_name": segment.recording.name,
        "onset": segment.onset,
        "offset": segment.offset,
        "duration": segment.offset - segment.onset,
        "spectrogram_url": reverse("segment_spectrogram", args=[segment.id]),
        "audio_url": reverse("segment_audio", args=[segment.id]),
    }

    return JsonResponse(response_data)


@login_required
def get_cluster_members(request):
    """API endpoint to get members of a cluster."""
    cluster_id = request.GET.get("cluster_id")
    limit = get_int_param(request, "limit", default=50, min_val=1, max_val=1000)
    offset = get_int_param(request, "offset", default=0, min_val=0)

    if not cluster_id:
        return JsonResponse({"success": False, "error": "No cluster ID provided"})

    cluster = get_object_or_404(Cluster, id=cluster_id)

    error = check_clustering_permission(
        request, cluster, json_response=True, error_message="You don't have permission to view this cluster"
    )
    if error:
        return error

    # Get the segment clusters with related data
    segment_clusters = (
        SegmentCluster.objects.filter(cluster=cluster)
        .select_related("segment", "segment__segmentation__recording")
        .order_by("segment__onset")[offset : offset + limit]
    )

    is_project_scope = cluster.clustering_run.scope == "project"

    members = []
    for sc in segment_clusters:
        segment = sc.segment
        member_data = {
            "segment_id": segment.id,
            "onset": float(segment.onset),
            "offset": float(segment.offset),
            "duration": float(segment.offset - segment.onset),
            "confidence": float(sc.confidence) if sc.confidence else None,
        }
        if is_project_scope and segment.segmentation:
            recording = segment.segmentation.recording
            member_data["recording_id"] = recording.id
            member_data["recording_name"] = recording.name
        members.append(member_data)

    return JsonResponse(
        {
            "success": True,
            "cluster_id": cluster.cluster_id,
            "total_size": cluster.size,
            "is_project_scope": is_project_scope,
            "members": members,
            "has_more": (offset + limit) < cluster.size,
        }
    )
