# BattyCoda Development Guidelines

## Important: Documentation Maintenance
**ALWAYS suggest updating this CLAUDE.md file when implementing significant new features, major changes, or new capabilities.**

## Task Tracking with Beads

This repository uses [Beads](https://github.com/steveyegge/beads) for task tracking. Beads is a persistent memory system for AI coding agents. Run `bd onboard` to get started.

### Common Commands
```bash
bd ready              # Show tasks without blocking dependencies (find available work)
bd list               # List all open issues
bd show <id>          # View issue details
bd create "Title" -p 1 -t task   # Create a task with priority 1
bd create "Title" -t epic --parent <id>  # Create sub-task under epic
bd update <id> --status in_progress      # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
bd dep tree <id>      # View dependency tree
```

### Workflow
1. Before starting work: `bd ready` to see available tasks
2. Pick a task: `bd update <id> --status in_progress`
3. When done: `bd close <id> --reason "Description of what was done"`
4. Create new tasks as you discover them

### Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

### Current Epics
- `battycoda-yf0`: Clustering Visualization Overhaul (see CLUSTERING_VISUALIZATION_OVERHAUL.md)

### Project Terminology

**puntomatic** - When the user says "puntomatic", it means:
1. Yes, it's OK to suppress/defer the warning or issue for now
2. BUT you MUST add a reminder to the relevant bead (the "proper-fix-it" task) to remove the suppression when the real fix is implemented
3. When you hear "puntomatic", read back this definition to acknowledge you remember it

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

## Node.js Environment

This project requires Node.js 22.x or later for Vite and frontend tooling.

**Using nvm (recommended):**
```bash
# Install nvm if not already installed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install and use correct Node version (reads from .nvmrc)
nvm install
nvm use
```

**Using system package manager:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Verify installation:**
```bash
node --version  # Should be v22.x.x
npm --version   # Should be v10.x.x
```

**Note:** The `.npmrc` file enforces strict engine checking. `npm install` will fail if your Node version doesn't match the requirements in `package.json`.

## Development Workflow

For development, you need to run multiple services: Django, Vite (for frontend assets), Celery worker, and Celery beat. Use the convenience scripts to manage these easily.

### Quick Start (Recommended)
```bash
# Start all services with honcho (Django, Vite, Celery worker, Celery beat)
./scripts/dev.sh
```

### Minimal Mode (Frontend Work)
```bash
# Start only Django + Vite (no Celery - async tasks won't process)
./scripts/dev-minimal.sh
```

### Selective Services
```bash
# Start specific services only using honcho
./scripts/dev.sh django vite           # Just Django and Vite
./scripts/dev.sh django vite celery    # Django, Vite, and Celery worker
```

### Manual Individual Services
```bash
# Terminal 1: Django
source venv/bin/activate && python manage.py runserver

# Terminal 2: Vite (for frontend HMR)
npm run dev

# Terminal 3: Celery worker (for async tasks)
source venv/bin/activate && celery -A config worker --loglevel=info

# Terminal 4: Celery beat (for scheduled tasks)
source venv/bin/activate && celery -A config beat --loglevel=info
```

### Development URLs
- **Django**: http://localhost:8000
- **Vite HMR**: http://localhost:5173 (proxied through Django in dev mode)

## Production Deployment

### Deployment Script
Use the deployment script to prepare the application for production:

```bash
# Standard deployment (build assets + collect static)
./scripts/deploy.sh

# With database migrations
./scripts/deploy.sh --migrate

# Skip npm install (if node_modules already up to date)
./scripts/deploy.sh --skip-npm
```

The deploy script performs:
1. `npm ci` - Install npm dependencies (reproducible builds)
2. `npm run build` - Build Vite frontend assets to `static/dist/`
3. `python manage.py collectstatic` - Collect all static files
4. Optionally run database migrations

### Deployment Workflow

After pulling code changes:

```bash
# 1. Pull latest code
git pull

# 2. Install Python dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# 3. Build and deploy assets
./scripts/deploy.sh --migrate

# 4. Restart services
sudo systemctl restart battycoda battycoda-celery battycoda-celery-beat

# 5. Verify services are running
sudo systemctl status battycoda
```

### Systemd Integration

The battycoda.service runs `collectstatic --noinput` on startup via ExecStartPre. However, you must run `./scripts/deploy.sh` manually after code changes to rebuild Vite assets.

After modifying systemd service files:
```bash
sudo ./systemd/install_services.sh
sudo systemctl restart battycoda
```

## Running Tests
```bash
source venv/bin/activate
python manage.py test
python manage.py test battycoda_app.tests.TestClassName.test_method_name

# Run specific test modules
python manage.py test battycoda_app.tests.test_clustering  # Project-level clustering tests
python manage.py test battycoda_app.tests.test_models      # Model tests
python manage.py test battycoda_app.tests.test_views_auth  # Auth view tests
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
- **ClusteringRun** - A clustering job (single segmentation or project-level)
- **ClusteringRunSegmentation** - Junction table for project-level runs (tracks included recordings)
- **Cluster** - A cluster of similar segments
- **SegmentCluster** - Links segments to clusters with confidence scores
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

Clustering groups similar segments together using unsupervised ML algorithms.

### Scope Options
- **Single Recording** - Cluster segments from one segmentation
- **Project-Level** - Cluster all segments across all recordings in a project
  - Requires species selection (clustering different species together is meaningless)
  - Uses PCA instead of t-SNE for visualization when >2000 segments (memory optimization)
  - Batched database writes for large datasets
  - 1-hour task timeout with progress tracking

### Supported Algorithms
- **Manual** (specify cluster count): kmeans, gaussian_mixture, spectral, dbscan
- **Automatic** (auto-determine clusters): HDBSCAN, Mean Shift, OPTICS, Affinity Propagation, DBSCAN Enhanced

### Feature Extraction
- Audio normalized to 22050 Hz sample rate for consistency
- Methods: MFCC (default), Mel Spectrogram, Chroma Features

### Key Models
- `ClusteringRun` - A clustering job (scope: segmentation or project)
- `ClusteringRunSegmentation` - Junction table tracking included recordings for project-level runs
- `Cluster` - A discovered cluster with size, coherence score, optional label
- `SegmentCluster` - Links segments to clusters with confidence scores
- `ClusterCallMapping` - Maps clusters to known call types

### API Endpoints
- `GET /clustering/project-segments/<project_id>/` - Get segment counts by species for a project
- `GET /clustering/get-cluster-members/?cluster_id=<id>` - Get segment members of a cluster (with recording info for project-level)
- `GET /clustering/get-cluster-data/?cluster_id=<id>` - Get cluster details
- `POST /clustering/update-cluster-label/` - Update cluster label
- `GET /clustering/export/<run_id>/` - Export clusters as CSV (includes recording columns for project-level)

Key files:
- `battycoda_app/audio/task_modules/clustering/` - Main clustering module
- `battycoda_app/views_clustering/` - Views for dashboard, explorer, mappings
- `templates/clustering/` - UI templates

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
- `dev.sh` - Start full development environment (Django, Vite, Celery, Beat)
- `dev-minimal.sh` - Start minimal dev environment (Django + Vite only)
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

### Vite Frontend Build (Feature Flags)
- `VITE_ENABLED` - Master switch for Vite bundles (default: false)
- `VITE_FEATURE_THEME_SWITCHER` - Use Vite for theme switcher (default: false)
- `VITE_FEATURE_NOTIFICATIONS` - Use Vite for notifications (default: false)
- `VITE_FEATURE_DATETIME_FORMATTER` - Use Vite for datetime formatter (default: false)
- `VITE_FEATURE_FILE_UPLOAD` - Use Vite for file upload (default: false)
- `VITE_FEATURE_CLUSTER_EXPLORER` - Use Vite for cluster explorer (default: false)
- `VITE_FEATURE_CLUSTER_MAPPING` - Use Vite for cluster mapping (default: false)
- `VITE_FEATURE_PLAYER` - Use Vite for audio player (default: false)
- `VITE_FEATURE_TASK_ANNOTATION` - Use Vite for task annotation (default: false)
- `VITE_FEATURE_SEGMENTATION` - Use Vite for segmentation (default: false)

## Vite Frontend Migration

BattyCoda uses an incremental migration strategy for moving from Django static files to Vite-bundled JavaScript.

### Feature Flag System

Each JavaScript feature can be migrated independently using feature flags in `settings.py`:

```python
VITE_ENABLED = True  # Master switch
VITE_FEATURES = {
    'theme_switcher': True,   # Migrated
    'notifications': False,   # Not yet
    # ...
}
```

Templates check these flags to load either legacy scripts or Vite bundles:
```html
{% if not VITE_FEATURES.theme_switcher %}
<script src="{% static 'js/theme-switcher.js' %}"></script>
{% endif %}
```

### CSS Bundling

CSS is processed through Vite with PostCSS for autoprefixing and minification:

**Entry Points:**
- `static/css/main.css` - Main CSS bundle (imports app.css, themes.css, typography.css, stroke-7)
- `static/css/themes/*.css` - Individual theme files (built separately for dynamic loading)

**Key Files:**
- `postcss.config.js` - PostCSS configuration (autoprefixer, cssnano)
- `vite.config.js` - Vite config with CSS entry points
- `battycoda_app/templatetags/vite.py` - Custom template tags for CSS loading

**Template Tags:**
```html
{% load vite %}
{% vite_css 'styles' %}           <!-- Load main CSS bundle -->
{% vite_theme_css 'blue-sky' %}   <!-- Load specific theme CSS -->
{% vite_theme_urls %}             <!-- Inject theme URL mapping for JS -->
```

The `vite_theme_urls` tag generates a JavaScript object (`window.__VITE_THEME_URLS__`) that maps theme names to their correct URLs (with hashes in production). This allows the theme-switcher.js to dynamically load themes without knowing the hashed filenames.

### Migration Order (Suggested)

| Order | Feature | Risk | Complexity |
|-------|---------|------|------------|
| 1 | theme_switcher | Low | Low |
| 2 | notifications | Low | Low |
| 3 | datetime_formatter | Low | Low |
| 4 | file_upload | Medium | Medium |
| 5 | cluster_explorer | Medium | High |
| 6 | cluster_mapping | Medium | High |
| 7 | player | High | High |
| 8 | task_annotation | High | High |
| 9 | segmentation | Medium | Medium |

### Rollback Procedures

#### Level 1: Disable Single Feature
Set the specific feature flag to false in `.env`:
```bash
VITE_FEATURE_THEME_SWITCHER=false
```
Then restart the service:
```bash
sudo systemctl restart battycoda
```

#### Level 2: Disable All Vite
Disable the master switch in `.env`:
```bash
VITE_ENABLED=false
```
Then restart:
```bash
sudo systemctl restart battycoda
```

#### Level 3: Full Revert
Revert to pre-Vite commit:
```bash
git log --oneline  # Find the commit before Vite changes
git revert HEAD~n..HEAD  # Or specific commits
sudo systemctl restart battycoda
```

### Testing Checklist Per Feature

Before enabling a feature in production:
- [ ] Unit tests pass
- [ ] E2E tests pass for this feature
- [ ] Manual testing on staging
- [ ] Performance comparison (bundle size, load time)
- [ ] No console errors
- [ ] All browsers tested

### Key Files
- `config/settings.py` - VITE_ENABLED, VITE_FEATURES settings
- `battycoda_app/context_processors.py` - vite_features context processor
- `templates/base.html` - Conditional script loading

## Code Style Guidelines

- **Imports**: Group by standard library, Django, then project modules; alphabetize within groups
- **Formatting**: PEP 8, 4-space indentation, ~120 char line limit
- **Naming**: CamelCase for classes, snake_case for functions/variables
- **Error Handling**: Don't use bare `except: pass` - remove the try block or handle properly
- **Frontend**: Prefer Django server-side rendering; Bootstrap 5
- **Comments**: Be sparse, especially when removing code

## JavaScript Build System (Vite)

BattyCoda uses Vite for JavaScript bundling and development.

### Directory Structure
```
static/
├── js/
│   ├── main.js              # Main entry point
│   ├── utils/               # Shared utilities
│   │   ├── page-data.js     # Django template data access
│   │   └── colormaps.js     # Color utilities
│   ├── player/              # Waveform player module
│   ├── cluster_explorer/    # Clustering visualization
│   ├── cluster_mapping/     # Cluster-to-call mapping
│   ├── file_upload/         # File upload handling
│   ├── segmentation/        # Segmentation module
│   └── test/                # Test setup, fixtures, mocks
├── css/
│   ├── main.css             # CSS entry point
│   └── themes/              # Theme CSS files
└── dist/                    # Built output (gitignored)
```

### Build Commands
```bash
# Start Vite dev server (port 5173)
npm run dev

# Build for production
npm run build

# Build with watch mode
npm run build:watch

# Preview production build
npm run preview
```

### Adding New JavaScript Modules

1. Create module in appropriate directory:
   ```javascript
   // static/js/feature/mymodule.js
   export function myFunction() { ... }
   ```

2. Add entry point in `vite.config.js` if needed:
   ```javascript
   rollupOptions: {
     input: {
       myFeature: resolve(__dirname, 'static/js/feature/index.js'),
     }
   }
   ```

3. Load in Django template:
   ```html
   {% load vite %}
   {% vite_asset 'myFeature.js' %}
   ```

### Accessing Django Data in JavaScript

Use data attributes pattern (not inline scripts):

```html
<!-- In template -->
<div id="app-data"
     data-recording-id="{{ recording.id }}"
     data-api-url="{% url 'api:endpoint' %}"
     style="display: none;">
</div>
```

```javascript
// In JavaScript
import { getPageData } from './utils/page-data.js';
const { recordingId, apiUrl } = getPageData();
```

### External Dependencies (CDN vs Bundled)

BattyCoda uses a hybrid approach for JavaScript dependencies:

**CDN (External)** - Loaded via CDN in Django templates, marked as external in Vite config:
| Library | Version | Reason |
|---------|---------|--------|
| jQuery | 3.3.1 | Deep integration, plugin ecosystem |
| Bootstrap JS | 5.3.3 | Tied to jQuery, used for modals/dropdowns |
| Toastr | latest | Simple toast notifications |
| Select2 | 4.1.0 | jQuery-based select dropdowns |
| Perfect Scrollbar | 1.5.0 | Minimal usage in Maisonnette theme |

**Bundled (npm)** - Installed via npm, bundled by Vite with tree-shaking:
| Library | Reason |
|---------|--------|
| D3.js | Heavy usage in cluster visualization, tree-shaking removes unused modules |

The Vite config marks jQuery as external so modules can reference `window.jQuery` without bundling it. D3 is imported as ES6 modules (e.g., `import { scaleLinear } from 'd3'`).

## JavaScript Testing

### Unit Tests (Vitest)

Unit tests use Vitest with jsdom for DOM testing.

```bash
# Run tests in watch mode
npm test

# Run tests once
npm run test:run

# Run with coverage
npm run test:coverage

# Open Vitest UI
npm run test:ui
```

**Test file location:** Place `.test.js` files next to the module they test:
```
static/js/
├── utils/
│   ├── page-data.js
│   └── page-data.test.js    # Tests for page-data.js
├── player/
│   ├── data_manager.js
│   └── data_manager.test.js
```

**Test setup files:** `static/js/test/` contains:
- `setup.js` - Global test configuration
- `fixtures/` - Test data fixtures
- `mocks/` - Mock implementations

**Writing tests:**
```javascript
import { describe, it, expect, vi } from 'vitest';
import { myFunction } from './mymodule.js';

describe('myFunction', () => {
  it('should return expected value', () => {
    expect(myFunction(input)).toBe(expected);
  });
});
```

### E2E Tests (Playwright)

End-to-end tests for full user workflows.

```bash
# Run E2E tests
npm run e2e

# Run with browser visible
npm run e2e:headed

# Open Playwright UI
npm run e2e:ui

# View test report
npm run e2e:report

# Run specific browser
npm run e2e:chromium
```

**Test file location:** `tests/e2e/`
```
tests/e2e/
├── playwright.config.js     # Note: config is at project root
├── global-setup.js          # Database setup before tests
├── global-teardown.js       # Cleanup after tests
├── fixtures/                # Test data and state
├── helpers/                 # Shared test utilities
│   └── auth.js              # Login helpers
└── specs/                   # Test files
    └── smoke.spec.js        # Basic smoke tests
```

**Writing E2E tests:**
```javascript
import { test, expect } from '@playwright/test';
import { login } from '../helpers/auth.js';

test('user can view dashboard', async ({ page }) => {
  await login(page, 'test@example.com', 'password');
  await page.goto('/dashboard/');
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

**Configuration:** Playwright config is at `playwright.config.js` in project root. Tests run against `http://localhost:8000` by default.

### Test Database Setup

E2E tests use a separate test database (`battycoda_test`) to avoid polluting development data.

**Initial Setup (one-time):**
```bash
# Create the test database
sudo -u postgres psql -c "CREATE DATABASE battycoda_test OWNER battycoda;"
```

**Database Management Scripts:**
```bash
# Set up test database with initial data (run before first test)
npm run e2e:setup-db

# Reset test database (clears all data and re-initializes)
npm run e2e:reset-db
```

**Environment Variable:**
- `DJANGO_TEST_MODE=true` - Set automatically by E2E test scripts. Tells Django to use the test database instead of the main database.

## JavaScript Linting

```bash
# Lint JavaScript
npm run lint

# Auto-fix lint issues
npm run lint:fix

# Format with Prettier
npm run format

# Check formatting
npm run format:check
```

ESLint config is in `eslint.config.js` (flat config format).

## Python Linting

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
- Dev scripts: `scripts/dev.sh`, `scripts/dev-minimal.sh`
- Procfile (dev): `Procfile.dev`

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
