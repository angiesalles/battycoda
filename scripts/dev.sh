#!/bin/bash
# scripts/dev.sh - Start full development environment for BattyCoda
#
# Starts Django, Vite, Celery worker, and Celery beat using honcho.
# All processes run together with combined colored output.
#
# Usage:
#   ./scripts/dev.sh                    # Start all services
#   ./scripts/dev.sh django vite        # Start specific services only

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    echo "Run: nvm install (using .nvmrc) or see CLAUDE.md for installation"
    exit 1
fi

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Error: Python virtual environment not found."
    echo "Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check honcho is installed
if ! source venv/bin/activate && command -v honcho &> /dev/null; then
    echo "Error: honcho not installed."
    echo "Run: source venv/bin/activate && pip install honcho"
    exit 1
fi

# Install JS dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Display startup info
echo ""
echo "=========================================="
echo "BattyCoda Development Environment"
echo "=========================================="
echo ""
echo "Services:"
echo "  Django:  http://localhost:8000"
echo "  Vite:    http://localhost:5173"
echo "  Celery:  Worker processing tasks"
echo "  Beat:    Scheduled task runner"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""
echo "=========================================="
echo ""

# Activate venv and start honcho
source venv/bin/activate

# If specific processes specified, run those only
if [ $# -gt 0 ]; then
    honcho start "$@" -f Procfile.dev
else
    honcho start -f Procfile.dev
fi
