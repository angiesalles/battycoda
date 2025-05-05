"""
Views for detecting and managing duplicate recordings.
"""
import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render

from .models.recording import Recording
from .views_common import *

@login_required
def detect_duplicate_recordings_view(request):
    """Show list of duplicate recordings for review"""
    # Check if user is an admin
    profile = request.user.profile
    if not profile.is_admin:
        messages.error(request, "Only administrators can perform this action.")
        return redirect("battycoda_app:recording_list")
    
    # Get user's group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to perform this action.")
        return redirect("battycoda_app:recording_list")
    
    # Get all recordings in the group
    recordings = Recording.objects.filter(group=profile.group)
    
    # Find duplicates based on recording name and duration
    # First, we'll group them by name and duration and count occurrences
    duplicate_groups = (
        recordings.exclude(duration__isnull=True)  # Skip recordings without duration
        .values('name', 'duration')  # Group by name and duration
        .annotate(count=Count('id'))  # Count occurrences
        .filter(count__gt=1)  # Keep only groups with more than one recording
    )
    
    # Get the actual recording objects for each duplicate group
    duplicate_recordings = []
    for group in duplicate_groups:
        recordings_in_group = Recording.objects.filter(
            group=profile.group,
            name=group['name'],
            duration=group['duration']
        ).order_by('-created_at')  # Most recent first
        
        duplicate_recordings.append({
            'name': group['name'],
            'duration': group['duration'],
            'count': group['count'],
            'recordings': recordings_in_group
        })
    
    context = {
        'duplicate_recordings': duplicate_recordings,
        'total_duplicate_count': sum(group['count'] - 1 for group in duplicate_groups)
    }
    
    return render(request, "recordings/duplicate_recordings.html", context)

@login_required
def remove_duplicate_recordings(request):
    """Remove duplicate recordings, keeping only the most recent version"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect("battycoda_app:recording_list")
    
    # Check if user is an admin
    profile = request.user.profile
    if not profile.is_admin:
        messages.error(request, "Only administrators can perform this action.")
        return redirect("battycoda_app:recording_list")
    
    # Get user's group
    if not profile.group:
        messages.error(request, "You must be assigned to a group to perform this action.")
        return redirect("battycoda_app:recording_list")
    
    # Find duplicate recordings
    # Get duplicate groups
    duplicate_groups = (
        Recording.objects.filter(group=profile.group)
        .exclude(duration__isnull=True)  # Skip recordings without duration
        .values('name', 'duration')  # Group by name and duration
        .annotate(count=Count('id'))  # Count occurrences
        .filter(count__gt=1)  # Keep only groups with more than one recording
    )
    
    # Track statistics
    removed_count = 0
    segments_removed = 0
    tasks_removed = 0
    total_groups = 0
    
    # Process each duplicate group
    for group in duplicate_groups:
        total_groups += 1
        
        # Get recordings in this group, ordered by created date (most recent first)
        recordings_in_group = Recording.objects.filter(
            group=profile.group, 
            name=group['name'],
            duration=group['duration']
        ).order_by('-created_at')
        
        # Keep the most recent recording, delete the rest
        # Note: we use a list slice to skip the first item (most recent)
        for recording in list(recordings_in_group)[1:]:
            try:
                # Count segments for reporting purposes
                segment_count = recording.segments.count()
                segments_removed += segment_count
                
                # Count tasks associated with this recording's segments
                from .models.task import Task
                task_count = Task.objects.filter(source_segment__recording=recording).count()
                tasks_removed += task_count
                
                # Delete the recording (will cascade delete segmentations, segments, etc.)
                recording.delete()
                removed_count += 1
                
            except Exception as e:
                # Log the error but continue with other recordings
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error removing duplicate recording {recording.id}: {str(e)}")
    
    if removed_count > 0:
        message = f"Successfully removed {removed_count} duplicate recordings from {total_groups} groups."
        if segments_removed > 0:
            message += f" {segments_removed} segments were also removed."
        if tasks_removed > 0:
            message += f" {tasks_removed} associated tasks were affected."
        messages.success(request, message)
    else:
        messages.info(request, "No duplicate recordings were removed.")
    
    return redirect("battycoda_app:recording_list")

def has_duplicate_recordings(group):
    """Check if a group has any duplicate recordings"""
    duplicates_exist = Recording.objects.filter(group=group) \
        .exclude(duration__isnull=True) \
        .values('name', 'duration') \
        .annotate(count=Count('id')) \
        .filter(count__gt=1) \
        .exists()
    
    return duplicates_exist