"""
Training tasks for BattyCoda.

This module contains tasks for training custom classifiers.
"""
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

import requests
import soundfile as sf
from celery import shared_task
from django.conf import settings

from .base import extract_audio_segment
from .detection_tasks import (R_SERVER_URL, check_r_server_connection,
                             update_detection_run_status)


@shared_task(bind=True, name="battycoda_app.audio.task_modules.training_tasks.train_classifier")
def train_classifier(self, training_job_id):
    """
    Train a new classifier from a task batch with labeled tasks.
    Uses the R server to train either KNN or LDA classifier from audio segments.
    
    Args:
        training_job_id: ID of the ClassifierTrainingJob model
        
    Returns:
        dict: Result of the training process
    """
    from ...models.detection import Classifier, ClassifierTrainingJob
    from ...models.task import Task
    
    try:
        # Get the training job
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        
        # Update status to in progress
        update_detection_run_status(training_job, "in_progress", progress=5)
        
        # Get the task batch and verify it has labeled tasks
        task_batch = training_job.task_batch
        tasks = Task.objects.filter(batch=task_batch, is_done=True, label__isnull=False)
        total_tasks = tasks.count()
        
        if total_tasks == 0:
            error_msg = "No labeled tasks found in this batch. Tasks must be labeled to train a classifier."
            update_detection_run_status(training_job, "failed", error_msg)
            return {"status": "error", "message": error_msg}
        
        # Create directory for model storage
        model_dir = os.path.join(settings.MEDIA_ROOT, "models", "classifiers")
        os.makedirs(model_dir, exist_ok=True)
        
        # Generate a unique filename for the model
        timestamp = int(time.time())
        model_hash = hashlib.md5(f"{task_batch.id}_{timestamp}".encode()).hexdigest()[:10]
        model_filename = f"classifier_{model_hash}_{task_batch.id}.RData"
        model_path = os.path.join(model_dir, model_filename)
        
        update_detection_run_status(training_job, "in_progress", progress=10)
        
        # Create a temporary directory in a location both containers can access
        # Since both containers mount the /app directory, we'll create it there
        temp_dir = os.path.join("/app/tmp", f"training_{model_hash}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract and save labeled segments
        call_map = {}  # Track call types and their counts
        file_counter = 1
        
        for i, task in enumerate(tasks):
            if i % 5 == 0:  # Update progress every 5 tasks
                progress = 10.0 + (40.0 * (i / total_tasks))
                update_detection_run_status(training_job, "in_progress", progress=min(50.0, progress))
            
            # Skip tasks without labels
            if not task.label:
                continue
            
            # Track call type counts
            if task.label not in call_map:
                call_map[task.label] = 0
            call_map[task.label] += 1
            
            # Extract and save the audio segment
            try:
                # Get wav_file directly from task_batch
                if not task_batch.wav_file:
                    print(f"Warning: Task batch {task_batch.id} has no wav_file")
                    continue
                
                wav_file_path = task_batch.wav_file.path
                
                if not os.path.exists(wav_file_path):
                    print(f"Warning: WAV file path does not exist: {wav_file_path}")
                    continue
                
                # Debug info
                print(f"Extracting segment for task {task.id}: {task.onset} to {task.offset} from {wav_file_path}")
                
                # Extract audio segment
                segment_data, sample_rate = extract_audio_segment(
                    wav_file_path, task.onset, task.offset
                )
                
                # Check if we have valid audio data
                if segment_data is None or len(segment_data) == 0:
                    print(f"Warning: No audio data extracted for task {task.id}")
                    continue
                
                # Save as WAV with format NUMBER_LABEL.wav
                output_filename = f"{file_counter}_{task.label}.wav"
                output_path = os.path.join(temp_dir, output_filename)
                sf.write(output_path, segment_data, samplerate=sample_rate)
                
                print(f"Saved segment {file_counter} with label '{task.label}' to {output_path}")
                file_counter += 1
            except Exception as e:
                # Log error but continue with other tasks
                print(f"Error extracting segment for task {task.id}: {str(e)}")
                continue
        
        update_detection_run_status(training_job, "in_progress", progress=50)
        
        # Check if we have enough files
        if file_counter <= 1:
            error_msg = "Failed to extract any valid audio segments for training."
            update_detection_run_status(training_job, "failed", error_msg)
            
            # Clean up
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            
            return {"status": "error", "message": error_msg}
        
        # Check R server connection
        server_ok, error_msg = check_r_server_connection(R_SERVER_URL)
        if not server_ok:
            update_detection_run_status(training_job, "failed", error_msg)
            
            # Clean up
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
            
            return {"status": "error", "message": error_msg}
        
        update_detection_run_status(training_job, "in_progress", progress=60)
        
        # Send training request to R server
        try:
            # Check if parameters has algorithm_type, default to "knn"
            algorithm_type = "knn"  # Default
            if training_job.parameters and 'algorithm_type' in training_job.parameters:
                algorithm_type = training_job.parameters['algorithm_type']
            
            # Build parameters for R server
            train_params = {
                'data_folder': temp_dir,
                'output_model_path': model_path,
                'test_split': 0.2  # Use 20% for testing
            }
            
            # Add any additional parameters from training_job.parameters
            if training_job.parameters:
                for key, value in training_job.parameters.items():
                    if key != 'algorithm_type':  # We handle this separately for endpoint selection
                        train_params[key] = value
            
            update_detection_run_status(training_job, "in_progress", progress=70)
            
            # Determine which endpoint to use based on algorithm type
            if algorithm_type.lower() == "lda":
                endpoint = f"{R_SERVER_URL}/train/lda"
                algorithm_description = "Linear Discriminant Analysis"
            else:
                endpoint = f"{R_SERVER_URL}/train/knn"
                algorithm_description = "K-Nearest Neighbors"
            
            print(f"Using {algorithm_type.upper()} training endpoint: {endpoint}")
            print(f"Training parameters: {train_params}")
            
            # Make the training request - IMPORTANT: Use data instead of params
            train_response = requests.post(
                endpoint,
                data=train_params,  # Changed from params to data for proper form encoding
                timeout=3600  # Allow up to 1 hour for training
            )
            
            if train_response.status_code != 200:
                error_msg = f"R server training failed. Status: {train_response.status_code}, Response: {train_response.text}"
                update_detection_run_status(training_job, "failed", error_msg)
                
                # Clean up
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                
                return {"status": "error", "message": f"R server training failed. Status: {train_response.status_code}"}
            
            # Debug the raw response before parsing JSON
            print(f"Raw training response text: {train_response.text[:200]}...")  # Print first 200 chars
            
            # Process successful response
            train_result = train_response.json()
            update_detection_run_status(training_job, "in_progress", progress=90)
            
            # Handle both string and list format for status, same as in classification_tasks.py
            status_value = train_result.get('status')
            is_success = (status_value == 'success' or 
                         (isinstance(status_value, list) and len(status_value) > 0 and status_value[0] == 'success'))
            
            if not is_success:
                error_msg = f"R server training error: {train_result.get('message', 'Unknown error')}"
                update_detection_run_status(training_job, "failed", error_msg)
                
                # Clean up
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                
                return {"status": "error", "message": error_msg}
            
            # Training successful, create the classifier
            # Unwrap list values if needed
            def unwrap_list(value):
                if isinstance(value, list) and len(value) > 0:
                    return value[0]
                return value
                
            # Get accuracy, ensure it's a number not a list
            accuracy = unwrap_list(train_result.get('accuracy', 0))
            if not isinstance(accuracy, (int, float)):
                try:
                    accuracy = float(accuracy)
                except (ValueError, TypeError):
                    accuracy = 0
                    
            # Get classes, ensure it's a list
            classes = train_result.get('classes', [])
            if not isinstance(classes, list):
                classes = []
            
            # Create classifier in database
            classifier = Classifier.objects.create(
                name=f"{algorithm_type.upper()} Classifier: {task_batch.name}",
                description=f"{algorithm_description} classifier trained on task batch: {task_batch.name} with {total_tasks} labeled tasks. Accuracy: {accuracy:.1f}%",
                response_format=training_job.response_format,
                celery_task="battycoda_app.audio.task_modules.classification_tasks.run_call_detection",
                service_url=R_SERVER_URL,
                endpoint=f"/predict/{algorithm_type.lower()}",  # Use the appropriate endpoint for this algorithm
                source_task_batch=task_batch,
                model_file=os.path.join("media", "models", "classifiers", model_filename),
                is_active=True,
                created_by=training_job.created_by,
                group=training_job.group,
                species=task_batch.species  # Link to the species
            )
            
            # Update the training job with classifier reference
            training_job.classifier = classifier
            update_detection_run_status(training_job, "completed", progress=100)
            
            result = {
                "status": "success",
                "message": f"Successfully trained classifier on {file_counter-1} segments with {len(classes)} call types. Accuracy: {accuracy:.1f}%",
                "classifier_id": classifier.id,
                "model_path": model_path,
                "accuracy": accuracy,
                "classes": classes
            }
            
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                # Don't fail if cleanup fails
                pass
                
            return result
            
        except Exception as e:
            error_msg = f"Error in model training: {str(e)}"
            update_detection_run_status(training_job, "failed", error_msg)
            
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass
                
            return {"status": "error", "message": error_msg}
                
    except Exception as e:
        # Update job status and return error
        try:
            training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
            error_msg = f"Error in classifier training: {str(e)}"
            update_detection_run_status(training_job, "failed", error_msg)
        except Exception:
            error_msg = f"Critical error in classifier training: {str(e)}"
            
        # Try to clean up the temp directory if it was created
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        except Exception:
            pass
            
        return {"status": "error", "message": error_msg}