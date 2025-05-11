"""
Classification tasks for BattyCoda.

This module contains tasks for running call detection and classification.
"""
import json
import os
import tempfile
from pathlib import Path

import requests
import soundfile as sf
from celery import shared_task
from django.conf import settings
from django.db import transaction

from .base import extract_audio_segment
from .detection_tasks import (R_SERVER_URL, check_r_server_connection,
                             get_call_types, get_segments,
                             update_detection_run_status)


@shared_task(bind=True, name="battycoda_app.audio.task_modules.classification_tasks.run_call_detection")
def run_call_detection(self, detection_run_id):
    """
    Run automated call classification on segments using the configured classifier.
    Uses the R server /classify endpoint to classify audio segments.
    
    Processes segments in small batches for better progress tracking and reliability.

    Args:
        detection_run_id: ID of the DetectionRun model

    Returns:
        dict: Result of the classification process
    """
    from ...models.detection import CallProbability, Classifier, DetectionResult, DetectionRun

    try:
        # Get the detection run
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        
        # Update status to in progress
        update_detection_run_status(detection_run, "in_progress", progress=0)

        # Get the classifier to use
        classifier = detection_run.classifier
        
        # If no classifier is specified, try to get the default KNN E. fuscus classifier
        if not classifier:
            try:
                classifier = Classifier.objects.get(name="KNN E. fuscus")
            except Classifier.DoesNotExist:
                try:
                    classifier = Classifier.objects.get(name="R-direct Classifier")
                except Classifier.DoesNotExist:
                    update_detection_run_status(detection_run, "failed", "No classifier specified and default classifier not found")
                    return {"status": "error", "message": "No classifier specified and default classifier not found"}

        # Configure the service URL and endpoint
        service_url = classifier.service_url
        endpoint = f"{service_url}{classifier.endpoint}"

        # Get the recording and check if the WAV file exists
        recording = detection_run.segmentation.recording
        if not recording.wav_file or not os.path.exists(recording.wav_file.path):
            update_detection_run_status(detection_run, "failed", f"WAV file not found for recording {recording.id}")
            return {"status": "error", "message": f"WAV file not found: {recording.wav_file.path if recording.wav_file else None}"}

        # Test the R server connection
        server_ok, error_msg = check_r_server_connection(service_url)
        if not server_ok:
            update_detection_run_status(detection_run, "failed", error_msg)
            return {"status": "error", "message": error_msg}

        # Get all segments and call types
        segments, seg_error = get_segments(recording, detection_run.segmentation)
        if not segments:
            update_detection_run_status(detection_run, "failed", seg_error)
            return {"status": "error", "message": seg_error}
            
        calls, call_error = get_call_types(recording.species)
        if not calls:
            update_detection_run_status(detection_run, "failed", call_error)
            return {"status": "error", "message": call_error}

        # Process segments in smaller batches for better progress tracking
        try:
            # Get total number of segments and prepare for batch processing
            total_segments = segments.count()
            segment_list = list(segments)  # Convert queryset to list for easier batching
            
            # Store all classification results
            all_classification_results = []
            
            # Get model path if we have a custom model
            model_path = None
            if classifier.model_file:
                # Use the model file path directly (since it now includes the full path from project root)
                model_path = os.path.join(settings.BASE_DIR, classifier.model_file)
                if not os.path.exists(model_path):
                    raise ValueError(f"Model file not found: {model_path}")
            
            print(f"Model path: {model_path}")
            
            # Determine the batch size - aim for approximately 100 batches
            # But ensure minimum batch size is 5 and maximum is 50 for reasonable performance
            batch_size = max(5, min(50, total_segments // 100 + 1))
            num_batches = (total_segments + batch_size - 1) // batch_size  # Ceiling division
            
            print(f"Processing {total_segments} segments in {num_batches} batches (batch size: {batch_size})")
            
            # Process each batch separately
            for batch_index in range(num_batches):
                # Calculate start and end indices for this batch
                start_idx = batch_index * batch_size
                end_idx = min(start_idx + batch_size, total_segments)
                
                # Get the segments for this batch
                batch_segments = segment_list[start_idx:end_idx]
                
                print(f"Processing batch {batch_index+1}/{num_batches} ({len(batch_segments)} segments)")
                
                # Create a shared temporary directory for this batch
                # Using a directory both containers can access
                shared_tmp_dir = os.path.join(settings.BASE_DIR, 'tmp')
                os.makedirs(shared_tmp_dir, exist_ok=True)
                
                # Create a temporary directory for this batch
                batch_dir_name = f"batch_{batch_index}_{detection_run.id}"
                batch_dir = os.path.join(shared_tmp_dir, batch_dir_name)
                os.makedirs(batch_dir, exist_ok=True)
                
                try:
                    # Mapping of filename to segment ID for this batch
                    segment_map = {}
                    
                    # Extract audio segments for this batch
                    for i, segment in enumerate(batch_segments):
                        # Extract audio segment from WAV file
                        segment_data, sample_rate = extract_audio_segment(
                            recording.wav_file.path, segment.onset, segment.offset
                        )
                        
                        # Generate unique filename for this segment
                        segment_filename = f"segment_{segment.id}.wav"
                        segment_path = os.path.join(batch_dir, segment_filename)
                        
                        # Save the segment as a WAV file
                        sf.write(segment_path, segment_data, samplerate=sample_rate)
                        
                        # Store mapping of filename to segment ID
                        segment_map[segment_filename] = segment.id
                    
                    # Prepare parameters for the batch classification
                    # Use the path relative to /app in the docker container for R server
                    # since both containers mount the project at /app
                    r_server_path = os.path.join('/app', 'tmp', batch_dir_name)
                    params = {
                        "wav_folder": r_server_path,
                        "model_path": model_path
                    }
                    
                    # Call the classifier service for this batch
                    print(f"Calling classifier service for batch {batch_index+1} at {endpoint}...")
                    print(f"Parameters: {params}")
                    
                    # IMPORTANT: Use data parameter instead of params to send as form data
                    response = requests.post(endpoint, data=params, timeout=60)  # 60 sec timeout per batch
                    
                    if response.status_code != 200:
                        raise RuntimeError(f"Classifier service error for batch {batch_index+1}: Status {response.status_code} - {response.text}")
                    
                    # Debug the raw response before parsing JSON
                    print(f"Raw response text: {response.text[:200]}...")  # Print first 200 chars
                    
                    # Process the batch response
                    try:
                        prediction_data = response.json()
                        print(f"Response JSON keys: {list(prediction_data.keys())}")
                        print(f"Response status: {prediction_data.get('status', 'NO_STATUS_FIELD')}")
                    except Exception as json_error:
                        raise ValueError(f"Failed to parse JSON response: {str(json_error)}, raw response: {response.text[:200]}...")
                    
                    # Handle both string and list format for status
                    status_value = prediction_data.get('status')
                    is_success = (status_value == 'success' or 
                                 (isinstance(status_value, list) and len(status_value) > 0 and status_value[0] == 'success'))
                    
                    if not is_success:
                        raise ValueError(f"Classifier returned error for batch {batch_index+1}: {prediction_data.get('message', 'Unknown error')}")
                    
                    # Get file results from response
                    file_results = prediction_data.get('file_results', {})
                    
                    if not file_results:
                        print(f"Warning: No classification results returned for batch {batch_index+1}")
                    else:
                        print(f"Received {len(file_results)} classification results for batch {batch_index+1}")
                        
                        # Store the results from this batch
                        for filename, result_data in file_results.items():
                            segment_id = segment_map.get(filename)
                            if segment_id:
                                # Unwrap list values for consistency
                                processed_data = {}
                                for key, value in result_data.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        processed_data[key] = value[0]
                                    else:
                                        processed_data[key] = value
                                
                                # Handle class_probabilities specially since it's a nested structure
                                if 'class_probabilities' in result_data:
                                    prob_data = result_data['class_probabilities']
                                    if isinstance(prob_data, list) and len(prob_data) > 0:
                                        processed_data['class_probabilities'] = prob_data[0]
                                
                                all_classification_results.append((segment_id, processed_data))
                    
                    # Update progress after each batch - reserve 10% for database operations at the end
                    batch_progress = 90 * ((batch_index + 1) / num_batches)
                    update_detection_run_status(detection_run, status="in_progress", progress=batch_progress)
                    
                except Exception as batch_error:
                    print(f"Error processing batch {batch_index+1}: {str(batch_error)}")
                    raise batch_error
                finally:
                    # Clean up temporary directory
                    try:
                        import shutil
                        shutil.rmtree(batch_dir, ignore_errors=True)
                    except Exception as cleanup_error:
                        print(f"Warning: Could not clean up temporary directory {batch_dir}: {str(cleanup_error)}")
            
            # Now process all collected results and save to database
            print(f"Processing {len(all_classification_results)} total classification results...")
            
            # Calculate how many results were successfully processed
            success_rate = len(all_classification_results) / total_segments * 100
            print(f"Successfully classified {success_rate:.1f}% of segments")
            
            # Save all results to database in a single transaction
            with transaction.atomic():
                for i, (segment_id, result_data) in enumerate(all_classification_results):
                    # Get the segment
                    segment = segments.get(id=segment_id)
                    
                    # Create a detection result
                    result = DetectionResult.objects.create(detection_run=detection_run, segment=segment)
                    
                    # Get predicted class and probabilities
                    predicted_class = result_data.get('predicted_class')
                    class_probabilities = result_data.get('class_probabilities', {})
                    
                    # Save class probabilities
                    for call in calls:
                        # Get probability for this call type - handle missing values gracefully
                        if call.short_name not in class_probabilities:
                            # Use 0.0 probability for call types not predicted by the model
                            probability = 0.0
                            print(f"Note: Call type '{call.short_name}' not found in prediction results, using 0.0 probability")
                        else:
                            probability = class_probabilities[call.short_name]
                            # Handle case where probability is not a number
                            if not isinstance(probability, (int, float)):
                                # Try extracting from list if it's a list with one numeric element
                                if isinstance(probability, list) and len(probability) == 1 and isinstance(probability[0], (int, float)):
                                    probability = probability[0]
                                    print(f"Note: Extracted {probability} from list for call type '{call.short_name}'")
                                else:
                                    # If it's still not a valid number, use 0.0 as fallback
                                    print(f"Warning: Invalid probability value for call type '{call.short_name}': '{probability}', using 0.0")
                                    probability = 0.0
                            
                        # Convert from percentage to 0-1 range
                        prob_value = probability / 100.0
                        
                        # Ensure probability is within valid range
                        prob_value = max(0.0, min(1.0, float(prob_value)))
                        
                        # Create probability record
                        CallProbability.objects.create(
                            detection_result=result, 
                            call=call, 
                            probability=prob_value
                        )
                    
                    # Update progress occasionally during database saves (90%-100%)
                    if i % 20 == 0 or i == len(all_classification_results) - 1:  # Update every 20 saves or at the end
                        save_progress = 90 + 10 * (i / len(all_classification_results))
                        update_detection_run_status(detection_run, status="in_progress", progress=save_progress)
            
            # Mark as completed
            update_detection_run_status(detection_run, "completed", progress=100)
            
            return {
                "status": "success",
                "message": f"Successfully processed {total_segments} segments using classifier: {classifier.name}",
                "detection_run_id": detection_run_id,
            }
            
        except Exception as error:
            # Handle any error during processing
            update_detection_run_status(detection_run, "failed", str(error))
            raise error

    except Exception as e:
        # Update run status and return error
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        update_detection_run_status(detection_run, "failed", str(e))
        return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="battycoda_app.audio.task_modules.classification_tasks.run_dummy_classifier")
def run_dummy_classifier(self, detection_run_id):
    """
    Dummy classifier that assigns equal probability to all call types.
    This is for testing purposes only and doesn't perform actual classification.

    Args:
        detection_run_id: ID of the DetectionRun model

    Returns:
        dict: Result of the dummy classification process
    """
    from ...models.detection import CallProbability, DetectionResult, DetectionRun
    
    try:
        # Get the detection run
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        
        # Update status
        update_detection_run_status(detection_run, "in_progress", progress=0)
        
        # Get recording and segments
        recording = detection_run.segmentation.recording
        segments, seg_error = get_segments(recording, detection_run.segmentation)
        if not segments:
            update_detection_run_status(detection_run, "failed", seg_error)
            return {"status": "error", "message": seg_error}
            
        # Get call types
        calls, call_error = get_call_types(recording.species)
        if not calls:
            update_detection_run_status(detection_run, "failed", call_error)
            return {"status": "error", "message": call_error}
        
        # Calculate equal probability
        equal_probability = 1.0 / calls.count()
        
        # Total segments for progress tracking
        total_segments = segments.count()
        
        # Process each segment with equal probabilities
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
                
                # Update progress
                progress = ((i + 1) / total_segments) * 100
                update_detection_run_status(detection_run, "in_progress", progress=progress)
                
            except Exception as segment_error:
                # Log error but continue with other segments
                continue
        
        # Mark as completed
        update_detection_run_status(detection_run, "completed", progress=100)
        
        return {
            "status": "success",
            "message": f"Successfully processed {total_segments} segments with dummy classifier",
            "detection_run_id": detection_run_id,
        }
        
    except Exception as e:
        # Update run status and return error
        detection_run = DetectionRun.objects.get(id=detection_run_id)
        update_detection_run_status(detection_run, "failed", str(e))
        return {"status": "error", "message": str(e)}
