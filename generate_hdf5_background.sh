#!/bin/bash
# Generate missing HDF5 files in the background with CPU throttling
#
# This script runs the generate_missing_hdf5 management command with:
# - Low CPU priority (nice 19)
# - Low I/O priority (ionice best-effort class 3)
# - Adaptive sleep time (sleeps as long as processing took)
# - Output logged to a file
#
# Usage:
#   ./generate_hdf5_background.sh [--batch-size N] [--sleep-multiplier N] [--dry-run]

cd /home/ubuntu/battycoda

# Activate virtual environment
source venv/bin/activate

# Default options
BATCH_SIZE=""
DRY_RUN=""
SLEEP_MULTIPLIER="1.0"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="--batch-size $2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --sleep-multiplier)
            SLEEP_MULTIPLIER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--batch-size N] [--sleep-multiplier N] [--dry-run]"
            exit 1
            ;;
    esac
done

# Log file with timestamp (uses system log directory)
LOG_FILE="/var/log/battycoda/hdf5_generation_$(date +%Y%m%d_%H%M%S).log"

echo "Starting HDF5 generation in background..."
echo "Log file: $LOG_FILE"
echo "Options: batch-size=${BATCH_SIZE:-all}, sleep-multiplier=${SLEEP_MULTIPLIER}, dry-run=${DRY_RUN:-no}"

# Run with low CPU and I/O priority
# nice -n 19: Lowest CPU priority
# ionice -c 3: Idle I/O priority (only when system is idle)
# -u: Unbuffered output so logs appear immediately
nohup nice -n 19 ionice -c 3 python -u manage.py generate_missing_hdf5 \
    $BATCH_SIZE \
    $DRY_RUN \
    --sleep-multiplier $SLEEP_MULTIPLIER \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo "Process started with PID: $PID"
echo "To monitor progress: tail -f $LOG_FILE"
echo "To stop: kill $PID"
