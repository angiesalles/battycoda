# BattyCoda API Documentation

## Overview
BattyCoda provides a simple, API key-based REST API designed for easy integration with R scripts and other programmatic clients. The API enables the complete classification workflow: upload recordings → segment → classify → create task batches → annotate.

## Authentication
- **Method**: API Key authentication via query parameter or POST data
- **Parameter**: `api_key`
- **Example**: `GET /simple-api/species/?api_key=your_key_here`

## Base URL
```
https://yourdomain.com/simple-api/
```

## Core Classification Workflow

The typical workflow for classification is:

1. **Upload a recording** (`POST /upload/`)
2. **Segment the recording** (`POST /recordings/{id}/segment/`)
3. **Run classification** (`POST /recordings/{id}/classify/`)
4. **Check classification status** (`GET /classification-runs/`)
5. **Create task batch for review** (`POST /classification-runs/{id}/create-task-batch/`)
6. **Review and annotate tasks** (`GET /task-batches/{id}/tasks/`)

## Endpoints

### 1. User Management

#### Get User Info
```
GET /simple-api/user/?api_key={api_key}
```
Returns information about the current user.

#### Generate API Key
```
POST /simple-api/generate-key/?api_key={api_key}
```
Generates a new API key for the user (requires existing valid API key).

### 2. Data Listing

#### List Species
```
GET /simple-api/species/?api_key={api_key}
```
Returns all species available to the user's group.

#### List Projects
```
GET /simple-api/projects/?api_key={api_key}
```
Returns all projects available to the user's group.

#### List Recordings
```
GET /simple-api/recordings/?api_key={api_key}
```
Optional parameters:
- `project_id`: Filter recordings by project

#### List Classifiers
```
GET /simple-api/classifiers/?api_key={api_key}
```
Returns all ML classifiers available to the user (e.g., Carollia, Efuscus models).

**Response:**
```json
{
  "success": true,
  "classifiers": [
    {
      "id": 1,
      "name": "LDA Carollia",
      "description": "Linear Discriminant Analysis classifier for Carollia perspicillata",
      "species_name": "Carollia perspicillata",
      "species_id": 1,
      "response_format": "full_probability"
    }
  ],
  "count": 1
}
```

### 3. File Upload

#### Upload Recording
```
POST /simple-api/upload/?api_key={api_key}
```
Uploads a new audio recording.

**Required Parameters:**
- `name`: Recording name
- `species_id`: Species ID
- `wav_file`: WAV file upload

**Optional Parameters:**
- `project_id`: Project ID
- `description`: Recording description
- `location`: Recording location
- `recorded_date`: Date recorded (YYYY-MM-DD format)

### 4. Classification Workflow

#### Start Classification
```
POST /simple-api/recordings/{recording_id}/classify/?api_key={api_key}
```
Starts classification on a recording's segments.

**Required Parameters:**
- `classifier_id`: ID of classifier to use

**Optional Parameters:**
- `name`: Custom name for the classification run

**Response:**
```json
{
  "success": true,
  "message": "Classification started using LDA Carollia",
  "classification_run": {
    "id": 1,
    "name": "LDA Carollia_on_recording_20250706_1420",
    "status": "queued",
    "classifier_name": "LDA Carollia",
    "recording_name": "my_recording.wav",
    "task_id": "task-uuid",
    "created_at": "2025-07-06T14:20:30Z"
  }
}
```

#### List Classification Runs
```
GET /simple-api/classification-runs/?api_key={api_key}
```
Lists classification runs and their status.

**Optional Parameters:**
- `recording_id`: Filter by recording

**Response:**
```json
{
  "success": true,
  "classification_runs": [
    {
      "id": 1,
      "name": "LDA Carollia_on_recording_20250706_1420",
      "status": "completed",
      "progress": 100,
      "classifier_name": "LDA Carollia",
      "recording_name": "my_recording.wav",
      "species_name": "Carollia perspicillata",
      "created_at": "2025-07-06T14:20:30Z",
      "result_summary": {
        "echolocation calls": 45,
        "distress calls": 3,
        "noise": 12
      }
    }
  ]
}
```

#### Create Task Batch
```
POST /simple-api/classification-runs/{run_id}/create-task-batch/?api_key={api_key}
```
Creates a task batch from completed classification for manual review.

**Required Parameters:**
- `name`: Task batch name

**Optional Parameters:**
- `description`: Task batch description
- `confidence_threshold`: Only include calls with confidence below this threshold (0-1)

**Response:**
```json
{
  "success": true,
  "message": "Task batch created successfully",
  "task_batch": {
    "id": 1,
    "name": "Review Carollia Classifications",
    "description": "Manual review of low-confidence calls",
    "species_name": "Carollia perspicillata",
    "total_tasks": 23,
    "created_at": "2025-07-06T14:25:30Z"
  }
}
```

### 5. Task Management

#### List Task Batches
```
GET /simple-api/task-batches/?api_key={api_key}
```
Lists existing task batches.

**Optional Parameters:**
- `project_id`: Filter by project

#### List Tasks in Batch
```
GET /simple-api/task-batches/{batch_id}/tasks/?api_key={api_key}
```
Lists tasks in a batch for annotation.

**Optional Parameters:**
- `call_type`: Filter by call type
- `limit`: Number of tasks per page (default: 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "success": true,
  "task_batch": {
    "id": 1,
    "name": "Review Carollia Classifications",
    "species_name": "Carollia perspicillata",
    "available_call_types": ["echolocation calls", "distress calls", "noise"]
  },
  "tasks": [
    {
      "id": 1,
      "onset": 1.25,
      "offset": 1.8,
      "label": null,
      "classification_result": "echolocation calls",
      "confidence": 0.73,
      "is_done": false,
      "status": "pending"
    }
  ],
  "pagination": {
    "total": 23,
    "limit": 50,
    "offset": 0,
    "has_next": false,
    "has_previous": false
  }
}
```

**Parameters:**
- `file`: Audio file (WAV format recommended)
- `project_id`: ID of the project (optional)
- `species_id`: ID of the species (optional)
- `filename`: Custom filename (optional)

**Response:**
```json
{
  "success": true,
  "recording_id": 123,
  "message": "Recording uploaded successfully"
}
```

### 4. Segmentation

#### Start Segmentation
```
POST /simple-api/recordings/{recording_id}/segment/?api_key={api_key}
```
Starts automatic segmentation of a recording.

**Parameters:**
- `algorithm_id`: ID of segmentation algorithm (optional)

**Response:**
```json
{
  "success": true,
  "segmentation_id": 456,
  "status": "in_progress"
}
```

#### List Segmentation Algorithms
```
GET /simple-api/algorithms/?api_key={api_key}
```
Returns available segmentation algorithms.

**Response:**
```json
{
  "algorithms": [
    {
      "id": 1,
      "name": "Default Segmentation",
      "description": "Standard bat call segmentation"
    }
  ]
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "status": "error"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (missing parameters)
- `401`: Unauthorized (invalid/missing API key)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

## Usage Examples

### R Script Example
```r
library(httr)
library(jsonlite)

api_key <- "your_api_key_here"
base_url <- "https://yourdomain.com/simple-api"

# List species
response <- GET(paste0(base_url, "/species/"), 
               query = list(api_key = api_key))
species_data <- content(response, "parsed")

# Upload a file
upload_response <- POST(paste0(base_url, "/upload/"),
                       body = list(
                         api_key = api_key,
                         file = upload_file("recording.wav"),
                         project_id = 1
                       ),
                       encode = "multipart")
```

### Python Example
```python
import requests

api_key = "your_api_key_here"
base_url = "https://yourdomain.com/simple-api"

# List recordings
response = requests.get(f"{base_url}/recordings/", 
                       params={"api_key": api_key})
recordings = response.json()

# Upload file
with open("recording.wav", "rb") as f:
    response = requests.post(f"{base_url}/upload/",
                           data={"api_key": api_key, "project_id": 1},
                           files={"file": f})
```

## Getting an API Key

1. Log into the BattyCoda web interface
2. Go to Profile → Account Settings  
3. Click "Generate API Key"
4. Copy and securely store your key

## Rate Limits

Currently no rate limits are enforced, but reasonable usage is expected.

---

This API is specifically designed to be simple and easy to use from R scripts and other automated tools, avoiding the complexity of OAuth or session-based authentication.