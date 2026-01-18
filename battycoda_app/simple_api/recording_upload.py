"""
Recording upload API views.
Handles WAV file uploads with optional pickle segmentation data.
"""

import logging
import os
import tempfile
from datetime import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..audio.utils import get_audio_duration, process_pickle_file, split_audio_file
from ..models import Project, Recording, Segment, Segmentation
from ..models.organization import Species
from ..utils_modules.cleanup import safe_cleanup_dir, safe_remove_file
from ..utils_modules.validation import safe_int
from .auth import api_key_required

logger = logging.getLogger(__name__)


def _get_species_for_user(species_id, user):
    """
    Look up species by ID with access control.
    Returns (species, error_response) - error_response is None on success.
    """
    user_group = user.profile.group

    try:
        if user_group:
            # User has a group - can access group species AND system species
            return Species.objects.get(Q(id=species_id) & (Q(group=user_group) | Q(group__isnull=True))), None
        else:
            # User has no group - can access their own species AND system species
            return Species.objects.get(Q(id=species_id) & (Q(created_by=user) | Q(group__isnull=True))), None
    except Species.DoesNotExist:
        return None, JsonResponse(
            {"success": False, "error": f"Species with ID {species_id} not found or not accessible"}, status=400
        )


def _get_project_for_user(project_id, user):
    """
    Look up project by ID with access control.
    Returns (project, error_response) - error_response is None on success.
    """
    try:
        project_id = int(project_id)
        return Project.objects.get(id=project_id, group=user.profile.group), None
    except (ValueError, Project.DoesNotExist):
        return None, JsonResponse(
            {"success": False, "error": f"Project with ID {project_id} not found or not accessible"}, status=400
        )


def _parse_recorded_date(date_string):
    """
    Parse a date string in YYYY-MM-DD format.
    Returns (date, error_response) - error_response is None on success.
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date(), None
    except ValueError:
        return None, JsonResponse({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}, status=400)


def _create_split_recordings(chunk_paths, name, description, location, parsed_date, species, project, user):
    """
    Create multiple recordings from audio chunks.
    Returns list of created Recording objects.
    """
    recordings_created = []

    for i, chunk_path in enumerate(chunk_paths):
        with open(chunk_path, "rb") as chunk_file:
            chunk_name = f"{name} (Part {i + 1}/{len(chunk_paths)})"
            chunk_django_file = SimpleUploadedFile(
                os.path.basename(chunk_path), chunk_file.read(), content_type="audio/wav"
            )

            with transaction.atomic():
                recording = Recording.objects.create(
                    name=chunk_name,
                    description=description,
                    wav_file=chunk_django_file,
                    location=location,
                    recorded_date=parsed_date,
                    species=species,
                    project=project,
                    group=user.profile.group,
                    created_by=user,
                    file_ready=True,
                )
                recordings_created.append(recording)

    # Clean up chunk files
    for chunk_path in chunk_paths:
        safe_remove_file(chunk_path, "audio chunk file")
        safe_cleanup_dir(os.path.dirname(chunk_path), "chunk directory")

    return recordings_created


def _process_pickle_segmentation(pickle_file, recording, user):
    """
    Process a pickle file containing segmentation data.
    Returns segmentation info dict or error dict.
    """
    try:
        # Reset file pointer to beginning
        pickle_file.seek(0)

        # Process the pickle file to extract onsets and offsets
        onsets, offsets = process_pickle_file(pickle_file)

        # Create a new segmentation
        segmentation = Segmentation.objects.create(
            recording=recording,
            name="API Upload Segmentation",
            algorithm=None,  # Manual/imported segmentation
            status="completed",
            created_by=user,
            segments_created=len(onsets),
        )

        # Create individual segments
        segments_created = 0
        for i, (onset, offset) in enumerate(zip(onsets, offsets)):
            Segment.objects.create(
                recording=recording,
                segmentation=segmentation,
                name=f"Segment {i + 1}",
                onset=float(onset),
                offset=float(offset),
                created_by=user,
            )
            segments_created += 1

        # Update segments count
        segmentation.segments_created = segments_created
        segmentation.save()

        return {
            "id": segmentation.id,
            "name": segmentation.name,
            "segments_count": segments_created,
            "created_at": segmentation.created_at.isoformat(),
        }

    except Exception as pickle_error:
        return {"error": f"Pickle file processing failed: {str(pickle_error)}"}


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required
def upload_recording(request):
    """Upload a WAV recording with optional pickle segmentation data."""
    user = request.api_user

    # Check if user has a group
    if not user.profile.group:
        return JsonResponse(
            {"success": False, "error": "User must be assigned to a group to upload recordings"}, status=400
        )

    try:
        # Get and validate required fields
        name = request.POST.get("name")
        species_id = request.POST.get("species_id")
        wav_file = request.FILES.get("wav_file")
        pickle_file = request.FILES.get("pickle_file")  # Optional segmentation data

        if not all([name, species_id, wav_file]):
            return JsonResponse(
                {"success": False, "error": "Missing required fields: name, species_id, wav_file"}, status=400
            )

        species_id = safe_int(species_id)
        if species_id is None:
            return JsonResponse({"success": False, "error": "species_id must be a valid integer"}, status=400)

        # Get optional fields
        description = request.POST.get("description", "")
        location = request.POST.get("location", "")
        project_id = request.POST.get("project_id")
        recorded_date = request.POST.get("recorded_date")  # YYYY-MM-DD format

        # Validate species
        species, error = _get_species_for_user(species_id, user)
        if error:
            return error

        # Validate project if provided
        project = None
        if project_id:
            project, error = _get_project_for_user(project_id, user)
            if error:
                return error

        # Parse date if provided
        parsed_date = None
        if recorded_date:
            parsed_date, error = _parse_recorded_date(recorded_date)
            if error:
                return error

        # Save uploaded file to temporary location to check duration
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            for chunk in wav_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            duration = get_audio_duration(temp_file_path)

            # If duration > 60 seconds, split into 1-minute chunks
            if duration > 60:
                chunk_paths = split_audio_file(temp_file_path, chunk_duration_seconds=60)
                recordings_created = _create_split_recordings(
                    chunk_paths, name, description, location, parsed_date, species, project, user
                )

                return JsonResponse(
                    {
                        "success": True,
                        "split": True,
                        "original_duration": duration,
                        "chunks_created": len(recordings_created),
                        "recordings": [
                            {"id": rec.id, "name": rec.name, "created_at": rec.created_at.isoformat()}
                            for rec in recordings_created
                        ],
                    }
                )

            # File is ≤ 60 seconds, create single recording
            wav_file.seek(0)

            with transaction.atomic():
                recording = Recording.objects.create(
                    name=name,
                    description=description,
                    wav_file=wav_file,
                    location=location,
                    recorded_date=parsed_date,
                    species=species,
                    project=project,
                    group=user.profile.group,
                    created_by=user,
                    file_ready=True,
                )

            # Process pickle file if provided
            segmentation_info = None
            if pickle_file:
                segmentation_info = _process_pickle_segmentation(pickle_file, recording, user)

            # Build response
            response_data = {
                "success": True,
                "split": False,
                "recording": {
                    "id": recording.id,
                    "name": recording.name,
                    "duration": recording.duration,
                    "species_name": recording.species.name,
                    "project_name": recording.project.name if recording.project else None,
                    "created_at": recording.created_at.isoformat(),
                },
            }

            if segmentation_info:
                response_data["segmentation"] = segmentation_info

            return JsonResponse(response_data)

        finally:
            safe_remove_file(temp_file_path, "temporary upload file")

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Upload failed: {str(e)}"}, status=500)
