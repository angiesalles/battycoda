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

## Classification System

Classification runs are processed via a queue system:
- Runs are created with status "queued"
- `process_classification_queue` task runs every 30 seconds
- Picks up queued runs and processes them via R server
- Results saved incrementally per batch to avoid memory issues

Key files:
- `battycoda_app/audio/task_modules/classification/run_classification.py`
- `battycoda_app/audio/task_modules/queue_processor.py`

## Memory Monitoring

Celery workers have a memory monitor that dumps profiling info when memory exceeds threshold:
- Threshold: 1.5GB (warning), 2GB (critical)
- Dumps written to `/var/log/battycoda/memory_dump_*.txt`
- Includes tracemalloc allocations, object counts, process info

## Email Notifications

Worker failures trigger email alerts to admins (configured in `settings.py` ADMINS):
- Uses AWS SES
- Triggered via systemd OnFailure directive
- Script: `scripts/notify_worker_failure.py`

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

## Key Models

- **Group** - All resources belong to a group
- **Species** - Bat species with associated call types
- **Recording** - WAV file uploads
- **Segmentation** - Detected segments in a recording
- **Segment** - Individual detected call
- **ClassificationRun** - Classification job for a segmentation
- **ClassificationResult** - Prediction for a segment

## Environment Configuration

Configuration in `.env` file:
- `SECRET_KEY` - Django secret key (required)
- `DOMAIN_NAME` - e.g., battycoda.com
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` / `CELERY_BROKER_URL` - Redis connection
- `AWS_SES_*` - Email configuration

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
