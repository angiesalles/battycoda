#!/bin/bash
# scripts/dev-minimal.sh - Start minimal development environment (Django + Vite only)
#
# Use this when you don't need Celery for async tasks or scheduled jobs.
# Useful for frontend development, template work, or testing basic views.
#
# Usage: ./scripts/dev-minimal.sh

set -e

# Change to project root directory
cd "$(dirname "$0")/.."

# Trap to kill both processes on Ctrl+C
trap 'kill 0' EXIT

# Check prerequisites
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required. See CLAUDE.md for installation."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Run: python -m venv venv"
    exit 1
fi

# Install JS dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo ""
echo "=========================================="
echo "BattyCoda Minimal Dev Environment"
echo "=========================================="
echo ""
echo "  Django:  http://localhost:8000"
echo "  Vite:    http://localhost:5173"
echo ""
echo "Note: Celery not running - async tasks will queue but not process"
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Start Vite in background
npm run dev &

# Start Django in foreground
source venv/bin/activate && python manage.py runserver
