"""
Dashboard view for the BattyCoda application.
"""

from datetime import datetime, timedelta

from django.db import models
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .models.classification import ClassificationRun
from .models.organization import Project, Species
from .models import Recording, Segmentation
from .models.task import Task, TaskBatch
from .models.user import GroupInvitation


def index(request):
    """Root URL - show dashboard if logged in, or login page if not"""
    if request.user.is_authenticated:
        profile = request.user.profile
        context = {}

        # Check for pending invitations for this user
        if request.user.email:
            pending_invitations = GroupInvitation.objects.filter(
                email=request.user.email,
                accepted=False,
                expires_at__gt=timezone.now()
            ).select_related('group', 'invited_by')
            context["pending_invitations"] = pending_invitations

        # Section 1: Get projects with tasks
        context["projects_with_tasks"] = _get_projects_with_tasks(profile)

        # Section 2: Get my work statistics
        context["my_stats"] = _get_my_work_stats(request.user, profile)

        # Section 3: Get leaderboard (only if user is in a group)
        if profile.group:
            context["leaderboard"] = _get_leaderboard(profile.group, request.user)

        return render(request, "dashboard.html", context)
    else:
        return redirect("battycoda_app:landing")


def _get_projects_with_tasks(profile):
    """Get projects that have pending tasks"""
    if profile.group:
        projects = Project.objects.filter(group=profile.group)
    else:
        projects = Project.objects.filter(created_by=profile.user)

    projects_with_tasks = []
    for project in projects:
        # Get tasks for this project
        if profile.group:
            tasks = Task.objects.filter(project=project, group=profile.group)
        else:
            tasks = Task.objects.filter(project=project, created_by=profile.user)

        total_tasks = tasks.count()
        if total_tasks == 0:
            continue

        pending_tasks = tasks.filter(is_done=False).count()
        completed_tasks = total_tasks - pending_tasks

        if pending_tasks > 0:  # Only show projects with pending work
            progress_percentage = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

            project.pending_tasks = pending_tasks
            project.completed_tasks = completed_tasks
            project.progress_percentage = progress_percentage
            projects_with_tasks.append(project)

    return projects_with_tasks


def _get_my_work_stats(user, profile):
    """Get user's work statistics"""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Get base query for user's tasks
    if profile.group:
        my_tasks = Task.objects.filter(annotated_by=user, group=profile.group)
    else:
        my_tasks = Task.objects.filter(annotated_by=user)

    # Calculate stats
    today = my_tasks.filter(annotated_at__gte=today_start, is_done=True).count()
    this_week = my_tasks.filter(annotated_at__gte=week_start, is_done=True).count()
    total = my_tasks.filter(is_done=True).count()

    # Calculate streak
    streak = _calculate_streak(user, profile)

    # Get recently worked on batches
    recent_batches_data = my_tasks.filter(
        annotated_at__gte=now - timedelta(days=7),
        batch__isnull=False,
        is_done=True
    ).values('batch').annotate(
        count=Count('id')
    ).order_by('-count')[:5]

    recent_batches = []
    for batch_data in recent_batches_data:
        batch = TaskBatch.objects.select_related('project').get(id=batch_data['batch'])
        recent_batches.append({
            'batch': batch,
            'count': batch_data['count']
        })

    return {
        'today': today,
        'this_week': this_week,
        'total': total,
        'streak': streak,
        'recent_batches': recent_batches
    }


def _calculate_streak(user, profile):
    """Calculate consecutive days of task completion"""
    # Get base query
    if profile.group:
        tasks = Task.objects.filter(annotated_by=user, group=profile.group)
    else:
        tasks = Task.objects.filter(annotated_by=user)

    # Get dates when user completed tasks
    completed_dates = tasks.filter(
        is_done=True,
        annotated_at__isnull=False
    ).values_list('annotated_at', flat=True).order_by('-annotated_at')

    if not completed_dates:
        return 0

    # Convert to date objects and get unique dates
    dates = sorted(set(dt.date() for dt in completed_dates), reverse=True)

    if not dates:
        return 0

    # Check if there's activity today or yesterday (streak is still alive)
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    if dates[0] not in [today, yesterday]:
        return 0  # Streak broken

    # Count consecutive days
    streak = 1
    current_date = dates[0]

    for date in dates[1:]:
        expected_date = current_date - timedelta(days=1)
        if date == expected_date:
            streak += 1
            current_date = date
        else:
            break

    return streak


def _get_leaderboard(group, current_user):
    """Get leaderboard for the group"""
    from django.contrib.auth.models import User

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    # Get all users in the group
    group_users = User.objects.filter(profile__group=group)

    leaderboard = []
    for user in group_users:
        user_tasks = Task.objects.filter(annotated_by=user, group=group)

        today = user_tasks.filter(annotated_at__gte=today_start, is_done=True).count()
        this_week = user_tasks.filter(annotated_at__gte=week_start, is_done=True).count()
        total = user_tasks.filter(is_done=True).count()
        streak = _calculate_streak(user, user.profile)

        leaderboard.append({
            'username': user.username,
            'today': today,
            'this_week': this_week,
            'total': total,
            'streak': streak,
            'is_current_user': user == current_user
        })

    # Sort by total (primary), then by this_week, then by today
    leaderboard.sort(key=lambda x: (x['total'], x['this_week'], x['today']), reverse=True)

    # Add ranks
    for i, entry in enumerate(leaderboard, 1):
        entry['rank'] = i

    return leaderboard
