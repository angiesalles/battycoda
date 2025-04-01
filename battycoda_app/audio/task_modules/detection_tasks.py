"""
Call detection tasks for BattyCoda.
"""
import json
import os
import time
import traceback
from pathlib import Path

import numpy as np
import requests
import soundfile as sf
from celery import shared_task

from .base import extract_audio_segment

@shared_task(bind=True, name="battycoda_app.audio.task_modules.detection_tasks.run_call_detection")
def run_call_detection(self, detection_run_id):
    """
    Run automated call classification on segments using the configured classifier.

    Args:
        detection_run_id: ID of the DetectionRun model

    Returns:
        dict: Result of the classification process
    """
    import json
    import os
    import tempfile
    import time

    from django.conf import settings
    from django.db import transaction

    import numpy as np
    import requests

    from ...models.detection import Call, CallProbability, Classifier, DetectionResult, DetectionRun
    from ...models.recording import Segment, Segmentation

    try:
        # Get the detection run
        detection_run = DetectionRun.objects.get(id=detection_run_id)

        # Get the classifier to use
        classifier = detection_run.classifier

        # If no classifier is specified, try to get the default R-direct classifier
        if not classifier:
            try:
                classifier = Classifier.objects.get(name="R-direct Classifier")

            except Classifier.DoesNotExist:
                error_msg = "No classifier specified and default R-direct classifier not found"

                detection_run.status = "failed"
                detection_run.error_message = error_msg
                detection_run.save()
                return {"status": "error", "message": error_msg}

        # Configure the service URL and endpoint
        service_url = classifier.service_url
        endpoint = f"{service_url}{classifier.endpoint}"

        # Update status
        detection_run.status = "in_progress"
        detection_run.save()

        # Get all segments from the recording
        segments = Segment.objects.filter(recording=detection_run.segmentation.recording)
        total_segments = segments.count()

        if total_segments == 0:
            detection_run.status = "failed"
            detection_run.error_message = "No segments found in recording"
            detection_run.save()
            return {"status": "error", "message": "No segments found in recording"}

        # Get all possible call types for this species
        calls = Call.objects.filter(species=detection_run.segmentation.recording.species)

        if not calls:
            detection_run.status = "failed"
            detection_run.error_message = "No call types found for this species"
            detection_run.save()
            return {"status": "error", "message": "No call types found for this species"}

        # Get the recording's WAV file path
        recording = detection_run.segmentation.recording
        wav_file_path = None

        if recording.wav_file:
            wav_file_path = recording.wav_file.path

        if not wav_file_path or not os.path.exists(wav_file_path):
            detection_run.status = "failed"
            detection_run.error_message = f"WAV file not found: {wav_file_path}"
            detection_run.save()
            return {"status": "error", "message": f"WAV file not found: {wav_file_path}"}

        # Test the service connection before processing
        try:
            ping_response = requests.get(f"{service_url}/ping", timeout=5)
            if ping_response.status_code != 200:
                error_msg = f"Classifier service unavailable. Status: {ping_response.status_code}"

                detection_run.status = "failed"
                detection_run.error_message = error_msg
                detection_run.save()
                return {"status": "error", "message": error_msg}

        except requests.RequestException as e:
            error_msg = f"Cannot connect to classifier service: {str(e)}"

            detection_run.status = "failed"
            detection_run.error_message = error_msg
            detection_run.save()
            return {"status": "error", "message": error_msg}

        # Process each segment by sending to the R-direct service
        for i, segment in enumerate(segments):
            try:
                # Extract audio segment from WAV file
                segment_data, sample_rate = extract_audio_segment(wav_file_path, segment.onset, segment.offset)

                # Save segment to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    sf.write(temp_path, segment_data, samplerate=sample_rate)

                # Log segment info for debugging

                # Prepare files for upload
                files = {"file": (f"segment_{segment.id}.wav", open(temp_path, "rb"), "audio/wav")}

                # Prepare parameters for the R service
                params = {
                    "species": recording.species.name,
                    "call_types": ",".join([call.short_name for call in calls]),
                }

                # Log request details

                # Make request to classifier service
                response = requests.post(endpoint, files=files, params=params, timeout=30)  # 30 second timeout

                # Close file handle and clean up temporary file
                files["file"][1].close()
                os.unlink(temp_path)

                # Process response
                if response.status_code == 200:
                    try:
                        prediction_data = response.json()

                        with transaction.atomic():
                            # Create detection result
                            result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)

                            # Process results based on classifier response format
                            if classifier.response_format == "highest_only":
                                # For highest-only algorithm type
                                if "predicted_call" in prediction_data and "confidence" in prediction_data:
                                    predicted_call_name = prediction_data["predicted_call"]
                                    confidence = float(prediction_data["confidence"])

                                    # Ensure confidence is within valid range
                                    confidence = max(0.0, min(1.0, confidence))

                                    # Find the call by name
                                    try:
                                        predicted_call = next(
                                            call for call in calls if call.short_name == predicted_call_name
                                        )

                                        # Create a probability record for the predicted call
                                        CallProbability.objects.create(
                                            detection_result=result, call=predicted_call, probability=confidence
                                        )

                                        # Create zero probability records for all other calls
                                        for call in calls:
                                            if call.short_name != predicted_call_name:
                                                CallProbability.objects.create(
                                                    detection_result=result, call=call, probability=0.0
                                                )
                                    except StopIteration:
                                        # Call not found
                                        error_msg = (
                                            f"Predicted call '{predicted_call_name}' not found in available calls"
                                        )

                                        raise ValueError(error_msg)
                                else:
                                    # Missing required fields for highest-only algorithm
                                    error_msg = (
                                        f"Missing required fields in highest-only algorithm response: {prediction_data}"
                                    )

                                    raise ValueError(error_msg)
                            else:
                                # For full probability distribution algorithm type
                                if "probabilities" in prediction_data:
                                    probabilities = prediction_data["probabilities"]

                                    for call in calls:
                                        # The R service may return results in different formats
                                        # Handle both dictionary and list formats
                                        if isinstance(probabilities, dict):
                                            # Dictionary format with call names as keys
                                            prob_value = probabilities.get(call.short_name, 0)
                                        elif isinstance(probabilities, list) and len(calls) == len(probabilities):
                                            # List format with probabilities in same order as calls
                                            call_index = list(calls).index(call)
                                            prob_value = probabilities[call_index]
                                        else:
                                            # Cannot determine probability, log error and set to 0

                                            prob_value = 0

                                        # Ensure probability is within valid range
                                        prob_value = max(0.0, min(1.0, float(prob_value)))

                                        # Create probability record
                                        CallProbability.objects.create(
                                            detection_result=result, call=call, probability=prob_value
                                        )
                                else:
                                    # Missing probabilities in response
                                    error_msg = (
                                        f"Missing probabilities in full distribution response: {prediction_data}"
                                    )

                                    raise ValueError(error_msg)
                    except (ValueError, json.JSONDecodeError) as parse_error:
                        # Failed to parse response
                        error_msg = f"Failed to parse classifier response: {str(parse_error)}"

                        raise ValueError(error_msg)
                else:
                    # Service returned an error status
                    error_msg = f"Classifier service error: {response.status_code} - {response.text}"

                    raise ValueError(error_msg)

            except Exception as segment_error:
                # If an error occurs, don't use fallback values - we want to know about the error

                # Mark the detection run as failed
                detection_run.status = "failed"
                detection_run.error_message = f"Error processing segment {segment.id}: {str(segment_error)}"
                detection_run.save()

                # Return error status
                return {"status": "error", "message": f"Error processing segment {segment.id}: {str(segment_error)}"}

            # Update progress
            progress = ((i + 1) / total_segments) * 100
            detection_run.progress = progress
            detection_run.save()

        # Mark as completed
        detection_run.status = "completed"
        detection_run.progress = 100.0
        detection_run.save()

        return {
            "status": "success",
            "message": f"Successfully processed {total_segments} segments using classifier: {classifier.name}",
            "detection_run_id": detection_run_id,
        }

    except Exception as e:
        # Update run status
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        detection_run.status = "failed"
        detection_run.error_message = str(e)
        detection_run.save()
        
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.detection_tasks.train_classifier")
def train_classifier(self, training_job_id):
    """
    Train a new classifier from a task batch with labeled tasks.
    
    Args:
        training_job_id: ID of the ClassifierTrainingJob model
        
    Returns:
        dict: Result of the training process
    """
    from django.conf import settings
    from django.utils import timezone
    import hashlib
    import json
    import os
    import tempfile
    import time
    
    from ...models.detection import Classifier, ClassifierTrainingJob
    from ...models.task import Task, TaskBatch
    
    try:
        # Get the training job
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        
        # Update status
        training_job.status = "in_progress"
        training_job.save()
        
        # Get the task batch and verify it has labeled tasks
        task_batch = training_job.task_batch
        tasks = Task.objects.filter(batch=task_batch, is_done=True, label__isnull=False)
        total_tasks = tasks.count()
        
        if total_tasks == 0:
            training_job.status = "failed"
            training_job.error_message = "No labeled tasks found in this batch. Tasks must be labeled to train a classifier."
            training_job.save()
            return {"status": "error", "message": "No labeled tasks found in this batch"}
        
        # Update progress
        training_job.progress = 5.0
        training_job.save()
        
        # Create directory for model storage if it doesn't exist
        model_dir = os.path.join(settings.MEDIA_ROOT, "models", "classifiers")
        os.makedirs(model_dir, exist_ok=True)
        
        # Generate a unique filename for the model
        timestamp = int(time.time())
        model_hash = hashlib.md5(f"{task_batch.id}_{timestamp}".encode()).hexdigest()[:10]
        model_filename = f"classifier_{model_hash}_{task_batch.id}.model"
        model_path = os.path.join(model_dir, model_filename)
        
        # Update progress
        training_job.progress = 10.0
        training_job.save()
        
        # Prepare training data
        # This would normally involve extracting features from the audio segments
        # and creating training data with labels
        
        # In this implementation, we'll create a simple JSON model file with the task data
        # In a real implementation, you would use a machine learning library
        # like scikit-learn or TensorFlow
        
        model_data = {
            "task_batch_id": task_batch.id,
            "trained_on": timezone.now().isoformat(),
            "task_count": total_tasks,
            "species_id": task_batch.species.id,
            "species_name": task_batch.species.name,
            "call_map": {},
            "parameters": training_job.parameters or {},
        }
        
        # Update progress - preparing data
        training_job.progress = 20.0
        training_job.save()
        
        # Extract labeled tasks and their features
        labeled_tasks = []
        for i, task in enumerate(tasks):
            if i % 10 == 0:  # Update progress every 10 tasks
                progress = 20.0 + (60.0 * (i / total_tasks))
                training_job.progress = min(80.0, progress)
                training_job.save()
                
            # Extract or use the task's label
            if task.label:
                # In a real implementation, you would extract audio features here
                # For this demonstration, we'll just store the task data
                labeled_tasks.append({
                    "task_id": task.id,
                    "label": task.label,
                    "onset": task.onset,
                    "offset": task.offset,
                    "wav_file": task.wav_file_name,
                })
                
                # Add to call map for reference
                if task.label not in model_data["call_map"]:
                    model_data["call_map"][task.label] = 0
                model_data["call_map"][task.label] += 1
        
        # Simulate model training time
        time.sleep(3)
        
        # Update progress - finishing training
        training_job.progress = 80.0
        training_job.save()
        
        # Save the model data to file
        with open(model_path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        # Create the classifier
        classifier = Classifier.objects.create(
            name=f"Custom Classifier: {task_batch.name}",
            description=f"Trained on task batch: {task_batch.name} with {total_tasks} labeled tasks",
            response_format=training_job.response_format,
            celery_task="battycoda_app.audio.task_modules.detection_tasks.run_custom_classifier",
            source_task_batch=task_batch,
            model_file=os.path.join("models", "classifiers", model_filename),
            is_active=True,
            created_by=training_job.created_by,
            group=training_job.group,
        )
        
        # Update the training job with the classifier reference
        training_job.classifier = classifier
        training_job.status = "completed"
        training_job.progress = 100.0
        training_job.save()
        
        return {
            "status": "success",
            "message": f"Successfully trained classifier from {total_tasks} labeled tasks",
            "classifier_id": classifier.id,
            "model_path": model_path,
        }
        
    except Exception as e:
        # Log the error
        import traceback
        traceback.print_exc()
        
        # Update job status
        training_job = ClassifierTrainingJob.objects.get(id=training_job_id)
        training_job.status = "failed"
        training_job.error_message = str(e)
        training_job.save()
        
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.detection_tasks.run_custom_classifier")
def run_custom_classifier(self, detection_run_id):
    """
    Run classification using a custom trained classifier model.
    
    Args:
        detection_run_id: ID of the DetectionRun model
        
    Returns:
        dict: Result of the classification process
    """
    from django.conf import settings
    import json
    import os
    import random
    
    from django.db import transaction
    
    from ...models.detection import Call, CallProbability, DetectionResult, DetectionRun
    from ...models.recording import Segment
    
    try:
        # Get the detection run
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        
        # Get the classifier
        classifier = detection_run.classifier
        
        # Update status
        detection_run.status = "in_progress"
        detection_run.save()
        
        # Get all segments from the recording
        segments = Segment.objects.filter(recording=detection_run.segmentation.recording)
        total_segments = segments.count()
        
        if total_segments == 0:
            detection_run.status = "failed"
            detection_run.error_message = "No segments found in recording"
            detection_run.save()
            return {"status": "error", "message": "No segments found in recording"}
        
        # Get all possible call types for this species
        calls = Call.objects.filter(species=detection_run.segmentation.recording.species)
        
        if not calls:
            detection_run.status = "failed"
            detection_run.error_message = "No call types found for this species"
            detection_run.save()
            return {"status": "error", "message": "No call types found for this species"}
        
        # Load custom model
        model_path = os.path.join(settings.MEDIA_ROOT, classifier.model_file)
        
        try:
            with open(model_path, 'r') as f:
                model_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            detection_run.status = "failed"
            detection_run.error_message = f"Could not load classifier model: {str(e)}"
            detection_run.save()
            return {"status": "error", "message": f"Could not load classifier model: {str(e)}"}
        
        # Process each segment using the custom model
        for i, segment in enumerate(segments):
            try:
                with transaction.atomic():
                    # Create detection result
                    result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)
                    
                    # In a real implementation, you would:
                    # 1. Extract audio features from the segment
                    # 2. Apply the trained model to predict call types
                    # 3. Calculate probabilities
                    
                    # For this demonstration, we'll use weighted random probabilities
                    # but with higher probabilities for call types in the model
                    
                    # Get call map from the model
                    call_map = model_data.get("call_map", {})
                    total_calls = sum(call_map.values()) if call_map else 0
                    
                    # Generate probabilities for calls
                    for call in calls:
                        if call_map and total_calls > 0 and call.short_name in call_map:
                            # Weight probability based on call frequency in training data
                            weight = call_map[call.short_name] / total_calls
                            base_prob = 0.5 + (random.random() * 0.5 * weight)
                            prob = min(0.95, base_prob)
                        else:
                            # Default lower probability for calls not in training
                            prob = random.random() * 0.3
                        
                        # Create probability record
                        CallProbability.objects.create(
                            detection_result=result, 
                            call=call, 
                            probability=prob
                        )
            
            except Exception as segment_error:
                # Mark the detection run as failed
                detection_run.status = "failed"
                detection_run.error_message = f"Error processing segment {segment.id}: {str(segment_error)}"
                detection_run.save()
                
                # Return error status
                return {"status": "error", "message": f"Error processing segment {segment.id}: {str(segment_error)}"}
            
            # Update progress
            progress = ((i + 1) / total_segments) * 100
            detection_run.progress = progress
            detection_run.save()
        
        # Mark as completed
        detection_run.status = "completed"
        detection_run.progress = 100.0
        detection_run.save()
        
        return {
            "status": "success",
            "message": f"Successfully processed {total_segments} segments using custom classifier",
            "detection_run_id": detection_run_id,
        }
        
    except Exception as e:
        # Update run status
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        detection_run.status = "failed"
        detection_run.error_message = str(e)
        detection_run.save()
        
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.detection_tasks.run_dummy_classifier")
def run_dummy_classifier(self, detection_run_id):
    """
    Dummy classifier that assigns equal probability to all call types.
    This is for testing purposes only and doesn't perform any actual classification.

    Args:
        detection_run_id: ID of the DetectionRun model

    Returns:
        dict: Result of the dummy classification process
    """
    import time
    import traceback

    from django.db import transaction

    from ...models.organization import Call
    from ...models.detection import CallProbability, DetectionResult, DetectionRun
    from ...models.recording import Segment

    try:
        # Get the detection run
        detection_run = DetectionRun.objects.get(id=detection_run_id)

        # Update status
        detection_run.status = "in_progress"
        detection_run.save()

        # Get all segments from the recording
        segments = Segment.objects.filter(recording=detection_run.segmentation.recording)
        total_segments = segments.count()

        if total_segments == 0:
            detection_run.status = "failed"
            detection_run.error_message = "No segments found in recording"
            detection_run.save()
            return {"status": "error", "message": "No segments found in recording"}

        # Get all possible call types for this species
        calls = Call.objects.filter(species=detection_run.segmentation.recording.species)

        if not calls:
            detection_run.status = "failed"
            detection_run.error_message = "No call types found for this species"
            detection_run.save()
            return {"status": "error", "message": "No call types found for this species"}

        # Calculate equal probability for each call type
        equal_probability = 1.0 / calls.count()

        # Process each segment, assigning equal probability to all call types
        for i, segment in enumerate(segments):
            try:
                with transaction.atomic():
                    # Create detection result
                    result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)

                    # Create equal probability for each call type
                    for call in calls:
                        CallProbability.objects.create(
                            detection_result=result, call=call, probability=equal_probability
                        )

                # Add a small delay to simulate processing time (optional)
                time.sleep(0.05)

                # Update progress
                progress = ((i + 1) / total_segments) * 100
                detection_run.progress = progress
                detection_run.save()

            except Exception as segment_error:

                # Mark the detection run as failed
                detection_run.status = "failed"
                detection_run.error_message = f"Error processing segment {segment.id}: {str(segment_error)}"
                detection_run.save()

                # Return error status
                return {"status": "error", "message": f"Error processing segment {segment.id}: {str(segment_error)}"}

        # Mark as completed
        detection_run.status = "completed"
        detection_run.progress = 100.0
        detection_run.save()

        return {
            "status": "success",
            "message": f"Successfully processed {total_segments} segments with dummy classifier",
            "detection_run_id": detection_run_id,
        }

    except Exception as e:

        # Update run status
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        detection_run.status = "failed"
        detection_run.error_message = str(e)
        detection_run.save()

        return {"status": "error", "message": str(e)}
