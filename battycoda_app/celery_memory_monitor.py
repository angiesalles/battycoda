"""
Memory monitor for Celery workers.

Periodically checks memory usage and dumps profiling info when memory exceeds threshold.
This helps diagnose OOM issues by capturing state before the kernel kills the process.
"""
import gc
import logging
import os
import threading
import time
import tracemalloc
from datetime import datetime

import psutil

logger = logging.getLogger(__name__)

# Configuration
MEMORY_CHECK_INTERVAL = 10  # seconds
MEMORY_THRESHOLD_MB = 1500  # Dump when worker exceeds this
MEMORY_CRITICAL_MB = 2000  # More detailed dump at this level
LOG_DIR = "/var/log/battycoda"


class MemoryMonitor:
    def __init__(self):
        self.running = False
        self.thread = None
        self.tracemalloc_started = False
        self.last_dump_time = 0
        self.dump_cooldown = 60  # Don't dump more than once per minute

    def start(self):
        if self.running:
            return

        self.running = True

        # Start tracemalloc for detailed memory tracking
        if not tracemalloc.is_tracing():
            tracemalloc.start(25)  # Keep 25 frames of traceback
            self.tracemalloc_started = True

        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Memory monitor started (threshold: %dMB)", MEMORY_THRESHOLD_MB)

    def stop(self):
        self.running = False
        if self.tracemalloc_started:
            tracemalloc.stop()

    def _get_memory_mb(self):
        """Get current process memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def _monitor_loop(self):
        while self.running:
            try:
                memory_mb = self._get_memory_mb()

                if memory_mb > MEMORY_CRITICAL_MB:
                    self._dump_memory_info(memory_mb, critical=True)
                elif memory_mb > MEMORY_THRESHOLD_MB:
                    self._dump_memory_info(memory_mb, critical=False)

            except Exception as e:
                logger.error("Memory monitor error: %s", e)

            time.sleep(MEMORY_CHECK_INTERVAL)

    def _dump_memory_info(self, memory_mb, critical=False):
        """Dump memory profiling information to log file."""
        now = time.time()
        if now - self.last_dump_time < self.dump_cooldown:
            return
        self.last_dump_time = now

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        level = "CRITICAL" if critical else "WARNING"

        # Ensure log directory exists
        os.makedirs(LOG_DIR, exist_ok=True)
        dump_file = os.path.join(LOG_DIR, f"memory_dump_{timestamp}.txt")

        try:
            with open(dump_file, "w") as f:
                f.write(f"Memory Dump - {level}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"Memory Usage: {memory_mb:.1f} MB\n")
                f.write("=" * 60 + "\n\n")

                # Tracemalloc top allocations
                if tracemalloc.is_tracing():
                    f.write("TOP MEMORY ALLOCATIONS (tracemalloc):\n")
                    f.write("-" * 60 + "\n")
                    snapshot = tracemalloc.take_snapshot()
                    top_stats = snapshot.statistics('lineno')

                    for stat in top_stats[:30]:
                        f.write(f"{stat}\n")

                    f.write("\n\nTOP ALLOCATIONS BY FILE:\n")
                    f.write("-" * 60 + "\n")
                    top_files = snapshot.statistics('filename')
                    for stat in top_files[:20]:
                        f.write(f"{stat}\n")

                # Garbage collector stats
                f.write("\n\nGARBAGE COLLECTOR INFO:\n")
                f.write("-" * 60 + "\n")
                f.write(f"GC counts: {gc.get_count()}\n")
                f.write(f"GC thresholds: {gc.get_threshold()}\n")

                # Count objects by type
                f.write("\n\nOBJECT COUNTS BY TYPE:\n")
                f.write("-" * 60 + "\n")
                type_counts = {}
                for obj in gc.get_objects():
                    obj_type = type(obj).__name__
                    type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

                sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
                for obj_type, count in sorted_types[:30]:
                    f.write(f"  {obj_type}: {count}\n")

                # Current process info
                f.write("\n\nPROCESS INFO:\n")
                f.write("-" * 60 + "\n")
                process = psutil.Process(os.getpid())
                f.write(f"RSS: {process.memory_info().rss / 1024 / 1024:.1f} MB\n")
                f.write(f"VMS: {process.memory_info().vms / 1024 / 1024:.1f} MB\n")
                f.write(f"Threads: {process.num_threads()}\n")
                f.write(f"Open files: {len(process.open_files())}\n")

            logger.warning(
                "Memory %s: %.1f MB - dump written to %s",
                level, memory_mb, dump_file
            )

            # Also print to stdout so it appears in Celery logs
            print(f"[MEMORY {level}] {memory_mb:.1f} MB - dump: {dump_file}")

        except Exception as e:
            logger.error("Failed to write memory dump: %s", e)


# Global monitor instance
_monitor = None


def start_memory_monitor():
    """Start the memory monitor. Call this from Celery worker_ready signal."""
    global _monitor
    if _monitor is None:
        _monitor = MemoryMonitor()
    _monitor.start()


def stop_memory_monitor():
    """Stop the memory monitor."""
    global _monitor
    if _monitor is not None:
        _monitor.stop()
