# BattyCoda Operations Guide

This guide covers production operations, environment configuration, and system administration.

## Service Management

All services run via systemd (NOT Docker). Service files are in `systemd/` folder.

### Quick Reference
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

# After modifying service files:
sudo ./systemd/install_services.sh
```

## Environment Configuration

Configuration in `.env` file:

### Required
| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |

### Application
| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN_NAME` | Domain name (e.g., battycoda.com) | |
| `DEBUG` | Enable debug mode | `False` |
| `DISABLE_STATIC_CACHING` | Disable whitenoise caching for dev | |
| `MAX_UPLOAD_SIZE_MB` | Max upload size in MB | `100` |

### Database & Redis
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `CELERY_BROKER_URL` | Redis URL for Celery broker |
| `CELERY_RESULT_BACKEND` | Redis URL for Celery results |

### AWS SES (Email)
| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_SES_REGION_NAME` | AWS region | `us-east-1` |
| `AWS_SES_ACCESS_KEY_ID` | AWS access key | |
| `AWS_SES_SECRET_ACCESS_KEY` | AWS secret key | |
| `AWS_SES_CONFIGURATION_SET` | SES configuration set | (optional) |
| `DEFAULT_FROM_EMAIL` | From address for emails | |

### Backups
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_BACKUP_BUCKET` | S3 bucket for backups | `backup-battycoda` |
| `DATABASE_BACKUP_PREFIX` | S3 prefix for backups | `database-backups/` |

### Security
| Variable | Description | Default |
|----------|-------------|---------|
| `CSP_ENFORCE` | Enable CSP enforcement | `false` |
| `CSP_STRICT_MODE` | Remove 'unsafe-inline' from script-src | `false` |

### Sentry Error Tracking
| Variable | Description | Default |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry Data Source Name | |
| `SENTRY_ENVIRONMENT` | Environment name | `production` |
| `SENTRY_AUTH_TOKEN` | Auth token for source map uploads | |
| `SENTRY_ORG` | Sentry organization slug | |
| `SENTRY_PROJECT` | Sentry project name | |

When Sentry source map variables are set, `./scripts/deploy.sh` automatically uploads source maps.

### Vite Feature Flags
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_ENABLED` | Master switch for Vite bundles | `false` |
| `VITE_FEATURE_*` | Individual feature flags | `false` |

## Celery Tasks & Beat Schedule

### Scheduled Tasks
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

## R Server

The R server runs classification models (KNN, LDA) via plumber API.

### Configuration
- Runs on port 8001
- Single-threaded (processes one request at a time)
- Uses warbleR for acoustic feature extraction
- Models stored in `media/models/classifiers/`

### Health Check
```bash
curl http://localhost:8001/ping
```

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict/knn` | POST | KNN classification |
| `/predict/lda` | POST | LDA classification |
| `/train/knn` | POST | Train KNN model |
| `/train/lda` | POST | Train LDA model |

### Key Files
- `R_code/server.R` - Main server
- `R_code/api_endpoints.R` - API endpoint definitions
- `R_code/model_functions/` - Model runner, trainer, and utilities

## Content Security Policy (CSP)

BattyCoda uses CSP headers as defense-in-depth against XSS attacks.

### Configuration
CSP is implemented via `django-csp` middleware in `config/settings.py`.

**Modes:**
- **Report-Only (default)**: Violations logged but not blocked
- **Enforcement**: Violations blocked (`CSP_ENFORCE=true`)
- **Strict Mode**: Removes `'unsafe-inline'` from script-src (`CSP_STRICT_MODE=true`)

**Current Policy:**
- Scripts: `'self'`, CDNs (jsdelivr, cloudflare, jquery, sentry), + `'unsafe-inline'` in non-strict mode
- Styles: `'self'`, `'unsafe-inline'`, CDNs
- Images: `'self'`, `data:`
- Fonts: `'self'`, CDNs
- Connections: `'self'`, Sentry endpoints

**Development Mode:**
When `DEBUG=true` and `VITE_DEV_MODE=true`, the Vite dev server (localhost:5173) is automatically allowed.

### Script Migration Status
Migrated to external files:
- `static/js/utils/security.js` - `escapeHtml()`, `validateUrl()`
- `static/js/integrations/sentry-init.js` - Sentry initialization
- `static/js/core/app-init.js` - Django messages, management features
- `static/js/utils/bootstrap-init.js` - Auto-initializes tooltips and popovers

Remaining inline scripts:
- Page-specific scripts (can use nonces in strict mode)

### Enabling Strict Mode
Before enabling:
1. Test in report-only mode (`CSP_ENFORCE=false`)
2. Check browser console for CSP violations
3. Fix violations (move to external files or add nonces)

```bash
# In .env:
CSP_STRICT_MODE=true
CSP_ENFORCE=false  # Start in report-only mode

# After testing:
CSP_ENFORCE=true
```

### Checking CSP Headers
```bash
curl -sI http://localhost:8000/ | grep -i "content-security-policy"
```

### Key Files
- `config/settings.py` - CSP configuration
- `battycoda_app/templatetags/vite.py` - Vite template tags with nonce support
- `static/js/utils/security.js` - Security utility functions
- `static/css/utilities.css` - CSS utility classes

## Memory Monitoring

Celery workers have a memory monitor that dumps profiling info when memory exceeds threshold.

### Thresholds
- 1.5GB: Warning
- 2GB: Critical

### Output Location
`/var/log/battycoda/memory_dump_*.txt`

### Dump Contents
- tracemalloc allocations
- Object counts
- Process info

### Key File
`battycoda_app/celery_memory_monitor.py`

## Email Notifications

Uses AWS SES for email.

### Key Notifications
- Worker failure alerts (via systemd OnFailure directive)
- Disk usage warnings (when usage exceeds 90%)

### Key File
`battycoda_app/utils/email_utils.py`

## Management Commands

```bash
source venv/bin/activate

# Database backup
python manage.py backup_database

# Generate missing HDF5 spectrogram files
python manage.py generate_missing_hdf5
python manage.py generate_missing_hdf5 --dry-run  # Preview only

# Background generation with CPU throttling:
./scripts/generate_hdf5_background.sh
./scripts/generate_hdf5_background.sh --batch-size 10
./scripts/generate_hdf5_background.sh --dry-run
# Logs to: /var/log/battycoda/hdf5_generation_TIMESTAMP.log

# Import species from CSV
python manage.py import_species

# Initialize default data
python manage.py initialize_defaults

# Populate group memberships
python manage.py populate_memberships
```

## Scripts

Located in `scripts/`:
| Script | Description |
|--------|-------------|
| `dev.sh` | Start full development environment |
| `dev-minimal.sh` | Start minimal dev environment (Django + Vite only) |
| `deploy.sh` | Production deployment (build assets, collect static) |
| `notify_worker_failure.py` | Sends email alerts when workers fail |
| `create_clustering_algorithms.py` | Creates default clustering algorithms |
| `generate_hdf5_background.sh` | Background HDF5 generation |
| `sentry_fetch.py` | Fetch Sentry issue details and stack traces |

Root directory:
| Script | Description |
|--------|-------------|
| `setup_nginx.sh` | Generate and install nginx config (uses `.env` for domain/settings) |

## Nginx Configuration

Nginx runs on the host (not in Docker) and proxies to Django on port 8000.

### Regenerating Config
```bash
sudo ./setup_nginx.sh
```

This script:
- Reads `DOMAIN_NAME` and `MAX_UPLOAD_SIZE_MB` from `.env`
- Generates `/etc/nginx/sites-available/battycoda.conf`
- Sets up HTTPS if SSL certificates exist (`/etc/letsencrypt/live/$DOMAIN_NAME/`)
- Tests and reloads nginx

### Key Settings
- Django backend: `127.0.0.1:8000`
- Static files: `/home/ubuntu/battycoda/staticfiles/`
- Media files: `/home/ubuntu/battycoda/media/`

## Production Deployment

### Deployment Script
```bash
./scripts/deploy.sh             # Standard (build assets + collect static)
./scripts/deploy.sh --migrate   # With database migrations
./scripts/deploy.sh --skip-npm  # Skip npm install
```

The script performs:
1. `npm ci` - Install npm dependencies
2. `npm run build` - Build Vite frontend assets
3. `python manage.py collectstatic` - Collect static files
4. Optionally run database migrations

### Deployment Workflow
```bash
# 1. Pull latest code
git pull

# 2. Install Python dependencies (if changed)
source venv/bin/activate
pip install -r requirements.txt

# 3. Build and deploy assets
./scripts/deploy.sh --migrate

# 4. Restart services
sudo systemctl restart battycoda battycoda-celery battycoda-celery-beat

# 5. Verify
sudo systemctl status battycoda
```

## Common Issues

**Classification runs failing at ~88%**: Usually memory-related.
1. Check memory dumps in `/var/log/battycoda/`
2. Check for multiple large runs processing concurrently
3. Check R server memory: `ps aux | grep R`

**Celery OOM killed**:
```bash
sudo journalctl -u battycoda-celery | grep -i oom
```

**R server not responding**:
```bash
curl http://localhost:8001/ping
ps aux | grep "R.*server"
```

**Disk usage alerts**:
```bash
df -h / /home
```
