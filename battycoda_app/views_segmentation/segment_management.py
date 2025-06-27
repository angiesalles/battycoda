"""
Views for managing individual recording segments (CRUD operations).
"""
import json
import os
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from battycoda_app.forms import SegmentForm
from battycoda_app.models.recording import Recording, Segment, Segmentation
from battycoda_app.models.spectrogram import SpectrogramJob


def get_spectrogram_status(recording):
    """
    Get comprehensive spectrogram status for a recording.
    
    Returns:
        dict: Contains 'status', 'url', 'job', 'progress' information
    """
    try:
        # Hash the recording file path for cache key
        file_hash = hashlib.md5(recording.wav_file.path.encode()).hexdigest()
        spectrogram_path = os.path.join(settings.MEDIA_ROOT, "spectrograms", "recordings", f"{file_hash}.png")
        
        # Check if spectrogram file already exists
        if os.path.exists(spectrogram_path) and os.path.getsize(spectrogram_path) > 0:
            return {
                'status': 'available',
                'url': f"/media/spectrograms/recordings/{file_hash}.png",
                'job': None,
                'progress': 100
            }
        
        # Check for existing jobs
        active_job = SpectrogramJob.objects.filter(
            recording=recording,
            status__in=['pending', 'in_progress']
        ).first()
        
        if active_job:
            return {
                'status': 'generating',
                'url': None,
                'job': active_job,
                'progress': active_job.progress
            }
        
        # Check for completed jobs with file
        completed_job = SpectrogramJob.objects.filter(
            recording=recording,
            status='completed'
        ).order_by('-created_at').first()
        
        if completed_job and completed_job.output_file_path and os.path.exists(completed_job.output_file_path):
            # Extract the relative URL from the full path
            relative_path = completed_job.output_file_path.replace(settings.MEDIA_ROOT, '').lstrip('/')
            return {
                'status': 'available',
                'url': f"/media/{relative_path}",
                'job': completed_job,
                'progress': 100
            }
        
        # No spectrogram available, no active jobs
        return {
            'status': 'not_available',
            'url': None,
            'job': None,
            'progress': 0
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'url': None,
            'job': None,
            'progress': 0,
            'error': str(e)
        }


@login_required
def segment_recording_view(request, recording_id):
    """View for segmenting a recording (marking regions)"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission to edit this recording
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to segment this recording.")
        return redirect("battycoda_app:recording_list")

    # Check if a specific segmentation ID is requested in the query parameters
    requested_segmentation_id = request.GET.get('segmentation_id')
    
    if requested_segmentation_id:
        try:
            # Try to get the requested segmentation
            requested_segmentation = Segmentation.objects.get(id=requested_segmentation_id, recording=recording)
            
            # Automatically make it active
            if not requested_segmentation.is_active:
                # Deactivate all other segmentations for this recording
                Segmentation.objects.filter(recording=recording).update(is_active=False)
                
                # Activate the requested one
                requested_segmentation.is_active = True
                requested_segmentation.save()
                
            # Use this segmentation
            active_segmentation = requested_segmentation
            segments_queryset = Segment.objects.filter(segmentation=active_segmentation).order_by("onset")
            
            # Add segmentation info to context
            segmentation_info = {
                "id": active_segmentation.id,
                "name": active_segmentation.name,
                "algorithm": active_segmentation.algorithm.name if active_segmentation.algorithm else "Manual",
                "created_at": active_segmentation.created_at,
                "manually_edited": active_segmentation.manually_edited,
            }
        except Segmentation.DoesNotExist:
            # If the requested segmentation doesn't exist, fall back to the active one
            return redirect("battycoda_app:segment_recording", recording_id=recording.id)
    else:
        # No specific segmentation requested, use the active one
        try:
            active_segmentation = Segmentation.objects.get(recording=recording, is_active=True)

            # Get segments from the active segmentation
            segments_queryset = Segment.objects.filter(segmentation=active_segmentation).order_by("onset")

            # Add segmentation info to context
            segmentation_info = {
                "id": active_segmentation.id,
                "name": active_segmentation.name,
                "algorithm": active_segmentation.algorithm.name if active_segmentation.algorithm else "Manual",
                "created_at": active_segmentation.created_at,
                "manually_edited": active_segmentation.manually_edited,
            }
        except Segmentation.DoesNotExist:
            # No active segmentation, return empty queryset
            segments_queryset = Segment.objects.none()
            segmentation_info = None

            # Check if there are any segmentations at all
            if Segmentation.objects.filter(recording=recording).exists():
                # Activate the most recent segmentation
                latest_segmentation = Segmentation.objects.filter(recording=recording).order_by("-created_at").first()
                latest_segmentation.is_active = True
                latest_segmentation.save()

                # Redirect to refresh the page with the newly activated segmentation
                return redirect("battycoda_app:segment_recording", recording_id=recording.id)

    # Apply filters if provided
    min_duration = request.GET.get('min_duration')
    max_duration = request.GET.get('max_duration')
    search_id = request.GET.get('search_id')
    
    if min_duration:
        try:
            min_duration = float(min_duration)
            # Filter by duration (offset - onset)
            segments_queryset = segments_queryset.extra(
                where=["(offset - onset) >= %s"],
                params=[min_duration]
            )
        except ValueError:
            pass
    
    if max_duration:
        try:
            max_duration = float(max_duration)
            segments_queryset = segments_queryset.extra(
                where=["(offset - onset) <= %s"],
                params=[max_duration]
            )
        except ValueError:
            pass
    
    if search_id:
        try:
            search_id = int(search_id)
            segments_queryset = segments_queryset.filter(id=search_id)
        except ValueError:
            pass

    # Set up pagination for segments - 50 segments per page for reasonable performance
    paginator = Paginator(segments_queryset, 50)
    page = request.GET.get('page')
    
    try:
        segments = paginator.page(page)
    except PageNotAnInteger:
        segments = paginator.page(1)
    except EmptyPage:
        segments = paginator.page(paginator.num_pages)

    # Check spectrogram status and jobs
    spectrogram_info = get_spectrogram_status(recording)
    spectrogram_url = spectrogram_info.get('url')

    # For waveform display, only load first 200 segments to avoid performance issues
    # Additional segments will be loaded dynamically via AJAX as needed
    initial_segments_for_waveform = segments_queryset[:200]
    segments_json = []
    for segment in initial_segments_for_waveform:
        segments_json.append({"id": segment.id, "onset": segment.onset, "offset": segment.offset})

    # Get total segment count for context
    total_segments_count = segments_queryset.count()

    # Get all segmentations for the dropdown
    all_segmentations = Segmentation.objects.filter(recording=recording).order_by("-created_at")

    context = {
        "recording": recording,
        "segments": segments,
        "segments_json": json.dumps(segments_json),
        "total_segments_count": total_segments_count,
        "spectrogram_url": spectrogram_url,
        "spectrogram_info": spectrogram_info,
        "active_segmentation": segmentation_info,
        "all_segmentations": all_segmentations,
        "filter_values": {
            "min_duration": request.GET.get('min_duration', ''),
            "max_duration": request.GET.get('max_duration', ''),
            "search_id": request.GET.get('search_id', ''),
        },
    }

    return render(request, "recordings/segment_recording.html", context)

@login_required
def add_segment_view(request, recording_id):
    """Add a segment to a recording via AJAX"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check if the user has permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = SegmentForm(request.POST, recording=recording)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.recording = recording
            segment.created_by = request.user
            segment.save(manual_edit=True)  # Mark as manually edited

            return JsonResponse(
                {
                    "success": True,
                    "segment": {
                        "id": segment.id,
                        "name": segment.name or f"Segment {segment.id}",
                        "onset": segment.onset,
                        "offset": segment.offset,
                        "duration": segment.duration(),  # Call the method instead of using it as a property
                        "notes": segment.notes or "",
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

@login_required
def edit_segment_view(request, segment_id):
    """Edit a segment via AJAX"""
    segment = get_object_or_404(Segment, id=segment_id)
    recording = segment.recording

    # Check if the user has permission
    profile = request.user.profile
    if segment.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        form = SegmentForm(request.POST, instance=segment, recording=recording)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.save(manual_edit=True)  # Mark as manually edited

            return JsonResponse(
                {
                    "success": True,
                    "segment": {
                        "id": segment.id,
                        "name": segment.name or f"Segment {segment.id}",
                        "onset": segment.onset,
                        "offset": segment.offset,
                        "duration": segment.duration(),  # Call the method instead of using it as a property
                        "notes": segment.notes or "",
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

@login_required
def delete_segment_view(request, segment_id):
    """Delete a segment via AJAX"""
    segment = get_object_or_404(Segment, id=segment_id)
    recording = segment.recording

    # Check if the user has permission
    profile = request.user.profile
    if segment.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    if request.method == "POST":
        # Get the segmentation to mark as manually edited
        segmentation = segment.segmentation
        if segmentation:
            segmentation.manually_edited = True
            segmentation.save()

        segment_id = segment.id
        segment.delete()
        return JsonResponse({"success": True, "segment_id": segment_id})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)