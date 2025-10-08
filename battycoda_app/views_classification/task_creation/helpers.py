"""Helper functions for task batch creation."""

from battycoda_app.models.classification import ClassificationResult
from battycoda_app.models.task import Task, TaskBatch


def create_task_batch_helper(run, batch_name, description, created_by, group, max_confidence=None):
    """
    Helper function to create a task batch from a classification run.

    Args:
        run: ClassificationRun instance
        batch_name: Name for the task batch
        description: Description for the task batch
        created_by: User creating the batch
        group: Group for the batch
        max_confidence: Optional confidence threshold (tasks with higher confidence are filtered out)

    Returns:
        tuple: (batch, tasks_created, tasks_filtered) or (None, 0, 0) if no tasks created
    """
    recording = run.segmentation.recording

    batch = TaskBatch.objects.create(
        name=batch_name,
        description=description,
        created_by=created_by,
        wav_file_name=recording.wav_file.name if recording.wav_file else '',
        wav_file=recording.wav_file,
        species=recording.species,
        project=recording.project,
        group=group,
        detection_run=run,
    )

    # Fetch all results with probabilities in one efficient query
    results = ClassificationResult.objects.filter(
        classification_run=run
    ).select_related('segment').prefetch_related('probabilities__call')

    # Get all segment IDs that already have tasks (one query)
    segments_with_tasks = set(
        Task.objects.filter(
            source_segment__classification_results__classification_run=run
        ).values_list('source_segment_id', flat=True)
    )

    tasks_to_create = []
    tasks_created = 0
    tasks_filtered = 0

    for result in results:
        segment = result.segment

        # Skip if segment already has a task (no DB query)
        if segment.id in segments_with_tasks:
            continue

        # Get top probability from prefetched data (no DB query)
        probabilities = list(result.probabilities.all())
        top_probability = max(probabilities, key=lambda p: p.probability) if probabilities else None

        if max_confidence is not None and top_probability and top_probability.probability > max_confidence:
            tasks_filtered += 1
            continue

        task_data = Task(
            wav_file_name=recording.wav_file.name if recording.wav_file else '',
            onset=segment.onset,
            offset=segment.offset,
            species=recording.species,
            project=recording.project,
            batch=batch,
            created_by=created_by,
            group=group,
            label=top_probability.call.short_name if top_probability else None,
            classification_result=top_probability.call.short_name if top_probability else None,
            confidence=top_probability.probability if top_probability else None,
            status="pending",
            source_segment=segment,
        )
        tasks_to_create.append(task_data)
        tasks_created += 1

    if tasks_created == 0:
        batch.delete()
        return None, 0, 0

    Task.objects.bulk_create(tasks_to_create)

    return batch, tasks_created, tasks_filtered
