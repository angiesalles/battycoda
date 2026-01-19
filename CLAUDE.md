# BattyCoda Development Guidelines

## Documentation Maintenance
**ALWAYS suggest updating this CLAUDE.md file when implementing significant new features, major changes, or new capabilities.**

## Task Tracking with Beads

This repository uses [Beads](https://github.com/steveyegge/beads) for task tracking. Run `bd onboard` to get started.

### Common Commands
| Command | Description |
|---------|-------------|
| `bd ready` | Show tasks without blockers |
| `bd list` | List all open issues |
| `bd show <id>` | View issue details |
| `bd create "Title" -p 1 -t task` | Create task with priority 1 |
| `bd update <id> --status in_progress` | Claim work |
| `bd close <id>` | Complete work |
| `bd sync` | Sync with git |

### Workflow
1. `bd ready` - Find available work
2. `bd update <id> --status in_progress` - Claim it
3. `bd close <id> --reason "Description"` - Complete it
4. Create new tasks as you discover them

### Landing the Plane (Session Completion)

**MANDATORY WORKFLOW** - Work is NOT complete until `git push` succeeds:

1. File issues for remaining work
2. Run quality gates (if code changed)
3. Update issue status
4. **PUSH TO REMOTE**:
   ```bash
   git pull --rebase && bd sync && git push
   git status  # MUST show "up to date with origin"
   ```
5. Clean up stashes, verify all changes pushed

### Project Terminology

**puntomatic** - When the user says "puntomatic", it means:
1. Yes, it's OK to suppress/defer the warning for now
2. BUT you MUST add a reminder to the relevant bead to remove the suppression when the real fix is implemented
3. Read back this definition to acknowledge you remember it

## Architecture Overview

BattyCoda is a Django application for annotating and classifying bat call recordings.

| Component | Description |
|-----------|-------------|
| Django web app | Main application (gunicorn on port 8000) |
| Celery worker | Async task processing |
| Celery beat | Periodic task scheduler |
| R server | Plumber API for ML classification (port 8001) |
| PostgreSQL | Database |
| Redis | Celery broker |
| Nginx | Reverse proxy (runs on host) |

All services run via **systemd** (NOT Docker). Service files in `systemd/`.

## Quick Reference

### Service Management
```bash
# Status
sudo systemctl status battycoda battycoda-celery battycoda-celery-beat battycoda-r-server

# Restart
sudo systemctl restart battycoda battycoda-celery battycoda-celery-beat

# Logs
sudo journalctl -u battycoda-celery -f

# After modifying systemd files:
sudo ./systemd/install_services.sh
```

### Python Environment
```bash
source venv/bin/activate
python manage.py [command]
```

### Development
```bash
# Quick start (recommended) - runs Django, Vite, Celery worker, Celery beat
./scripts/dev.sh

# Minimal (Django + Vite only, no async tasks)
./scripts/dev-minimal.sh

# Selective
./scripts/dev.sh django vite celery
```

**URLs:** Django: http://localhost:8000 | Vite HMR: http://localhost:5173

See [Frontend Guide](docs/FRONTEND.md) for build system details.

### Production Deployment
```bash
# Build and deploy
./scripts/deploy.sh --migrate

# Restart services
sudo systemctl restart battycoda battycoda-celery battycoda-celery-beat
```

See [Operations Guide](docs/OPERATIONS.md) for full deployment workflow.

### Running Tests
```bash
# Python
python manage.py test
python manage.py test battycoda_app.tests.TestClassName.test_method_name

# JavaScript
npm test              # Unit tests (watch mode)
npm run e2e           # E2E tests

# Linting
./lint.sh             # Python
npm run lint          # JavaScript
```

See [Testing Guide](docs/TESTING.md) for full testing documentation.

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
- **ClusteringRun** - A clustering job (single segmentation or project-level)
- **ClusteringRunSegmentation** - Junction table for project-level runs
- **Cluster** - A cluster of similar segments
- **SegmentCluster** - Links segments to clusters with confidence scores
- **ClusterCallMapping** - Maps clusters to call types

### Tasks & Jobs
- **TaskBatch** - Group of annotation tasks created together
- **Task** - Individual annotation task for a segment
- **SpectrogramJob** - Tracks spectrogram generation jobs
- **UserNotification** - User notifications

## Domain Systems

### Classification System
Runs are processed via queue: created with status "queued", picked up by `process_classification_queue` task (every 30s), processed via R server.

Key files:
- `battycoda_app/audio/task_modules/classification/run_classification.py`
- `battycoda_app/audio/task_modules/queue_processor.py`

### Clustering System
Groups similar segments using unsupervised ML.

**Scope:** Single recording or project-level (all recordings, filtered by species)
**Algorithms:** Manual (kmeans, GMM, spectral, dbscan) or Automatic (HDBSCAN, Mean Shift, OPTICS)
**Features:** MFCC (default), Mel Spectrogram, Chroma

Key files:
- `battycoda_app/audio/task_modules/clustering/`
- `battycoda_app/views_clustering/`

### R Server
ML classification models (KNN, LDA) via plumber API on port 8001.

```bash
curl http://localhost:8001/ping  # Health check
```

Key files: `R_code/server.R`, `R_code/api_endpoints.R`

### Simple API
REST endpoints in `battycoda_app/simple_api/`:
- `recording_upload.py` - Recording upload (supports auto-split)
- `classification_views.py` - Classification endpoints
- `segmentation_views.py` - Segmentation endpoints
- `task_views.py` - Task management
- `data_views.py` - Data export

### Audio Auto-Split
Long audio files (>60s) automatically split into 1-minute chunks on upload.

## Code Style

- **Imports**: Group by standard library, Django, then project; alphabetize within groups
- **Formatting**: PEP 8, 4-space indentation, ~120 char line limit
- **Naming**: CamelCase for classes, snake_case for functions/variables
- **Error Handling**: Don't use bare `except: pass` - handle properly or remove try block
- **Frontend**: Prefer Django server-side rendering; Bootstrap 5
- **Comments**: Be sparse, especially when removing code

## Useful Paths

| Path | Description |
|------|-------------|
| `templates/` | HTML templates |
| `static/` | Static files (CSS, JS) |
| `media/` | Media uploads |
| `/var/log/battycoda/` | Celery logs, memory dumps |
| `systemd/` | Systemd service files |
| `R_code/` | R server code |
| `battycoda_app/management/commands/` | Management commands |
| `battycoda_app/simple_api/` | REST API |
| `scripts/` | Dev and deployment scripts |

## Database

```bash
source venv/bin/activate
python manage.py shell

# Example:
from battycoda_app.models.classification import ClassificationRun
run = ClassificationRun.objects.get(id=123)
run.status  # queued, pending, in_progress, completed, failed
```

## Common Issues

**Classification runs failing at ~88%**: Memory-related. Check `/var/log/battycoda/` for dumps, R server memory (`ps aux | grep R`).

**Celery OOM killed**:
```bash
sudo journalctl -u battycoda-celery | grep -i oom
```

**R server not responding**:
```bash
curl http://localhost:8001/ping
ps aux | grep "R.*server"
```

**Disk usage alerts**: `df -h / /home`

## Detailed Documentation

| Guide | Contents |
|-------|----------|
| [Frontend Development](docs/FRONTEND.md) | Bootstrap 5, Vite, TypeScript, theme system, JS modules |
| [Testing Guide](docs/TESTING.md) | Python tests, Vitest, Playwright, E2E, visual regression |
| [Operations Guide](docs/OPERATIONS.md) | Environment config, CSP, Celery, R server, deployment |
| [API Reference](docs/API.md) | REST API documentation |
