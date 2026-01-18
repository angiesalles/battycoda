"""Clustering run management views."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Project, Segmentation, Species
from ..models.clustering import Cluster, ClusteringAlgorithm, ClusteringRun
from ..models.segmentation import Segment
from .permissions import check_clustering_permission


@login_required
def dashboard(request):
    """Display a list of clustering runs for the user's group."""
    group = request.user.profile.group

    if group:
        clustering_runs = ClusteringRun.objects.filter(group=group).order_by("-created_at")
    else:
        clustering_runs = ClusteringRun.objects.filter(created_by=request.user).order_by("-created_at")

    if group:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(group=group).order_by("name")
    else:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(created_by=request.user).order_by("name")

    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(is_active=True, group__isnull=True).exclude(
            id__in=[a.id for a in algorithms]
        )
    )

    context = {
        "clustering_runs": clustering_runs,
        "algorithms": algorithms,
    }
    return render(request, "clustering/dashboard.html", context)


@login_required
def create_clustering_run(request):
    """Form for creating a new clustering run."""
    group = request.user.profile.group

    # Get available segmentations
    if group:
        segmentations = Segmentation.objects.filter(recording__group=group, status="completed").order_by("-created_at")
        projects = Project.objects.filter(group=group).order_by("name")
    else:
        segmentations = Segmentation.objects.filter(created_by=request.user, status="completed").order_by("-created_at")
        projects = Project.objects.filter(created_by=request.user).order_by("name")

    # Get available algorithms
    if group:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(group=group).order_by("name")
    else:
        algorithms = ClusteringAlgorithm.objects.filter(is_active=True).filter(created_by=request.user).order_by("name")

    algorithms = list(algorithms) + list(
        ClusteringAlgorithm.objects.filter(is_active=True, group__isnull=True).exclude(
            id__in=[a.id for a in algorithms]
        )
    )

    if request.method == "POST":
        scope = request.POST.get("scope", "segmentation")
        segmentation_id = request.POST.get("segmentation")
        project_id = request.POST.get("project")
        species_id = request.POST.get("species")
        algorithm_id = request.POST.get("algorithm")
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        n_clusters = request.POST.get("n_clusters")
        feature_method = request.POST.get("feature_method", "mfcc")
        batch_size = request.POST.get("batch_size", 500)

        # Validate required fields
        if not all([algorithm_id, name]):
            messages.error(request, "Please fill in all required fields")
            return redirect("battycoda_app:create_clustering_run")

        algorithm = get_object_or_404(ClusteringAlgorithm, id=algorithm_id)

        segmentation = None
        project = None
        species = None

        if scope == "project":
            # Project-level clustering
            if not project_id:
                messages.error(request, "Please select a project")
                return redirect("battycoda_app:create_clustering_run")

            project = get_object_or_404(Project, id=project_id)

            # Permission check
            if project.group != group:
                messages.error(request, "You don't have permission to cluster this project")
                return redirect("battycoda_app:create_clustering_run")

            # Get all species in the project
            project_species = Species.objects.filter(recordings__project=project).distinct()

            if project_species.count() == 0:
                messages.error(request, "Project has no recordings")
                return redirect("battycoda_app:create_clustering_run")

            # Species selection
            if project_species.count() > 1:
                if not species_id:
                    messages.error(
                        request,
                        f"Project contains {project_species.count()} species. Please select which species to cluster.",
                    )
                    return redirect("battycoda_app:create_clustering_run")
                species = get_object_or_404(Species, id=species_id)
            else:
                # Single species - auto-select
                species = project_species.first()

            # Validation: Project must have recordings of selected species
            recordings_query = project.recordings.filter(species=species)
            if recordings_query.count() == 0:
                messages.error(request, f"No recordings of {species.name} in this project")
                return redirect("battycoda_app:create_clustering_run")

            # Validation: Must have at least one completed segmentation
            completed_segs = Segmentation.objects.filter(recording__in=recordings_query, status="completed").count()
            if completed_segs == 0:
                messages.error(request, "No recordings have completed segmentations")
                return redirect("battycoda_app:create_clustering_run")

            # Count segments for warning
            segment_count = Segment.objects.filter(
                segmentation__recording__in=recordings_query, segmentation__status="completed"
            ).count()

            if segment_count > 10000:
                messages.warning(request, f"Large dataset ({segment_count} segments). This may take a while.")

        else:
            # Single-segmentation clustering
            if not segmentation_id:
                messages.error(request, "Please select a segmentation")
                return redirect("battycoda_app:create_clustering_run")

            segmentation = get_object_or_404(Segmentation, id=segmentation_id)

        # Create clustering run
        clustering_run = ClusteringRun.objects.create(
            name=name,
            description=description,
            scope=scope,
            segmentation=segmentation,
            project=project,
            species=species,
            algorithm=algorithm,
            n_clusters=int(n_clusters) if n_clusters else None,
            feature_extraction_method=feature_method,
            batch_size=int(batch_size) if batch_size else 500,
            created_by=request.user,
            group=group,
            status="pending",
            progress=0.0,
        )

        # Submit task
        from celery import current_app

        task_name = algorithm.celery_task
        task_func = current_app.tasks.get(task_name)
        if task_func:
            task = task_func.delay(clustering_run.id)
        else:
            from ..audio.task_modules.clustering.tasks import run_clustering

            task = run_clustering.delay(clustering_run.id)

        clustering_run.task_id = task.id
        clustering_run.save()

        messages.success(request, f"Clustering run '{name}' created and submitted")
        return redirect("battycoda_app:clustering_run_detail", run_id=clustering_run.id)

    context = {
        "segmentations": segmentations,
        "projects": projects,
        "algorithms": algorithms,
    }
    return render(request, "clustering/create_run.html", context)


@login_required
def clustering_run_detail(request, run_id):
    """Display details of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(
        request, clustering_run, error_message="You don't have permission to view this clustering run"
    )
    if error:
        return error

    clusters = []
    if clustering_run.status == "completed":
        clusters = Cluster.objects.filter(clustering_run=clustering_run).order_by("cluster_id")

    context = {
        "clustering_run": clustering_run,
        "clusters": clusters,
    }
    return render(request, "clustering/run_detail.html", context)


@login_required
def clustering_run_status(request, run_id):
    """Check the status of a clustering run."""
    clustering_run = get_object_or_404(ClusteringRun, id=run_id)

    error = check_clustering_permission(request, clustering_run, json_response=True)
    if error:
        return error

    return JsonResponse(
        {
            "status": clustering_run.status,
            "progress": clustering_run.progress,
            "progress_message": clustering_run.progress_message,
            "clusters_created": clustering_run.num_clusters_created,
        }
    )


@login_required
def get_project_segment_count(request, project_id):
    """Return segment stats for a project, including species breakdown."""
    project = get_object_or_404(Project, id=project_id)

    # Permission check (using consistent pattern with staff bypass)
    error = check_clustering_permission(request, project, json_response=True)
    if error:
        return error

    # Optional species filter
    species_id = request.GET.get("species")

    if species_id:
        # Return stats for specific species
        species = get_object_or_404(Species, id=species_id)
        recordings = project.recordings.filter(species=species)
        segment_count = Segment.objects.filter(
            segmentation__recording__in=recordings, segmentation__status="completed"
        ).count()
        return JsonResponse(
            {
                "species_name": species.name,
                "recording_count": recordings.count(),
                "segment_count": segment_count,
                "warning": segment_count > 5000,
            }
        )

    # Return all species in project with counts
    species_list = []
    for species in Species.objects.filter(recordings__project=project).distinct():
        recordings = project.recordings.filter(species=species)
        rec_count = recordings.count()
        seg_count = Segment.objects.filter(
            segmentation__recording__in=recordings, segmentation__status="completed"
        ).count()
        species_list.append(
            {"id": species.id, "name": species.name, "recording_count": rec_count, "segment_count": seg_count}
        )

    total_segments = sum(s["segment_count"] for s in species_list)

    return JsonResponse(
        {
            "species": species_list,
            "total_recordings": project.recordings.count(),
            "segment_count": total_segments,
            "warning": total_segments > 5000,
        }
    )
