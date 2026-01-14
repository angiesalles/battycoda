"""
Utility functions for exporting task data.
"""

import csv
from io import StringIO


def generate_tasks_csv(tasks):
    """
    Generate CSV content for a list of tasks.

    Args:
        tasks (QuerySet): A queryset of Task objects

    Returns:
        str: CSV content as a string
    """
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(
        [
            "Task ID",
            "Onset (s)",
            "Offset (s)",
            "Duration (s)",
            "Status",
            "Label",
            "Classification Result",
            "Confidence",
            "Notes",
            "WAV File",
            "Species",
            "Project",
            "Created By",
            "Annotated By",
            "Created At",
            "Updated At",
            "Annotated At",
        ]
    )

    # Write data rows
    for task in tasks:
        writer.writerow(
            [
                task.id,
                task.onset,
                task.offset,
                task.offset - task.onset,
                task.status,
                "" if task.status == "pending" else task.label if task.label else "",
                task.classification_result if task.classification_result else "",
                task.confidence if task.confidence is not None else "",
                task.notes.replace("\n", " ").replace("\r", "") if task.notes else "",
                task.wav_file_name,
                task.species.name,
                task.project.name,
                task.created_by.username,
                task.annotated_by.username if task.annotated_by else "",
                task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                task.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                task.annotated_at.strftime("%Y-%m-%d %H:%M:%S") if task.annotated_at else "",
            ]
        )

    # Return the CSV content
    return output.getvalue()
