"""
Views for importing segments from external data sources.
"""
import os
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from battycoda_app.audio.utils import process_pickle_file
from battycoda_app.models.recording import Recording, Segment, Segmentation

@login_required
def upload_pickle_segments_view(request, recording_id):
    """Upload a pickle file to create segments for a recording"""
    recording = get_object_or_404(Recording, id=recording_id)

    # Check permission
    profile = request.user.profile
    if recording.created_by != request.user and (not profile.group or recording.group != profile.group):
        messages.error(request, "You don't have permission to add segments to this recording.")
        return redirect("battycoda_app:recording_detail", recording_id=recording.id)

    # Check for existing segmentations (but no need to warn now that we support multiple segmentations)
    existing_segmentations = Segmentation.objects.filter(recording=recording)

    # Set up context for GET requests
    if request.method == "GET":
        context = {
            "recording": recording,
            "has_existing_segmentation": existing_segmentations.exists(),
        }
        return render(request, "recordings/upload_pickle.html", context)

    # Handle POST requests
    if request.method == "POST" and request.FILES.get("pickle_file"):
        pickle_file = request.FILES["pickle_file"]

        try:
            # Process the pickle file
            onsets, offsets = process_pickle_file(pickle_file)

            # Create segments from the onset/offset pairs
            segments_created = 0
            with transaction.atomic():
                # Create a new Segmentation entry first
                segmentation = Segmentation.objects.create(
                    recording=recording,
                    name="Pickle Import",
                    algorithm=None,  # No algorithm for manual upload
                    status="completed",
                    progress=100,
                    manually_edited=False,
                    created_by=request.user,
                )

                # We no longer need to delete existing segments since we support multiple segmentations
                # Just counting for logging purposes
                existing_count = Segment.objects.filter(recording=recording).count()

                # Create new segments
                for i in range(len(onsets)):
                    try:
                        # Create segment name
                        segment_name = f"Segment {i+1}"

                        # Create and save the segment
                        segment = Segment(
                            recording=recording,
                            segmentation=segmentation,  # Link to the new segmentation
                            name=segment_name,
                            onset=onsets[i],
                            offset=offsets[i],
                            created_by=request.user,
                        )
                        segment.save(manual_edit=False)  # Don't mark as manually edited for pickle uploads
                        segments_created += 1
                    except Exception as e:

                        raise  # Re-raise to trigger transaction rollback

            # Return appropriate response based on request type
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Successfully created {segments_created} segments.",
                        "redirect_url": reverse(
                            "battycoda_app:segment_recording", kwargs={"recording_id": recording.id}
                        ),
                    }
                )

            messages.success(request, f"Successfully created {segments_created} segments from pickle file.")
            return redirect("battycoda_app:segment_recording", recording_id=recording.id)

        except Exception as e:
            # Log the error with filename for troubleshooting
            import logging
            pickle_filename = pickle_file.name if hasattr(pickle_file, 'name') else 'unknown'
            logging.error(f"Error processing pickle file '{pickle_filename}': {str(e)}")

            # Return appropriate error response
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": str(e)})

            messages.error(request, f"Error processing pickle file '{os.path.basename(pickle_filename)}': {str(e)}")
            return redirect("battycoda_app:segment_recording", recording_id=recording.id)

    # GET request - render upload form
    context = {
        "recording": recording,
    }

    return render(request, "recordings/upload_pickle.html", context)
