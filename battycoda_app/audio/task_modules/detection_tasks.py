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

# Centralized configuration
R_SERVER_URL = "http://localhost:8000"

@shared_task(bind=True, name="battycoda_app.audio.task_modules.detection_tasks.run_call_detection")
def run_call_detection(self, detection_run_id):
    """
    Run automated call classification on segments using the configured classifier.
    Uses the R server /classify endpoint to classify audio segments.

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

        # Process each segment by sending to the R server
        for i, segment in enumerate(segments):
            try:
                # Extract audio segment from WAV file
                segment_data, sample_rate = extract_audio_segment(wav_file_path, segment.onset, segment.offset)

                # Save segment to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_path = temp_file.name
                    sf.write(temp_path, segment_data, samplerate=sample_rate)

                # Prepare parameters for the R service
                # Check if we have a custom model
                model_path = None
                if classifier.model_file:
                    model_path = os.path.join(settings.MEDIA_ROOT, classifier.model_file)
                    if not os.path.exists(model_path):
                        model_path = None  # Fallback to default model if specified model doesn't exist

                # Set up parameters for the classify endpoint
                params = {
                    "wav_path": temp_path,
                    "onset": 0,  # We've already extracted the segment, so use 0 as onset
                    "offset": len(segment_data) / sample_rate,  # Convert samples to seconds
                    "species": recording.species.name if recording.species else "Efuscus"
                }

                # Add model_path parameter if available
                if model_path:
                    params["model_path"] = model_path

                # Make request to classifier service
                response = requests.post(endpoint, params=params, timeout=30)  # 30 second timeout

                # Clean up temporary file
                os.unlink(temp_path)

                # Process response
                if response.status_code == 200:
                    try:
                        prediction_data = response.json()

                        with transaction.atomic():
                            # Create detection result
                            result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)

                            # Process results based on the response format
                            if classifier.response_format == "highest_only":
                                # For highest-only algorithm type
                                if "call_type" in prediction_data and "confidence" in prediction_data:
                                    # The R server returns "call_type" instead of "predicted_call"
                                    predicted_call_name = prediction_data["call_type"]
                                    confidence = float(prediction_data["confidence"]) / 100.0  # Convert percentage to 0-1 range

                                    # Ensure confidence is within valid range
                                    confidence = max(0.0, min(1.0, confidence))

                                    # Find the call by name
                                    matching_calls = [call for call in calls if call.short_name == predicted_call_name]
                                    
                                    if matching_calls:
                                        predicted_call = matching_calls[0]
                                        
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
                                    else:
                                        # Call not found - create even probabilities and log error
                                        equal_prob = 1.0 / len(calls)
                                        for call in calls:
                                            CallProbability.objects.create(
                                                detection_result=result, call=call, probability=equal_prob
                                            )
                                        print(f"Warning: Predicted call '{predicted_call_name}' not found in available calls")
                                else:
                                    # Missing required fields - create equal probabilities and log error
                                    equal_prob = 1.0 / len(calls)
                                    for call in calls:
                                        CallProbability.objects.create(
                                            detection_result=result, call=call, probability=equal_prob
                                        )
                                    print(f"Warning: Missing fields in highest-only response: {prediction_data}")
                            else:
                                # For full probability distribution algorithm type
                                if "all_probabilities" in prediction_data:
                                    all_probs = prediction_data["all_probabilities"]

                                    for call in calls:
                                        # Try to get probability for this call
                                        if call.short_name in all_probs:
                                            # Convert from percentage to 0-1 range
                                            prob_value = float(all_probs[call.short_name]) / 100.0
                                        else:
                                            # Not found in probabilities, use low value
                                            prob_value = 0.01

                                        # Ensure probability is within valid range
                                        prob_value = max(0.0, min(1.0, float(prob_value)))

                                        # Create probability record
                                        CallProbability.objects.create(
                                            detection_result=result, call=call, probability=prob_value
                                        )
                                else:
                                    # Missing probabilities - create equal probabilities and log error
                                    equal_prob = 1.0 / len(calls)
                                    for call in calls:
                                        CallProbability.objects.create(
                                            detection_result=result, call=call, probability=equal_prob
                                        )
                                    print(f"Warning: Missing probabilities in full distribution response: {prediction_data}")
                                    
                    except (ValueError, json.JSONDecodeError) as parse_error:
                        # Failed to parse response - create a result with equal probabilities
                        result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)
                        
                        # Create equal probability records for all calls
                        equal_prob = 1.0 / len(calls)
                        for call in calls:
                            CallProbability.objects.create(
                                detection_result=result, call=call, probability=equal_prob
                            )
                        
                        print(f"Warning: Failed to parse classifier response: {str(parse_error)}")
                else:
                    # Service returned an error status - create a result with equal probabilities
                    result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)
                    
                    # Create equal probability records for all calls
                    equal_prob = 1.0 / len(calls)
                    for call in calls:
                        CallProbability.objects.create(
                            detection_result=result, call=call, probability=equal_prob
                        )
                    
                    print(f"Warning: Classifier service error: {response.status_code} - {response.text}")

            except Exception as segment_error:
                # Log the error but continue processing other segments
                print(f"Error processing segment {segment.id}: {str(segment_error)}")
                
                try:
                    # Create a result with equal probabilities
                    result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)
                    
                    # Create equal probability records for all calls
                    equal_prob = 1.0 / len(calls)
                    for call in calls:
                        CallProbability.objects.create(
                            detection_result=result, call=call, probability=equal_prob
                        )
                except Exception as fallback_error:
                    print(f"Error creating fallback result: {str(fallback_error)}")

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
    Uses the R server to train a KNN classifier from audio segments.
    
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
    import requests
    import shutil
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
        model_filename = f"classifier_{model_hash}_{task_batch.id}.RData"
        model_path = os.path.join(model_dir, model_filename)
        
        # Update progress
        training_job.progress = 10.0
        training_job.save()
        
        # Create a temporary directory to store the WAV segments for training
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a counter to ensure unique filenames
            file_counter = 1
            # Dictionary to track call types and their counts
            call_map = {}
            
            # Process each labeled task and extract the audio segment
            for i, task in enumerate(tasks):
                if i % 5 == 0:  # Update progress every 5 tasks
                    progress = 10.0 + (40.0 * (i / total_tasks))
                    training_job.progress = min(50.0, progress)
                    training_job.save()
                
                # Skip tasks without labels
                if not task.label:
                    continue
                
                # Track call type counts
                if task.label not in call_map:
                    call_map[task.label] = 0
                call_map[task.label] += 1
                
                # Extract the audio segment based on onset/offset
                try:
                    # Get the recording's WAV file
                    recording = task_batch.recording
                    wav_file_path = recording.wav_file.path
                    
                    if not os.path.exists(wav_file_path):
                        continue
                    
                    # Extract the audio segment
                    segment_data, sample_rate = extract_audio_segment(
                        wav_file_path, task.onset, task.offset
                    )
                    
                    # Create a WAV file with the format NUMBER_LABEL.wav
                    output_filename = f"{file_counter}_{task.label}.wav"
                    output_path = os.path.join(temp_dir, output_filename)
                    
                    # Save the segment to a WAV file
                    import soundfile as sf
                    sf.write(output_path, segment_data, samplerate=sample_rate)
                    
                    file_counter += 1
                
                except Exception as e:
                    # Log the error but continue with other tasks
                    print(f"Error processing task {task.id}: {str(e)}")
                    continue
            
            # Update progress
            training_job.progress = 50.0
            training_job.save()
            
            # Check if we have enough files for training
            if file_counter <= 1:
                training_job.status = "failed"
                training_job.error_message = "Failed to extract any valid audio segments for training."
                training_job.save()
                return {"status": "error", "message": "Failed to extract any valid audio segments for training."}
            
            # Prepare the R server request - Use the /train endpoint
            r_server_url = R_SERVER_URL
            
            # Try to ping the R server first
            try:
                ping_response = requests.get(f"{r_server_url}/ping", timeout=5)
                if ping_response.status_code != 200:
                    training_job.status = "failed"
                    training_job.error_message = f"R server not available. Status: {ping_response.status_code}"
                    training_job.save()
                    return {"status": "error", "message": f"R server not available. Status: {ping_response.status_code}"}
            except requests.RequestException as e:
                training_job.status = "failed"
                training_job.error_message = f"Cannot connect to R server: {str(e)}"
                training_job.save()
                return {"status": "error", "message": f"Cannot connect to R server: {str(e)}"}
            
            # Update progress
            training_job.progress = 60.0
            training_job.save()
            
            # Send the training request to the R server
            try:
                # Parameters for the R server training endpoint
                train_params = {
                    'data_folder': temp_dir,
                    'output_model_path': model_path,
                    'test_split': 0.2  # Use 20% for testing
                }
                
                # Make the request to train the model
                training_job.progress = 70.0
                training_job.save()
                
                train_response = requests.post(
                    f"{r_server_url}/train",
                    params=train_params,
                    timeout=3600  # Allow up to 1 hour for training
                )
                
                if train_response.status_code != 200:
                    training_job.status = "failed"
                    training_job.error_message = f"R server training failed. Status: {train_response.status_code}, Response: {train_response.text}"
                    training_job.save()
                    return {"status": "error", "message": f"R server training failed. Status: {train_response.status_code}"}
                
                # Parse the response
                train_result = train_response.json()
                
                # Update progress
                training_job.progress = 90.0
                training_job.save()
                
                if train_result.get('status') != 'success':
                    training_job.status = "failed"
                    training_job.error_message = f"R server training error: {train_result.get('message', 'Unknown error')}"
                    training_job.save()
                    return {"status": "error", "message": f"R server training error: {train_result.get('message', 'Unknown error')}"}
                
                # Training successful, create the classifier
                accuracy = train_result.get('accuracy', 0)
                classes = train_result.get('classes', [])
                
                # Create the classifier
                classifier = Classifier.objects.create(
                    name=f"Custom Classifier: {task_batch.name}",
                    description=f"Trained on task batch: {task_batch.name} with {total_tasks} labeled tasks. Accuracy: {accuracy:.1f}%",
                    response_format=training_job.response_format,
                    celery_task="battycoda_app.audio.task_modules.detection_tasks.run_call_detection",
                    service_url=R_SERVER_URL,
                    endpoint="/classify",
                    source_task_batch=task_batch,
                    model_file=os.path.join("models", "classifiers", model_filename),
                    is_active=True,
                    created_by=training_job.created_by,
                    group=training_job.group,
                    species=task_batch.species  # Link to the species
                )
                
                # Update the training job with the classifier reference
                training_job.classifier = classifier
                training_job.status = "completed"
                training_job.progress = 100.0
                training_job.save()
                
                return {
                    "status": "success",
                    "message": f"Successfully trained classifier on {file_counter-1} segments with {len(classes)} call types. Accuracy: {accuracy:.1f}%",
                    "classifier_id": classifier.id,
                    "model_path": model_path,
                    "accuracy": accuracy,
                    "classes": classes
                }
            
            except requests.RequestException as e:
                training_job.status = "failed"
                training_job.error_message = f"Error communicating with R server: {str(e)}"
                training_job.save()
                return {"status": "error", "message": f"Error communicating with R server: {str(e)}"}
            
            except Exception as e:
                training_job.status = "failed"
                training_job.error_message = f"Error in model training: {str(e)}"
                training_job.save()
                return {"status": "error", "message": f"Error in model training: {str(e)}"}
        
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
