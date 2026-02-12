"""
TUS resumable upload protocol endpoint.

Implements the core TUS v1.0.0 protocol (creation, offset retrieval, patching)
plus the creation-with-upload and termination extensions.

Reference: https://tus.io/protocols/resumable-upload
"""

import base64
import json
import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .audio.modules.file_utils import AudioFileError
from .audio.utils import get_audio_duration, split_audio_file
from .models.organization import Project, Species
from .models.recording import Recording
from .models.tus_upload import TusUpload
from .models.user import UserProfile
from .utils_modules.cleanup import safe_remove_file

logger = logging.getLogger(__name__)

TUS_VERSION = "1.0.0"
TUS_EXTENSIONS = "creation,termination,creation-with-upload"


def _tus_headers(extra=None):
    """Return common TUS response headers."""
    headers = {
        "Tus-Resumable": TUS_VERSION,
        "Tus-Version": TUS_VERSION,
        "Tus-Extension": TUS_EXTENSIONS,
        "Tus-Max-Size": str(settings.TUS_MAX_SIZE),
    }
    if extra:
        headers.update(extra)
    return headers


def _set_headers(response, headers):
    """Apply a dict of headers to an HttpResponse."""
    for key, value in headers.items():
        response[key] = value
    return response


def _parse_metadata(header_value):
    """Parse TUS Upload-Metadata header into a dict.

    Format: key base64value, key base64value, ...
    Values are optional (key-only entries are stored as empty string).
    """
    result = {}
    if not header_value:
        return result
    for pair in header_value.split(","):
        pair = pair.strip()
        if not pair:
            continue
        parts = pair.split(None, 1)
        key = parts[0]
        if len(parts) == 2:
            try:
                result[key] = base64.b64decode(parts[1]).decode("utf-8")
            except Exception:
                result[key] = parts[1]
        else:
            result[key] = ""
    return result


def _error(status, message):
    """Return a JSON error response with TUS headers."""
    resp = JsonResponse({"error": message}, status=status)
    return _set_headers(resp, _tus_headers())


def _finalize_upload(tus_upload):
    """Convert a completed TUS upload into one or more Recording objects.

    Mirrors the logic in create_recording_view for consistency.
    """
    meta = tus_upload.metadata_json or {}
    user = tus_upload.user
    group = tus_upload.group

    # Resolve foreign keys
    try:
        species = Species.objects.get(id=int(meta.get("species_id", 0)))
    except (Species.DoesNotExist, ValueError, TypeError):
        logger.error(f"TUS finalize: invalid species_id in upload {tus_upload.upload_id}")
        safe_remove_file(tus_upload.temp_file_path, "TUS temp file")
        tus_upload.delete()
        return None

    try:
        project = Project.objects.get(id=int(meta.get("project_id", 0)))
    except (Project.DoesNotExist, ValueError, TypeError):
        logger.error(f"TUS finalize: invalid project_id in upload {tus_upload.upload_id}")
        safe_remove_file(tus_upload.temp_file_path, "TUS temp file")
        tus_upload.delete()
        return None

    recording_name = meta.get("name") or tus_upload.filename or "Untitled"
    description = meta.get("description", "")
    recorded_date = meta.get("recorded_date") or None
    location = meta.get("location", "")
    equipment = meta.get("equipment", "")
    environmental_conditions = meta.get("environmental_conditions", "")
    split_long_files = meta.get("split_long_files", "true").lower() in ("true", "on", "1")

    temp_path = tus_upload.temp_file_path
    recordings_created = []

    try:
        if split_long_files:
            try:
                duration = get_audio_duration(temp_path)
                if duration > 60:
                    chunk_paths = split_audio_file(temp_path, chunk_duration_seconds=60)
                    for i, chunk_path in enumerate(chunk_paths):
                        with open(chunk_path, "rb") as f:
                            django_file = SimpleUploadedFile(
                                os.path.basename(chunk_path), f.read(), content_type="audio/wav"
                            )
                            recording = Recording(
                                name=f"{recording_name} (Part {i + 1}/{len(chunk_paths)})",
                                wav_file=django_file,
                                description=description,
                                recorded_date=recorded_date,
                                location=location,
                                equipment=equipment,
                                environmental_conditions=environmental_conditions,
                                species=species,
                                project=project,
                                created_by=user,
                                group=group,
                            )
                            recording.save()
                            recording.file_ready = True
                            recording.save(update_fields=["file_ready"])
                            recordings_created.append(recording)

                    # Clean up chunks
                    for chunk_path in chunk_paths:
                        safe_remove_file(chunk_path, "audio chunk file")

                    safe_remove_file(temp_path, "TUS temp file")
                    tus_upload.delete()
                    return recordings_created
            except (IOError, OSError, AudioFileError) as e:
                logger.debug(f"TUS finalize: split not possible, normal processing: {e}")

        # Single recording (no split, or split failed, or file <= 60s)
        with open(temp_path, "rb") as f:
            django_file = SimpleUploadedFile(tus_upload.filename or "upload.wav", f.read(), content_type="audio/wav")
            recording = Recording(
                name=recording_name,
                wav_file=django_file,
                description=description,
                recorded_date=recorded_date,
                location=location,
                equipment=equipment,
                environmental_conditions=environmental_conditions,
                species=species,
                project=project,
                created_by=user,
                group=group,
            )
            recording.save()
            recording.file_ready = True
            recording.save(update_fields=["file_ready"])
            recordings_created.append(recording)

    finally:
        safe_remove_file(temp_path, "TUS temp file")
        # Delete TusUpload record if it still exists
        try:
            tus_upload.delete()
        except Exception:
            pass

    return recordings_created


@csrf_exempt
@login_required
def tus_upload_view(request, upload_id=None):
    """Main TUS protocol dispatcher."""
    method = request.method

    if method == "OPTIONS":
        return _handle_options(request)
    elif method == "POST" and upload_id is None:
        return _handle_create(request)
    elif method == "HEAD" and upload_id is not None:
        return _handle_head(request, upload_id)
    elif method == "PATCH" and upload_id is not None:
        return _handle_patch(request, upload_id)
    elif method == "DELETE" and upload_id is not None:
        return _handle_delete(request, upload_id)
    else:
        return _error(405, "Method not allowed")


def _handle_options(request):
    """Return TUS server capabilities."""
    resp = HttpResponse(status=204)
    return _set_headers(resp, _tus_headers())


def _handle_create(request):
    """POST /tus/ — create a new upload."""
    # Validate Upload-Length header
    try:
        upload_length = int(request.META.get("HTTP_UPLOAD_LENGTH", ""))
    except (ValueError, TypeError):
        return _error(400, "Missing or invalid Upload-Length header")

    if upload_length > settings.TUS_MAX_SIZE:
        return _error(413, f"Upload exceeds maximum size of {settings.TUS_MAX_SIZE} bytes")

    if upload_length < 0:
        return _error(400, "Upload-Length must be non-negative")

    # Parse metadata
    metadata = _parse_metadata(request.META.get("HTTP_UPLOAD_METADATA", ""))
    filename = metadata.get("filename", "upload.wav")
    content_type = metadata.get("content_type", "audio/wav")

    # Extract recording metadata from TUS metadata
    recording_meta = {}
    for key in ("name", "species_id", "project_id", "description", "recorded_date",
                "location", "equipment", "environmental_conditions", "split_long_files"):
        if key in metadata:
            recording_meta[key] = metadata[key]

    # Get user profile/group
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    group = profile.group

    # Create temp file
    upload_uuid = uuid.uuid4()
    temp_file_path = os.path.join(settings.TUS_UPLOAD_DIR, f"{upload_uuid}.part")

    # Create empty temp file
    with open(temp_file_path, "wb") as f:
        pass  # empty file

    tus_upload = TusUpload.objects.create(
        upload_id=upload_uuid,
        upload_length=upload_length,
        upload_offset=0,
        temp_file_path=temp_file_path,
        filename=filename,
        content_type=content_type,
        metadata_json=recording_meta,
        user=request.user,
        group=group,
    )

    # Build Location URL
    location = request.build_absolute_uri(
        reverse("battycoda_app:tus_upload_chunk", kwargs={"upload_id": tus_upload.upload_id})
    )

    # Handle creation-with-upload: if body has data and correct content-type
    initial_offset = 0
    req_content_type = request.content_type or ""
    if "application/offset+octet-stream" in req_content_type and request.body and len(request.body) > 0:
        body = request.body
        with open(temp_file_path, "ab") as f:
            f.write(body)
        initial_offset = len(body)
        tus_upload.upload_offset = initial_offset
        if initial_offset >= upload_length:
            tus_upload.is_complete = True
        tus_upload.save(update_fields=["upload_offset", "is_complete"])

    resp = HttpResponse(status=201)
    _set_headers(resp, _tus_headers({
        "Location": location,
        "Upload-Offset": str(initial_offset),
    }))

    # If upload completed in one shot, finalize
    if tus_upload.is_complete:
        result = _finalize_upload(tus_upload)
        if result:
            # Return redirect info in a custom header
            if len(result) == 1:
                resp["X-Recording-Id"] = str(result[0].id)
                resp["X-Redirect-Url"] = reverse(
                    "battycoda_app:recording_detail", kwargs={"recording_id": result[0].id}
                )
            else:
                resp["X-Redirect-Url"] = reverse("battycoda_app:recording_list")

    return resp


def _handle_head(request, upload_id):
    """HEAD /tus/<uuid> — return current offset for resumption."""
    try:
        tus_upload = TusUpload.objects.get(upload_id=upload_id, user=request.user)
    except TusUpload.DoesNotExist:
        return _error(404, "Upload not found")

    resp = HttpResponse(status=200)
    _set_headers(resp, _tus_headers({
        "Upload-Offset": str(tus_upload.upload_offset),
        "Upload-Length": str(tus_upload.upload_length),
        "Cache-Control": "no-store",
    }))
    return resp


def _handle_patch(request, upload_id):
    """PATCH /tus/<uuid> — append a chunk."""
    # Content-Type must be application/offset+octet-stream
    content_type = request.content_type or ""
    if "application/offset+octet-stream" not in content_type:
        return _error(415, "Content-Type must be application/offset+octet-stream")

    # Validate Upload-Offset header
    try:
        client_offset = int(request.META.get("HTTP_UPLOAD_OFFSET", ""))
    except (ValueError, TypeError):
        return _error(400, "Missing or invalid Upload-Offset header")

    # Use select_for_update to prevent race conditions
    try:
        tus_upload = TusUpload.objects.select_for_update().get(upload_id=upload_id, user=request.user)
    except TusUpload.DoesNotExist:
        return _error(404, "Upload not found")

    # Offset conflict check
    if client_offset != tus_upload.upload_offset:
        return _error(409, f"Offset mismatch: server at {tus_upload.upload_offset}, client sent {client_offset}")

    # Read chunk from request body
    chunk = request.body
    if not chunk:
        return _error(400, "Empty request body")

    # Verify chunk doesn't exceed remaining space
    if tus_upload.upload_offset + len(chunk) > tus_upload.upload_length:
        return _error(413, "Chunk exceeds declared upload length")

    # Append chunk to temp file
    try:
        with open(tus_upload.temp_file_path, "ab") as f:
            f.write(chunk)
    except OSError as e:
        logger.error(f"TUS: failed to write chunk for {upload_id}: {e}")
        return _error(500, "Failed to write chunk")

    # Update offset
    tus_upload.upload_offset += len(chunk)
    is_complete = tus_upload.upload_offset >= tus_upload.upload_length
    tus_upload.is_complete = is_complete
    tus_upload.save(update_fields=["upload_offset", "is_complete", "updated_at"])

    resp = HttpResponse(status=204)
    headers = {
        "Upload-Offset": str(tus_upload.upload_offset),
    }

    if is_complete:
        result = _finalize_upload(tus_upload)
        if result:
            if len(result) == 1:
                headers["X-Recording-Id"] = str(result[0].id)
                headers["X-Redirect-Url"] = reverse(
                    "battycoda_app:recording_detail", kwargs={"recording_id": result[0].id}
                )
            else:
                headers["X-Redirect-Url"] = reverse("battycoda_app:recording_list")
        else:
            return _error(500, "Upload completed but recording creation failed")

    _set_headers(resp, _tus_headers(headers))
    return resp


def _handle_delete(request, upload_id):
    """DELETE /tus/<uuid> — cancel and remove an upload."""
    try:
        tus_upload = TusUpload.objects.get(upload_id=upload_id, user=request.user)
    except TusUpload.DoesNotExist:
        return _error(404, "Upload not found")

    safe_remove_file(tus_upload.temp_file_path, "TUS temp file")
    tus_upload.delete()

    resp = HttpResponse(status=204)
    return _set_headers(resp, _tus_headers())
