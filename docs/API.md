# BattyCoda API Documentation

This document describes the APIs available in BattyCoda for integration and extension.

## Overview

BattyCoda provides two types of APIs:

1. **Django REST API**: For web and mobile client integration
2. **R API Endpoints**: For audio processing and machine learning tasks

## Django REST API

### Authentication

All API endpoints require authentication using Django's session-based authentication or token authentication.

To use token authentication:

1. Obtain a token:
   ```
   POST /api/auth/token/
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

2. Include the token in subsequent requests:
   ```
   Authorization: Token your_token_here
   ```

### Recordings API

#### List Recordings

```
GET /api/recordings/
```

Response:
```json
[
  {
    "id": 1,
    "name": "Recording1",
    "description": "Night recording from site A",
    "duration": 120.5,
    "species": {
      "id": 1,
      "name": "Eptesicus fuscus"
    },
    "project": {
      "id": 1,
      "name": "Summer 2023 Survey"
    },
    "created_at": "2023-06-15T20:45:32Z"
  },
  ...
]
```

#### Get Recording Details

```
GET /api/recordings/{id}/
```

Response:
```json
{
  "id": 1,
  "name": "Recording1",
  "description": "Night recording from site A",
  "duration": 120.5,
  "sample_rate": 44100,
  "species": {
    "id": 1,
    "name": "Eptesicus fuscus"
  },
  "project": {
    "id": 1,
    "name": "Summer 2023 Survey"
  },
  "location": "Forest edge, site A",
  "equipment": "Pettersson D500X",
  "recorded_date": "2023-06-10",
  "created_at": "2023-06-15T20:45:32Z",
  "segments": [
    {
      "id": 1,
      "onset": 2.4,
      "offset": 3.2
    },
    ...
  ]
}
```

#### Create Recording

```
POST /api/recordings/
```

Request:
```json
{
  "name": "New Recording",
  "description": "Recording from location B",
  "species": 1,
  "project": 1,
  "wav_file": [binary data]
}
```

### Segments API

#### List Segments

```
GET /api/segments/?recording_id={recording_id}
```

Response:
```json
[
  {
    "id": 1,
    "recording": 1,
    "onset": 2.4,
    "offset": 3.2,
    "notes": "Clear call sequence"
  },
  ...
]
```

#### Create Segment

```
POST /api/segments/
```

Request:
```json
{
  "recording": 1,
  "onset": 15.2,
  "offset": 16.1,
  "notes": "Feeding buzz"
}
```

### Tasks API

#### List Tasks

```
GET /api/tasks/?batch_id={batch_id}
```

Response:
```json
[
  {
    "id": 1,
    "wav_file_name": "Recording1.wav",
    "onset": 2.4,
    "offset": 3.2,
    "status": "pending",
    "label": null,
    "notes": ""
  },
  ...
]
```

#### Update Task

```
PATCH /api/tasks/{id}/
```

Request:
```json
{
  "status": "done",
  "label": "echolocation calls",
  "notes": "Clear FM sweep pattern"
}
```

### Classification API

#### Run Classification

```
POST /api/classify/
```

Request:
```json
{
  "classifier_id": 1,
  "recording_ids": [1, 2, 3]
}
```

Response:
```json
{
  "run_id": 42,
  "status": "pending",
  "message": "Classification job started"
}
```

#### Get Classification Results

```
GET /api/classify/results/{run_id}/
```

Response:
```json
{
  "run_id": 42,
  "status": "completed",
  "created_at": "2023-06-20T14:25:11Z",
  "results": [
    {
      "segment_id": 1,
      "prediction": "echolocation calls",
      "confidence": 0.92
    },
    ...
  ]
}
```

## R API Endpoints

The R API is primarily used internally by the Django application but can be accessed directly for advanced usage.

### Base URL

The R API is accessible at:

```
http://localhost:8000/r-api/
```

### Health Check

```
GET /r-api/ping
```

Response:
```json
{
  "status": "alive",
  "timestamp": "2023-06-20 14:30:22",
  "r_version": "R version 4.2.0"
}
```

### Prediction API

#### KNN Prediction

```
POST /r-api/predict/knn
```

Parameters:
- `wav_folder`: Path to folder containing WAV files
- `model_path`: Full path to the model file

Response:
```json
{
  "status": "success",
  "predictions": [
    {
      "file": "call1.wav",
      "prediction": "echolocation calls",
      "probability": 0.85
    },
    ...
  ],
  "summary": {
    "total": 10,
    "by_class": {
      "echolocation calls": 8,
      "social calls": 2
    }
  }
}
```

#### LDA Prediction

```
POST /r-api/predict/lda
```

Parameters:
- `wav_folder`: Path to folder containing WAV files
- `model_path`: Full path to the model file

Response: Same format as KNN prediction

### Training API

#### Train KNN Model

```
POST /r-api/train/knn
```

Parameters:
- `data_folder`: Path to training data directory
- `output_model_path`: Full path where the model should be saved
- `test_split`: Fraction of data to use for testing (0.0-1.0)

Response:
```json
{
  "status": "success",
  "model_info": {
    "type": "knn",
    "training_files": 120,
    "classes": ["echolocation calls", "social calls", "noise"],
    "accuracy": 0.92,
    "model_path": "/app/data/models/knn_model.RData"
  },
  "confusion_matrix": [
    [28, 1, 1],
    [2, 25, 3],
    [0, 2, 38]
  ],
  "class_metrics": {
    "echolocation calls": {
      "precision": 0.93,
      "recall": 0.88,
      "f1_score": 0.90
    },
    ...
  }
}
```

#### Train LDA Model

```
POST /r-api/train/lda
```

Parameters:
- `data_folder`: Path to training data directory
- `output_model_path`: Full path where the model should be saved
- `test_split`: Fraction of data to use for testing (0.0-1.0)

Response: Same format as KNN training

## Websocket API

BattyCoda also provides real-time updates through websockets.

### Connect to Websocket

```
ws://your-server/ws/notifications/
```

Authentication required via Django session or token in the URL:
```
ws://your-server/ws/notifications/?token=your_token_here
```

### Message Format

Incoming messages:

```json
{
  "type": "task_status_change",
  "data": {
    "task_id": 42,
    "status": "completed",
    "updated_at": "2023-06-20T14:35:22Z"
  }
}
```

Message types:
- `task_status_change`: When a task status changes
- `segmentation_progress`: Progress updates during segmentation
- `classification_complete`: When a classification run completes
- `notification`: General user notifications

## Error Handling

All API endpoints return standard HTTP status codes:

- 200: Success
- 400: Bad request
- 401: Unauthorized
- 403: Forbidden
- 404: Not found
- 500: Server error

Error responses include a message:

```json
{
  "error": "Invalid parameters",
  "detail": "The following parameters are required: data_folder, output_model_path"
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- Authenticated users: 100 requests per minute
- Unauthenticated users: 20 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623345600
```

## Integration Examples

### Python Example

```python
import requests

# Authenticate
response = requests.post('https://your-server/api/auth/token/', {
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['token']

# Get recordings
headers = {'Authorization': f'Token {token}'}
recordings = requests.get('https://your-server/api/recordings/', headers=headers)

# Process results
for recording in recordings.json():
    print(f"Recording: {recording['name']}, Duration: {recording['duration']}s")
```

### R Example

```r
library(httr)
library(jsonlite)

# Call the R API directly
result <- POST(
  "http://your-server/r-api/predict/knn",
  body = list(
    wav_folder = "/path/to/wav/files",
    model_path = "/path/to/model.RData"
  ),
  encode = "json"
)

# Process the response
prediction_data <- content(result)
cat("Prediction results:", toJSON(prediction_data, pretty=TRUE))
```

## Further Documentation

For detailed information about the API methods, parameters, and responses, access the interactive API documentation at:

```
https://your-server/api/docs/
```

## Support

For API support, contact the BattyCoda development team or open an issue on the GitHub repository.