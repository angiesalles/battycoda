"""
Views for executing automated segmentation tasks on recordings.
"""
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from battycoda_app.models.recording import Recording, Segment, Segmentation, SegmentationAlgorithm

@login_required
def select_recording_for_segmentation_view(request):
    """Display a page for selecting a recording to segment"""
    # Get user profile
    profile = request.user.profile

    # Filter recordings by group if the user is in a group
    if profile.group:
        if profile.is_current_group_admin:
            # Admin sees all recordings in their group
            recordings = Recording.objects.filter(group=profile.group).order_by("-created_at")
        else:
            # Regular user only sees their own recordings
            recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")
    else:
        # Fallback to showing only user's recordings if no group is assigned
        recordings = Recording.objects.filter(created_by=request.user).order_by("-created_at")

    # Transform recordings to match the generalized template's expected format
    items = []
    for recording in recordings:
        items.append({
            'id': recording.id,
            'name': recording.name,
            'type_name': f"{recording.species.name if recording.species else 'Unknown'} Recording",
            'created_at': recording.created_at,
            'detail_url': reverse('battycoda_app:recording_detail', kwargs={'recording_id': recording.id}),
            'action_url': reverse('battycoda_app:auto_segment_recording', kwargs={'recording_id': recording.id}),
        })

    context = {
        'title': "Select Recording for Segmentation",
        'list_title': "Available Recordings",
        'info_message': "Select a recording to create a new segmentation.",
        'items': items,
        'th1': "Recording Name",
        'th2': "Species",
        'action_text': "Segment This Recording",
        'action_icon': 'cut',
        'parent_url': 'battycoda_app:batch_segmentation',
        'parent_name': 'Segmentation Overview',
        'empty_message': "No recordings available. Upload a recording first.",
        'create_url': 'battycoda_app:create_recording',
    }

    return render(request, "automation/select_entity.html", context)

@login_required
def auto_segment_recording_view(request, recording_id, algorithm_id=None):
    """Run automated segmentation on a recording"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to segment this recording.")
        return redirect("battycoda_app:recording_detail", recording_id=recording_id)

    # Get available algorithms
    if profile.group and profile.is_current_group_admin:
        # Admin sees all algorithms plus group-specific ones
        # First get all global algorithms
        global_query = SegmentationAlgorithm.objects.filter(is_active=True, group__isnull=True)

        # Then get group-specific algorithms
        group_query = SegmentationAlgorithm.objects.filter(is_active=True, group=profile.group)

        # Get all the IDs of both queries
        global_ids = set(global_query.values_list("id", flat=True))
        group_ids = set(group_query.values_list("id", flat=True))

        # Combine the IDs without duplicates
        all_ids = global_ids.union(group_ids)

        # Now get all algorithms with these IDs in a single query
        algorithms = SegmentationAlgorithm.objects.filter(id__in=all_ids).order_by("name")
    else:
        # Regular user sees only global algorithms
        algorithms = SegmentationAlgorithm.objects.filter(is_active=True, group__isnull=True).order_by("name")

    # Get the selected algorithm
    if algorithm_id:
        # Use filter().first() instead of get() to avoid MultipleObjectsReturned error
        algorithm = SegmentationAlgorithm.objects.filter(id=int(algorithm_id), is_active=True).first()
        if not algorithm:
            # Fallback to the first algorithm if specified one not found
            algorithm = algorithms.first()
    else:
        # Use the first available algorithm (usually Standard Threshold)
        algorithm = algorithms.first()

    # Check for existing segmentations, but we no longer need to warn since we support multiple segmentations
    # Get the count of existing segmentations for information purposes
    existing_segmentations_count = Segmentation.objects.filter(recording=recording).count()
    existing_segmentation = None

    if request.method == "POST":
        # Log the POST data for debugging

        # Get parameters from request
        algorithm_id = request.POST.get("algorithm")

        min_duration_ms = request.POST.get("min_duration_ms", 10)
        smooth_window = request.POST.get("smooth_window", 3)
        threshold_factor = request.POST.get("threshold_factor", 0.5)

        # Get the algorithm by ID if specified
        if algorithm_id:
            try:
                # Debug logs

                # Use filter().first() instead of get() to avoid MultipleObjectsReturned error
                algorithm = SegmentationAlgorithm.objects.filter(id=int(algorithm_id), is_active=True).first()
                if not algorithm:
                    messages.error(request, f"Segmentation algorithm with ID {algorithm_id} not found.")
                    return redirect("battycoda_app:auto_segment_recording", recording_id=recording_id)

            except Exception as e:

                messages.error(request, f"Error selecting algorithm: {str(e)}")
                return redirect("battycoda_app:auto_segment_recording", recording_id=recording_id)

            # Check if user has access to this algorithm
            if algorithm.group and (not profile.group or algorithm.group != profile.group):
                messages.error(request, "You don't have permission to use this algorithm.")
                return redirect("battycoda_app:auto_segment_recording", recording_id=recording_id)
        else:
            # No algorithm selected - select the first algorithm as default
            algorithm = algorithms.first()
            if not algorithm:
                messages.error(request, "No segmentation algorithm was selected and no default algorithm is available.")
                return redirect("battycoda_app:auto_segment_recording", recording_id=recording_id)

        # Extract bandpass filter parameters
        low_freq = request.POST.get("low_freq")
        high_freq = request.POST.get("high_freq")
        
        # Convert to appropriate types
        try:
            min_duration_ms = int(min_duration_ms)
            smooth_window = int(smooth_window)
            threshold_factor = float(threshold_factor)
            
            # Convert frequency parameters to integers or None
            if low_freq and low_freq.strip():
                low_freq = int(low_freq)
            else:
                low_freq = None
                
            if high_freq and high_freq.strip():
                high_freq = int(high_freq)
            else:
                high_freq = None

            # Validate parameters
            if min_duration_ms < 1:
                raise ValueError("Minimum duration must be at least 1ms")
            if smooth_window < 1:
                raise ValueError("Smooth window must be at least 1 sample")
            if threshold_factor <= 0 or threshold_factor > 10:
                raise ValueError("Threshold factor must be between 0 and 10")
        except ValueError as e:
            messages.error(request, f"Invalid parameter: {str(e)}")
            return redirect("battycoda_app:segment_recording", recording_id=recording_id)

        # Start the segmentation task
        try:
            from celery import current_app


            # Create a Segmentation entry first to track this job
            segmentation = Segmentation.objects.create(
                recording=recording,
                name=f"{algorithm.name}",
                created_by=request.user,
                algorithm=algorithm,
                task_id="pending",  # Will be updated with actual task ID
                status="in_progress",
                progress=0,
                is_active=True,
                manually_edited=False,
            )

            # Launch Celery task with segmentation_id as the first parameter
            task = current_app.send_task(
                algorithm.celery_task,
                args=[recording.id, segmentation.id, min_duration_ms, smooth_window, threshold_factor, low_freq, high_freq],
            )
            
            # Update the segmentation with the actual task ID
            segmentation.task_id = task.id
            segmentation.save(update_fields=['task_id'])

            # Store task ID in session for status checking
            request.session[f"auto_segment_task_{recording_id}"] = task.id

            # Delete any existing segments for this recording
            with transaction.atomic():
                # Delete existing segments
                existing_count = Segment.objects.filter(recording=recording).count()
                if existing_count > 0:

                    Segment.objects.filter(recording=recording).delete()

                # Mark all existing segmentations as inactive
                Segmentation.objects.filter(recording=recording, is_active=True).update(is_active=False)
                
                # The segmentation was already created before launching the task

            # Set success message
            messages.success(
                request,
                f"Automated segmentation started using {algorithm.name}. This may take a few moments to complete.",
            )

            # Redirect to segmentation batch overview
            return redirect("battycoda_app:batch_segmentation")

        except Exception as e:

            # Set error message
            messages.error(request, f"Error starting segmentation: {str(e)}")

            # Redirect back to the auto segment form
            return redirect("battycoda_app:auto_segment_recording", recording_id=recording_id)

    # GET request - display form for configuring segmentation or return JSON if AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # Return JSON with algorithm details for AJAX requests
        if algorithm:
            return JsonResponse(
                {
                    "success": True,
                    "algorithm_id": algorithm.id,
                    "algorithm_name": algorithm.name,
                    "algorithm_description": algorithm.description,
                    "algorithm_type": algorithm.get_algorithm_type_display(),
                    "min_duration_ms": algorithm.default_min_duration_ms,
                    "smooth_window": algorithm.default_smooth_window,
                    "threshold_factor": algorithm.default_threshold_factor,
                }
            )
        else:
            return JsonResponse({"success": False, "error": "Algorithm not found"}, status=404)

    # Regular GET request - render the form
    context = {
        "recording": recording,
        "algorithms": algorithms,
        "selected_algorithm": algorithm,
        "min_duration_ms": algorithm.default_min_duration_ms if algorithm else 10,
        "smooth_window": algorithm.default_smooth_window if algorithm else 3,
        "threshold_factor": algorithm.default_threshold_factor if algorithm else 0.5,
        "existing_segmentation": existing_segmentation,
    }

    return render(request, "recordings/auto_segment.html", context)

@login_required
def auto_segment_status_view(request, recording_id):
    """Check the status of an auto-segmentation task"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    # Get task ID from session
    task_id = request.session.get(f"auto_segment_task_{recording_id}")

    if not task_id:
        # Try to get the segmentation from the database instead
        from ..models import Segmentation

        segmentation = Segmentation.objects.filter(recording_id=recording_id).first()

        if segmentation and segmentation.task_id:
            task_id = segmentation.task_id
        else:
            return JsonResponse(
                {"success": False, "status": "not_found", "message": "No active segmentation task found"}
            )

    try:
        from celery.result import AsyncResult

        from ..models import Segmentation

        # Get the segmentation from database
        segmentation = Segmentation.objects.filter(task_id=task_id).first()

        # Get task result
        result = AsyncResult(task_id)

        if result.ready():
            # Task is complete
            if result.successful():
                # Get result data
                task_result = result.get()

                # Success with segments
                if task_result.get("status") == "success":
                    segments_created = task_result.get("segments_created", 0)
                    message = f"Successfully created {segments_created} segments."

                    # Update segmentation status
                    if segmentation:
                        segmentation.status = "completed"
                        segmentation.progress = 100
                        segmentation.save()

                    # Clear task ID from session
                    if f"auto_segment_task_{recording_id}" in request.session:
                        del request.session[f"auto_segment_task_{recording_id}"]

                    # Prepare response with basic information
                    response_data = {
                        "success": True,
                        "status": "completed",
                        "message": message,
                        "segments_created": segments_created,
                        "result": task_result,
                    }


                    return JsonResponse(response_data)
                else:
                    # Task returned error status
                    error_message = task_result.get("message", "Unknown error in segmentation task")

                    # Update segmentation status
                    if segmentation:
                        segmentation.status = "failed"
                        segmentation.save()

                    # Clear task ID from session
                    if f"auto_segment_task_{recording_id}" in request.session:
                        del request.session[f"auto_segment_task_{recording_id}"]

                    return JsonResponse({"success": False, "status": "failed", "message": error_message})
            else:
                # Task failed with exception
                error_info = str(result.result)

                # Update segmentation status
                if segmentation:
                    segmentation.status = "failed"
                    segmentation.save()

                # Clear task ID from session
                if f"auto_segment_task_{recording_id}" in request.session:
                    del request.session[f"auto_segment_task_{recording_id}"]

                return JsonResponse(
                    {"success": False, "status": "failed", "message": f"Segmentation task failed: {error_info}"}
                )
        else:
            # Task is still running
            # Update segmentation status if it exists
            if segmentation and segmentation.status != "in_progress":
                segmentation.status = "in_progress"
                segmentation.save()

            return JsonResponse(
                {"success": True, "status": "in_progress", "message": "Segmentation is still processing..."}
            )

    except Exception as e:

        return JsonResponse({"success": False, "status": "error", "message": f"Error checking task status: {str(e)}"})
