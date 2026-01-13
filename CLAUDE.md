# BattyCoda Development Guidelines

## Important: Documentation Maintenance
**ALWAYS suggest updating this CLAUDE.md file when implementing significant new features, major changes, or new capabilities.**

## Architecture Overview

BattyCoda is a Django application for annotating and classifying bat call recordings. Key components:

- **Django web app** - Main application (gunicorn on port 8000)
- **Celery worker** - Async task processing (classification, segmentation, spectrograms)
- **Celery beat** - Periodic task scheduler
- **R server** - Plumber API for ML classification (port 8001)
- **PostgreSQL** - Database
- **Redis** - Celery broker
- **Nginx** - Reverse proxy (runs on host, not in Docker)

## Service Management

All services run via systemd (NOT Docker). Service files are in `systemd/` folder.

```bash
# View service status
sudo systemctl status battycoda
sudo systemctl status battycoda-celery
sudo systemctl status battycoda-celery-beat
sudo systemctl status battycoda-r-server

# Restart services
sudo systemctl restart battycoda
sudo systemctl restart battycoda-celery
sudo systemctl restart battycoda-celery-beat

# View logs
sudo journalctl -u battycoda-celery -f
sudo journalctl -u battycoda -f

# After modifying service files in systemd/ folder:
sudo ./systemd/install_services.sh
```

## Python Environment

Always use the virtual environment:
```bash
source venv/bin/activate
python manage.py [command]
```

## Running Tests
```bash
source venv/bin/activate
python manage.py test
python manage.py test battycoda_app.tests.TestClassName.test_method_name
```

## Key Models

### User & Authentication
- **Group** - Organization unit; all resources belong to a group
- **GroupInvitation** - Pending invitations to join a group
- **GroupMembership** - User membership in groups (with admin flag)
- **UserProfile** - Extended user profile (linked to Django User)
- **LoginCode** - Email-based authentication codes
- **PasswordResetToken** - Password reset tokens

### Organization
- **Project** - Projects within a group for organizing recordings
- **Species** - Bat species with image and spectrogram settings
- **Call** - Call types associated with a species

### Recordings & Segmentation
- **Recording** - WAV file uploads with duration and metadata
- **SegmentationAlgorithm** - Algorithm definitions (e.g., amplitude threshold)
- **Segmentation** - A segmentation run on a recording
- **Segment** - Individual detected call within a segmentation

### Classification
- **Classifier** - ML classifier model (KNN or LDA)
- **ClassificationRun** - Classification job for a segmentation
- **ClassificationResult** - Prediction result for a segment
- **CallProbability** - Per-call-type probability from classification
- **ClassifierTrainingJob** - Tracks classifier training from task batches

### Clustering
- **ClusteringAlgorithm** - Algorithm config (kmeans, dbscan, hierarchical, etc.)
- **ClusteringRun** - A clustering job on a segmentation
- **Cluster** - A cluster of similar segments
- **SegmentCluster** - Links segments to clusters
- **ClusterCallMapping** - Maps clusters to call types

### Tasks & Jobs
- **TaskBatch** - Group of annotation tasks created together
- **Task** - Individual annotation task for a segment
- **SpectrogramJob** - Tracks spectrogram generation jobs
- **UserNotification** - User notifications

## Classification System

Classification runs are processed via a queue system:
- Runs are created with status "queued"
- `process_classification_queue` task runs every 30 seconds
- Picks up queued runs and processes them via R server
- Results saved incrementally per batch to avoid memory issues

Key files:
- `battycoda_app/audio/task_modules/classification/run_classification.py`
- `battycoda_app/audio/task_modules/queue_processor.py`

## Clustering System

Clustering groups similar segments together:
- Supports algorithms: kmeans, dbscan, hierarchical, gaussian_mixture, spectral
- Uses acoustic features extracted via the feature extraction module
- Can map clusters to call types for labeling

Key files:
- `battycoda_app/audio/task_modules/clustering/` - Main clustering module

## R Server

The R server runs classification models (KNN, LDA) via plumber API:
- Runs on port 8001
- Single-threaded (processes one request at a time)
- Uses warbleR for acoustic feature extraction
- Models stored in `media/models/classifiers/`

```bash
# Check R server status
curl http://localhost:8001/ping

# R server endpoints:
# POST /predict/knn - KNN classification
# POST /predict/lda - LDA classification
# POST /train/knn - Train KNN model
# POST /train/lda - Train LDA model
```

Key files:
- `R_code/server.R` - Main server
- `R_code/api_endpoints.R` - API endpoint definitions
- `R_code/model_functions/` - Model runner, trainer, and utilities

## Celery Tasks & Beat Schedule

### Scheduled Tasks (Celery Beat)
| Task | Schedule | Description |
|------|----------|-------------|
| `process_classification_queue` | Every 30s | Processes queued classification runs |
| `backup_database_to_s3` | Weekly | Backs up database to S3 |
| `check_disk_usage` | Hourly | Monitors disk usage, sends alerts at 90% |

### Key Tasks
- `calculate_audio_duration` - Calculates recording duration (with retry logic)
- `backup_database_to_s3` - Database backup to S3
- `check_disk_usage` - Disk monitoring with email alerts
- `process_classification_queue` - Queue processor for classification runs
- Classification, segmentation, spectrogram, and clustering tasks in `battycoda_app/audio/task_modules/`

## Management Commands

```bash
source venv/bin/activate

# Database backup
python manage.py backup_database

# Generate missing HDF5 spectrogram files
python manage.py generate_missing_hdf5
python manage.py generate_missing_hdf5 --dry-run  # Preview only

# Import species from CSV
python manage.py import_species

# Initialize default data
python manage.py initialize_defaults

# Populate group memberships
python manage.py populate_memberships
```

## Scripts

Located in `scripts/`:
- `notify_worker_failure.py` - Sends email alerts when workers fail (called by systemd)
- `create_clustering_algorithms.py` - Creates default clustering algorithm entries
- `create_automatic_clustering_algorithms.py` - Creates automatic clustering algorithms

## Simple API

REST API endpoints in `battycoda_app/simple_api/`:
- `recording_upload.py` - Recording upload API (supports auto-split)
- `classification_views.py` - Classification endpoints
- `segmentation_views.py` - Segmentation endpoints
- `task_views.py` - Task management endpoints
- `data_views.py` - Data export endpoints
- `pickle_upload.py` - Pickle file upload for batch data
- `auth.py` - API authentication
- `user_views.py` - User management

## Audio Auto-Split

Long audio files are automatically split on upload:
- Files longer than 60 seconds are split into 1-minute chunks
- Each chunk becomes a separate recording
- Enabled by default (can be disabled via checkbox in upload UI)
- Applies to single upload, batch upload, and API upload

## Memory Monitoring

Celery workers have a memory monitor that dumps profiling info when memory exceeds threshold:
- Threshold: 1.5GB (warning), 2GB (critical)
- Dumps written to `/var/log/battycoda/memory_dump_*.txt`
- Includes tracemalloc allocations, object counts, process info

Key file: `battycoda_app/celery_memory_monitor.py`

## Email Notifications

Uses AWS SES for email. Key notifications:
- Worker failure alerts (via systemd OnFailure directive)
- Disk usage warnings (when usage exceeds 90%)

Key file: `battycoda_app/utils/email_utils.py`

## Environment Configuration

Configuration in `.env` file:

### Required
- `SECRET_KEY` - Django secret key

### Application
- `DOMAIN_NAME` - e.g., battycoda.com
- `DEBUG` - Enable debug mode (default: False)
- `DISABLE_STATIC_CACHING` - Disable whitenoise caching for development
- `MAX_UPLOAD_SIZE_MB` - Max upload size in MB (default: 100)

### Database & Redis
- `DATABASE_URL` - PostgreSQL connection string
- `CELERY_BROKER_URL` - Redis URL for Celery broker
- `CELERY_RESULT_BACKEND` - Redis URL for Celery results

### AWS SES (Email)
- `AWS_SES_REGION_NAME` - AWS region (default: us-east-1)
- `AWS_SES_ACCESS_KEY_ID` - AWS access key
- `AWS_SES_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_SES_CONFIGURATION_SET` - SES configuration set (optional)
- `DEFAULT_FROM_EMAIL` - From address for emails

### Backups
- `DATABASE_BACKUP_BUCKET` - S3 bucket for backups (default: backup-battycoda)
- `DATABASE_BACKUP_PREFIX` - S3 prefix for backups (default: database-backups/)

## Code Style Guidelines

- **Imports**: Group by standard library, Django, then project modules; alphabetize within groups
- **Formatting**: PEP 8, 4-space indentation, ~120 char line limit
- **Naming**: CamelCase for classes, snake_case for functions/variables
- **Error Handling**: Don't use bare `except: pass` - remove the try block or handle properly
- **Frontend**: Prefer Django server-side rendering; Bootstrap 4
- **Comments**: Be sparse, especially when removing code

## Linting

```bash
./lint.sh         # Check code quality
./format.sh       # Auto-format with black and isort
```

## Static Files

After CSS/JS changes:
```bash
source venv/bin/activate
python manage.py collectstatic --noinput
```

## Useful Paths

- Templates: `templates/`
- Static files: `static/`
- Media uploads: `media/`
- Celery logs: `/var/log/battycoda/celery.log`
- Memory dumps: `/var/log/battycoda/memory_dump_*.txt`
- Systemd services: `systemd/`
- R server code: `R_code/`
- Management commands: `battycoda_app/management/commands/`
- Simple API: `battycoda_app/simple_api/`

## Database

```bash
# Django shell
source venv/bin/activate
python manage.py shell

# Example queries:
from battycoda_app.models.classification import ClassificationRun
run = ClassificationRun.objects.get(id=123)
run.status  # queued, pending, in_progress, completed, failed
run.results.count()
```

## Common Issues

**Classification runs failing at ~88%**: Usually memory-related. Check:
1. Memory dumps in `/var/log/battycoda/`
2. Multiple large runs processing concurrently
3. R server memory usage: `ps aux | grep R`

**Celery OOM killed**: Check systemd logs:
```bash
sudo journalctl -u battycoda-celery | grep -i oom
```

**R server not responding**:
```bash
curl http://localhost:8001/ping
ps aux | grep "R.*server"
```

**Disk usage alerts**: Check current usage:
```bash
df -h / /home
```
