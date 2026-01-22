"""
Views for managing long-running background jobs in BattyCoda.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from battycoda_app.models import Segmentation
from battycoda_app.models.classification import ClassificationRun, ClassifierTrainingJob
from battycoda_app.models.clustering import ClusteringRun
from battycoda_app.models.spectrogram import SpectrogramJob


def job_status_api_view(request):
    """API endpoint to get the status of multiple jobs"""
    profile = request.user.profile

    # Get all active (non-completed) jobs
    jobs_status = {
        "segmentation_jobs": [],
        "classification_jobs": [],
        "training_jobs": [],
        "clustering_jobs": [],
        "spectrogram_jobs": [],
    }

    if profile.group:
        # Filter jobs by user permissions
        if profile.is_current_group_admin:
            # Admin sees all group jobs
            segmentations = Segmentation.objects.filter(
                recording__group=profile.group,
                recording__hidden=False,  # Exclude hidden recordings
                status__in=["pending", "in_progress"],
            )
            classification_runs = ClassificationRun.objects.filter(group=profile.group, status__in=["pending", "running"])
            training_jobs = ClassifierTrainingJob.objects.filter(group=profile.group, status__in=["pending", "running"])
            clustering_runs = ClusteringRun.objects.filter(group=profile.group, status__in=["pending", "running"])

            spectrogram_jobs = SpectrogramJob.objects.filter(
                recording__group=profile.group, status__in=["pending", "in_progress"]
            )
        else:
            # Regular user sees only their own jobs
            segmentations = Segmentation.objects.filter(
                created_by=request.user,
                recording__hidden=False,  # Exclude hidden recordings
                status__in=["pending", "in_progress"],
            )
            classification_runs = ClassificationRun.objects.filter(
                created_by=request.user, status__in=["pending", "running"]
            )
            training_jobs = ClassifierTrainingJob.objects.filter(
                created_by=request.user, status__in=["pending", "running"]
            )
            clustering_runs = ClusteringRun.objects.filter(created_by=request.user, status__in=["pending", "running"])

            spectrogram_jobs = SpectrogramJob.objects.filter(
                created_by=request.user, status__in=["pending", "in_progress"]
            )

        # Format segmentation jobs
        for seg in segmentations:
            jobs_status["segmentation_jobs"].append(
                {
                    "id": seg.id,
                    "name": f"Segmentation: {seg.recording.name}",
                    "status": seg.status,
                    "created_at": seg.created_at.isoformat(),
                    "progress": seg.progress if hasattr(seg, "progress") else None,
                    "url": f"/recordings/{seg.recording.id}/",
                }
            )

        # Format classification jobs
        for run in classification_runs:
            jobs_status["classification_jobs"].append(
                {
                    "id": run.id,
                    "name": f"Classification: {run.name}",
                    "status": run.status,
                    "created_at": run.created_at.isoformat(),
                    "progress": run.progress if hasattr(run, "progress") else None,
                    "url": f"/classification/runs/{run.id}/",
                }
            )

        # Format training jobs
        for job in training_jobs:
            jobs_status["training_jobs"].append(
                {
                    "id": job.id,
                    "name": f"Training: {job.name}",
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "progress": job.progress if hasattr(job, "progress") else None,
                    "url": f"/classification/classifiers/{job.id}/",
                }
            )

        # Format clustering jobs
        for run in clustering_runs:
            jobs_status["clustering_jobs"].append(
                {
                    "id": run.id,
                    "name": f"Clustering: {run.name}",
                    "status": run.status,
                    "created_at": run.created_at.isoformat(),
                    "progress": run.progress if hasattr(run, "progress") else None,
                    "url": f"/clustering/run/{run.id}/",
                }
            )

        # Format spectrogram jobs
        for job in spectrogram_jobs:
            jobs_status["spectrogram_jobs"].append(
                {
                    "id": job.id,
                    "name": f"Spectrogram: {job.recording.name}",
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "progress": job.progress,
                    "url": f"/recordings/{job.recording.id}/",
                }
            )

    return JsonResponse(jobs_status)


@login_required
def cancel_job_view(request, job_type, job_id):
    """Cancel a specific job"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"})

    profile = request.user.profile

    try:
        # Get the job based on type and ID
        if job_type == "segmentation":
            job = Segmentation.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.recording.group == profile.group
            ):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Cancel the job if possible
            if job.status in ["pending", "in_progress"]:
                job.status = "cancelled"
                job.save()
                return JsonResponse({"success": True, "message": "Segmentation job cancelled"})

        elif job_type == "classification":
            job = ClassificationRun.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (profile.is_current_group_admin and job.group == profile.group):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Cancel the job if possible
            if job.status in ["pending", "running"]:
                job.status = "cancelled"
                job.save()
                return JsonResponse({"success": True, "message": "Classification job cancelled"})

        elif job_type == "training":
            job = ClassifierTrainingJob.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (profile.is_current_group_admin and job.group == profile.group):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Cancel the job if possible
            if job.status in ["pending", "running"]:
                job.status = "cancelled"
                job.save()
                return JsonResponse({"success": True, "message": "Training job cancelled"})

        elif job_type == "clustering":
            job = ClusteringRun.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (profile.is_current_group_admin and job.group == profile.group):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Cancel the job if possible
            if job.status in ["pending", "running"]:
                job.status = "cancelled"
                job.save()
                return JsonResponse({"success": True, "message": "Clustering job cancelled"})

        elif job_type == "spectrogram":
            job = SpectrogramJob.objects.get(id=job_id)
            # Check permissions
            if job.created_by != request.user and not (
                profile.is_current_group_admin and job.recording.group == profile.group
            ):
                return JsonResponse({"success": False, "error": "Permission denied"})

            # Cancel the job if possible
            if job.status in ["pending", "in_progress"]:
                job.status = "cancelled"
                job.save()
                return JsonResponse({"success": True, "message": "Spectrogram job cancelled"})

        else:
            return JsonResponse({"success": False, "error": "Invalid job type"})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Job not found or cannot be cancelled"})
