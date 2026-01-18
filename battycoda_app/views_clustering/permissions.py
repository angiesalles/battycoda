"""Permission checking utilities for clustering views.

Centralizes the repeated permission check pattern:
    if not request.user.is_staff:
        if obj.group and obj.group != request.user.profile.group:
            return error_response
        if not obj.group and obj.created_by != request.user:
            return error_response

This module provides helper functions that handle various clustering-related
objects (ClusteringRun, Cluster, ClusterCallMapping, Segment) and response
types (HTML redirect vs JSON).
"""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


def _get_group_and_creator(obj):
    """Extract group and created_by from various clustering-related objects.

    Handles:
    - ClusteringRun: direct .group, .created_by
    - Cluster: .clustering_run.group, .clustering_run.created_by
    - ClusterCallMapping: .cluster.clustering_run.group, .cluster.clustering_run.created_by
    - Segment: .recording.group, .recording.created_by

    Returns:
        tuple: (group, created_by) - either may be None
    """
    # Check for direct group attribute first (ClusteringRun, Project, etc.)
    # This must come before checking for 'recording' because ClusteringRun
    # has a 'recording' property that can return None
    if hasattr(obj, "group") and hasattr(obj, "created_by"):
        return obj.group, obj.created_by

    # Cluster - via clustering_run
    if hasattr(obj, "clustering_run"):
        return obj.clustering_run.group, obj.clustering_run.created_by

    # ClusterCallMapping - via cluster.clustering_run
    if hasattr(obj, "cluster") and hasattr(obj.cluster, "clustering_run"):
        return obj.cluster.clustering_run.group, obj.cluster.clustering_run.created_by

    # Segment - via recording
    if hasattr(obj, "recording") and obj.recording is not None:
        return obj.recording.group, obj.recording.created_by

    raise ValueError(f"Cannot determine group/creator for object type: {type(obj).__name__}")


def has_clustering_permission(user, obj):
    """Check if user has permission to access a clustering-related object.

    Staff users always have permission.
    Non-staff users have permission if:
    - The object's group matches their profile group, OR
    - The object has no group and they created it

    Args:
        user: The request.user object
        obj: A clustering-related object (ClusteringRun, Cluster, etc.)

    Returns:
        bool: True if user has permission, False otherwise
    """
    if user.is_staff:
        return True

    group, created_by = _get_group_and_creator(obj)
    user_group = user.profile.group

    if group:
        return group == user_group
    else:
        return created_by == user


def check_clustering_permission(
    request,
    obj,
    *,
    json_response=False,
    error_message="Permission denied",
    redirect_url="battycoda_app:clustering_dashboard",
    status_code=403,
):
    """Check clustering permission and return error response if denied.

    This is the main function to use in views. It checks permission and
    returns an appropriate error response if denied.

    Args:
        request: The Django request object
        obj: A clustering-related object to check permission for
        json_response: If True, return JsonResponse; if False, return redirect
        error_message: The error message to display
        redirect_url: URL name to redirect to (only used if json_response=False)
        status_code: HTTP status code for JSON responses (default 403)

    Returns:
        None if user has permission
        HttpResponse if permission denied (JsonResponse or redirect)

    Example usage:
        clustering_run = get_object_or_404(ClusteringRun, id=run_id)

        error = check_clustering_permission(
            request, clustering_run,
            error_message="You don't have permission to view this clustering run"
        )
        if error:
            return error

        # ... rest of view logic
    """
    if has_clustering_permission(request.user, obj):
        return None

    if json_response:
        return JsonResponse({"status": "error", "message": error_message}, status=status_code)

    messages.error(request, error_message)
    return redirect(redirect_url)
