#!/bin/bash
#
# Install BattyCoda systemd service files
#
# This script copies service files from the repo to /etc/systemd/system/
# and reloads the systemd daemon.
#
# Usage: sudo ./systemd/install_services.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo ./systemd/install_services.sh"
    exit 1
fi

echo "Installing BattyCoda systemd services..."

# List of service files to install
SERVICES=(
    "battycoda.service"
    "battycoda-celery.service"
    "battycoda-celery-beat.service"
    "battycoda-failure-notify@.service"
)

for service in "${SERVICES[@]}"; do
    src="$SCRIPT_DIR/$service"
    dest="/etc/systemd/system/$service"

    if [ -f "$src" ]; then
        cp "$src" "$dest"
        chmod 644 "$dest"
        echo "  Installed: $service"
    else
        echo "  Warning: $src not found, skipping"
    fi
done

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Done! Services installed:"
ls -la /etc/systemd/system/battycoda*.service

echo ""
echo "To restart services, run:"
echo "  sudo systemctl restart battycoda battycoda-celery battycoda-celery-beat"
