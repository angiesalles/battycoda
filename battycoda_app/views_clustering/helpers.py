"""Helper functions for clustering views."""

from ..models.clustering import ClusteringAlgorithm


def get_available_algorithms(user):
    """
    Get all clustering algorithms available to a user.

    Returns algorithms owned by the user's group plus global algorithms (no group).
    For users without a group, returns algorithms they created plus global ones.
    """
    group = user.profile.group

    if group:
        user_algorithms = ClusteringAlgorithm.objects.filter(is_active=True, group=group).order_by("name")
    else:
        user_algorithms = ClusteringAlgorithm.objects.filter(is_active=True, created_by=user).order_by("name")

    # Add global algorithms (those without a group) that aren't already included
    user_algorithm_ids = [a.id for a in user_algorithms]
    global_algorithms = ClusteringAlgorithm.objects.filter(
        is_active=True, group__isnull=True
    ).exclude(id__in=user_algorithm_ids)

    return list(user_algorithms) + list(global_algorithms)
