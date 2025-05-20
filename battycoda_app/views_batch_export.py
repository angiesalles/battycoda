"""Views for exporting batches in bulk."""

import csv
import os
import tempfile
import zipfile
from datetime import datetime
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .models.task import Task, TaskBatch
from .utils_modules.task_export_utils import generate_tasks_csv


@login_required
def export_completed_batches(request):
    """Export all completed batches as a ZIP file containing CSV exports."""
    # Get user profile
    profile = request.user.profile
    
    # Determine which batches to include
    if profile.group and profile.is_admin:
        # Admin sees all batches in their group
        batches = TaskBatch.objects.filter(group=profile.group)
    else:
        # Regular user only sees their own batches
        batches = TaskBatch.objects.filter(created_by=request.user)
    
    # Filter for completed batches (all tasks in the batch are done)
    completed_batches = []
    for batch in batches:
        # Count total tasks and completed tasks
        task_count = Task.objects.filter(batch=batch).count()
        if task_count == 0:
            continue  # Skip empty batches
            
        completed_count = Task.objects.filter(batch=batch, is_done=True).count()
        
        # Only include batches where all tasks are completed
        if task_count == completed_count:
            completed_batches.append(batch)
    
    if not completed_batches:
        messages.info(request, "No completed batches found to export.")
        return redirect("battycoda_app:task_batch_list")
    
    # Create a temporary directory to store CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"completed_batches_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # Build the ZIP file containing CSVs for each batch
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for batch in completed_batches:
                # Get tasks for this batch
                tasks = Task.objects.filter(batch=batch).order_by("id")
                
                # Generate CSV for this batch using the shared utility function
                csv_content = generate_tasks_csv(tasks)
                
                # Clean batch name for filename
                safe_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in batch.name)
                filename = f"batch_{batch.id}_{safe_name}.csv"
                
                # Add CSV to the ZIP file
                zipf.writestr(filename, csv_content)
                
            # Add a summary file with batch information
            summary_content = generate_summary_csv(completed_batches)
            zipf.writestr("batch_summary.csv", summary_content)
        
        # Serve the ZIP file for download
        with open(zip_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
            return response


def generate_summary_csv(batches):
    """Generate a summary CSV with information about all included batches."""
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header row
    writer.writerow([
        "Batch ID",
        "Batch Name",
        "WAV File",
        "Species",
        "Project",
        "Tasks Count",
        "Created By",
        "Created At",
    ])
    
    # Write a row for each batch
    for batch in batches:
        task_count = Task.objects.filter(batch=batch).count()
        writer.writerow([
            batch.id,
            batch.name,
            batch.wav_file_name,
            batch.species.name,
            batch.project.name,
            task_count,
            batch.created_by.username,
            batch.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ])
    
    # Return the CSV content
    return output.getvalue()