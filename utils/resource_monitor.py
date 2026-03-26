"""
utils/resource_monitor.py
Background thread monitoring CPU and RAM usage of the PDFOS process.
"""
import threading
import psutil
import os
import gc
from utils.logger import log_resource_usage, log_memory_cleanup, get_logger

logger = get_logger("resource_monitor")


class ResourceMonitor:
    """Monitors CPU/RAM usage and calls a callback with updates."""

    def __init__(self, callback=None, interval: float = 2.0):
        """
        Args:
            callback: function(cpu_percent, ram_mb, ram_percent) called on each tick
            interval: seconds between updates
        """
        self.callback = callback
        self.interval = interval
        self._running = False
        self._thread = None
        self._process = psutil.Process(os.getpid())
        self._gc_counter = 0

    def start(self):
        """Start the monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Resource monitor started")

    def stop(self):
        """Stop the monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Resource monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # CPU usage (over interval period)
                cpu = self._process.cpu_percent(interval=self.interval)

                # Memory usage
                mem_info = self._process.memory_info()
                ram_mb = mem_info.rss / (1024 * 1024)
                ram_percent = self._process.memory_percent()

                # Log every 15th tick (~30 seconds) to avoid log spam
                self._gc_counter += 1
                if self._gc_counter % 15 == 0:
                    log_resource_usage(cpu, ram_mb, ram_percent)



                # Callback to update UI
                if self.callback:
                    try:
                        self.callback(cpu, ram_mb, ram_percent)
                    except Exception:
                        pass  # UI might be closing

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")

    def get_snapshot(self):
        """Get current resource usage snapshot."""
        try:
            cpu = self._process.cpu_percent(interval=0.1)
            mem = self._process.memory_info()
            return {
                "cpu_percent": cpu,
                "ram_mb": mem.rss / (1024 * 1024),
                "ram_percent": self._process.memory_percent(),
                "threads": self._process.num_threads(),
            }
        except Exception:
            return {"cpu_percent": 0, "ram_mb": 0, "ram_percent": 0, "threads": 0}


def cleanup_memory():
    """Force garbage collection and log results."""
    collected = gc.collect()
    if collected > 0:
        log_memory_cleanup(collected)
    return collected


