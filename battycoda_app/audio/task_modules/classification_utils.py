"""
Classification utility functions for BattyCoda.

Shared utilities for classification and training tasks including R server communication.
"""

import requests

# Centralized configuration
R_SERVER_URL = "http://localhost:8001"

# ---------------------------------------------------------------
# Common Utility Functions
# ---------------------------------------------------------------


def update_classification_run_status(classification_run, status, message=None, progress=None):
    """Update a classification run's status and related fields."""
    update_fields = []
    if status:
        classification_run.status = status
        update_fields.append("status")
    if message:
        classification_run.error_message = message
        update_fields.append("error_message")
    if progress is not None:
        classification_run.progress = progress
        update_fields.append("progress")
    classification_run.save(update_fields=update_fields)

    return classification_run


# Backward compatibility alias - to be removed
update_detection_run_status = update_classification_run_status


def check_r_server_connection(service_url=R_SERVER_URL):
    """Check if the R server is available."""
    try:
        ping_response = requests.get(f"{service_url}/ping", timeout=5)
        if ping_response.status_code == 200:
            return True, None
        return False, f"Classifier service unavailable. Status: {ping_response.status_code}"
    except requests.RequestException as e:
        return False, f"Cannot connect to classifier service: {str(e)}"


def get_call_types(species):
    """Get all call types for a species."""
    from ...models.organization import Call

    calls = Call.objects.filter(species=species)
    if not calls:
        return None, "No call types found for this species"
    return calls, None


def get_segments(recording, segmentation=None):
    """Get all segments for a recording or segmentation."""
    from ...models import Segment

    if segmentation:
        segments = Segment.objects.filter(segmentation=segmentation)
    else:
        segments = Segment.objects.filter(recording=recording)

    if not segments:
        return None, "No segments found in recording"
    return segments, None


def create_equal_probabilities(detection_result, calls):
    """Create equal probability records for all calls."""
    from ...models.classification import CallProbability

    equal_prob = 1.0 / len(calls)
    for call in calls:
        CallProbability.objects.create(classification_result=detection_result, call=call, probability=equal_prob)


def process_classification_result(classifier, result, prediction_data, calls):
    """Process the response from the classifier service and create probability records."""
    from ...models.classification import CallProbability

    if classifier.response_format == "highest_only":
        # For highest-only algorithm type
        if "call_type" in prediction_data and "confidence" in prediction_data:
            predicted_call_name = prediction_data["call_type"]
            confidence = float(prediction_data["confidence"]) / 100.0  # Convert percentage to 0-1

            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, confidence))

            # Find the call by name
            matching_calls = [call for call in calls if call.short_name == predicted_call_name]

            if matching_calls:
                predicted_call = matching_calls[0]

                # Create probability record for predicted call
                CallProbability.objects.create(
                    classification_result=result, call=predicted_call, probability=confidence
                )

                # Create zero probability records for all other calls
                for call in calls:
                    if call.short_name != predicted_call_name:
                        CallProbability.objects.create(classification_result=result, call=call, probability=0.0)
            else:
                # Call not found - create even probabilities
                create_equal_probabilities(result, calls)
        else:
            # Missing required fields - create equal probabilities
            create_equal_probabilities(result, calls)

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
                CallProbability.objects.create(classification_result=result, call=call, probability=prob_value)
        else:
            # Missing probabilities - create equal probabilities
            create_equal_probabilities(result, calls)


# No explicit imports of Celery tasks here to avoid circular imports
# The tasks will be discovered by Celery automatically
