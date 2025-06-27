"""Detail views for detection runs.

Provides views for displaying detailed information about detection runs.
"""

import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from battycoda_app.models.detection import CallProbability, DetectionResult, DetectionRun
from battycoda_app.models.organization import Call

@login_required
def detection_run_detail_view(request, run_id):
    """Display details of a specific classification run."""
    # Get the detection run by ID
    run = get_object_or_404(DetectionRun, id=run_id)

    # Check if the user has permission to view this run
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to view this classification run.")
        return redirect("battycoda_app:automation_home")

    # Get results with segment ordering
    results_query = DetectionResult.objects.filter(detection_run=run).order_by("segment__onset")

    # Get all call types for this species to use as table headers
    call_types = Call.objects.filter(species=run.segmentation.recording.species).order_by("short_name")

    # Add pagination
    page_size = 50  # Show 50 results per page
    paginator = Paginator(results_query, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Prepare the data for rendering
    results_with_probabilities = []
    for result in page_obj:
        # Get all probabilities for this result
        probabilities = CallProbability.objects.filter(detection_result=result)

        # Create a dictionary mapping call type ID to probability
        prob_dict = {prob.call_id: prob.probability for prob in probabilities}

        # For each call type, get the probability (or default to 0)
        call_probs = []
        for call in call_types:
            call_probs.append({"call": call, "probability": prob_dict.get(call.id, 0.0)})

        # Add to results
        results_with_probabilities.append({"result": result, "segment": result.segment, "probabilities": call_probs})

    context = {
        "run": run,
        "call_types": call_types,
        "results": results_with_probabilities,
        "page_obj": page_obj,
        "paginator": paginator,
    }

    return render(request, "automation/run_detail.html", context)

@login_required
def detection_run_status_view(request, run_id):
    """AJAX view for checking status of a detection run."""
    # Get the detection run by ID
    run = get_object_or_404(DetectionRun, id=run_id)

    # Check if the user has permission to view this run
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    # Return the status
    return JsonResponse(
        {
            "success": True,
            "status": run.status,
            "progress": run.progress,
            "error": run.error_message,
        }
    )

@login_required
def download_features_file_view(request, run_id):
    """Download the features CSV file for a detection run."""
    # Get the detection run by ID
    run = get_object_or_404(DetectionRun, id=run_id)

    # Check if the user has permission to view this run
    profile = request.user.profile
    if run.created_by != request.user and (not profile.group or run.group != profile.group):
        messages.error(request, "You don't have permission to access this classification run.")
        return redirect("battycoda_app:automation_home")

    # Check if features file exists
    if not run.features_file:
        messages.error(request, "No features file available for this run.")
        return redirect("battycoda_app:detection_run_detail", run_id=run_id)
    
    # Check if file exists on disk
    if not os.path.exists(run.features_file):
        messages.error(request, "Features file not found on disk.")
        return redirect("battycoda_app:detection_run_detail", run_id=run_id)
    
    # Generate a user-friendly filename
    filename = f"features_{run.name}_{run.id}.csv"
    # Remove any problematic characters from filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    
    # Return the file as a download
    try:
        response = FileResponse(
            open(run.features_file, 'rb'),
            as_attachment=True,
            filename=filename,
            content_type='text/csv'
        )
        return response
    except Exception as e:
        messages.error(request, f"Error downloading features file: {str(e)}")
        return redirect("battycoda_app:detection_run_detail", run_id=run_id)
