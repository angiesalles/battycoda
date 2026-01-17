#!/bin/bash
# scripts/deploy.sh - Production deployment script for BattyCoda
#
# This script prepares the application for production by:
# 1. Installing npm dependencies (reproducible via npm ci)
# 2. Building Vite frontend assets
# 3. Collecting Django static files
# 4. Optionally running database migrations
#
# Usage:
#   ./scripts/deploy.sh              # Build assets and collect static
#   ./scripts/deploy.sh --migrate    # Also run database migrations
#   ./scripts/deploy.sh --help       # Show help
#
# This script is called by systemd ExecStartPre to ensure assets are
# built before the application starts.

set -e

# Change to project root directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "Usage: ./scripts/deploy.sh [OPTIONS]"
    echo ""
    echo "Prepare BattyCoda for production deployment."
    echo ""
    echo "Options:"
    echo "  --migrate     Run database migrations after building"
    echo "  --skip-npm    Skip npm ci (use existing node_modules)"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/deploy.sh              # Standard deployment"
    echo "  ./scripts/deploy.sh --migrate    # Deploy with migrations"
}

# Parse arguments
RUN_MIGRATE=false
SKIP_NPM=false

for arg in "$@"; do
    case $arg in
        --migrate)
            RUN_MIGRATE=true
            shift
            ;;
        --skip-npm)
            SKIP_NPM=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $arg"
            show_help
            exit 1
            ;;
    esac
done

log_info "Starting BattyCoda deployment..."
log_info "Project root: $PROJECT_ROOT"

# Check prerequisites
log_info "Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install Node.js 22.x or later."
    exit 1
fi

NODE_VERSION=$(node --version)
log_info "Node.js version: $NODE_VERSION"

# Check npm
if ! command -v npm &> /dev/null; then
    log_error "npm is not installed."
    exit 1
fi

# Check Python virtual environment
if [ ! -d "venv" ]; then
    log_error "Python virtual environment not found at ./venv"
    exit 1
fi

# Load environment variables from .env for Sentry source map upload
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# Set production mode for Vite build (enables hidden source maps)
export NODE_ENV=production

# Set Sentry release to git commit hash for release tracking
if git rev-parse --git-dir > /dev/null 2>&1; then
    export SENTRY_RELEASE=$(git rev-parse HEAD)
    log_info "Sentry release: ${SENTRY_RELEASE:0:8}..."

    # Persist SENTRY_RELEASE to .env for runtime use by Django/Celery
    if grep -q "^SENTRY_RELEASE=" .env 2>/dev/null; then
        sed -i "s|^SENTRY_RELEASE=.*|SENTRY_RELEASE=$SENTRY_RELEASE|" .env
    else
        echo "SENTRY_RELEASE=$SENTRY_RELEASE" >> .env
    fi
fi

# Check if Sentry source map upload is configured
if [ -n "$SENTRY_AUTH_TOKEN" ] && [ -n "$SENTRY_ORG" ] && [ -n "$SENTRY_PROJECT" ]; then
    log_info "Sentry source map upload enabled (org: $SENTRY_ORG, project: $SENTRY_PROJECT)"
else
    log_warn "Sentry source map upload not configured (missing SENTRY_AUTH_TOKEN, SENTRY_ORG, or SENTRY_PROJECT)"
    log_warn "Source maps will be generated but not uploaded to Sentry"
fi

# Step 1: Install npm dependencies
if [ "$SKIP_NPM" = false ]; then
    log_info "Installing npm dependencies (npm ci)..."
    npm ci
else
    log_info "Skipping npm install (--skip-npm specified)"
fi

# Step 2: Build Vite assets
log_info "Building Vite frontend assets..."
npm run build

# Verify build output exists
if [ ! -d "static/dist" ]; then
    log_error "Vite build failed - static/dist directory not created"
    exit 1
fi

if [ ! -f "static/dist/.vite/manifest.json" ]; then
    log_error "Vite build failed - manifest.json not found"
    exit 1
fi

log_info "Vite build complete. Output in static/dist/"

# Step 3: Collect static files
log_info "Collecting Django static files..."
source venv/bin/activate
python manage.py collectstatic --noinput

# Step 4: Run migrations (optional)
if [ "$RUN_MIGRATE" = true ]; then
    log_info "Running database migrations..."
    python manage.py migrate
fi

log_info "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "  - Restart services: sudo systemctl restart battycoda battycoda-celery"
echo "  - Check status: sudo systemctl status battycoda"
