"""
Nexus Logger Cleanup - Manage lifecycle of local log files.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup basic logging for the cleanup process
logger = logging.getLogger("nexus.cleanup")

class LogCleanupManager:
    """
    Manages the cleanup of log files in a specified directory.
    """

    def __init__(self, log_dir: str = "/tmp/nexus_logs", retention_days: int = 7):
        self.log_dir = Path(log_dir).expanduser()
        self.retention_days = retention_days

    def ensure_dir(self):
        """Ensure the log directory exists."""
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created log directory: {self.log_dir}")

    def perform_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Scan and delete logs older than retention_days.
        """
        self.ensure_dir()
        
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=self.retention_days)
        
        stats = {
            "deleted": 0,
            "freed_bytes": 0,
            "errors": [],
            "kept": 0
        }

        for item in self.log_dir.iterdir():
            if item.is_file():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        size = item.stat().st_size
                        if not dry_run:
                            item.unlink()
                        stats["deleted"] += 1
                        stats["freed_bytes"] += size
                    else:
                        stats["kept"] += 1
                except Exception as e:
                    stats["errors"].append(f"Error processing {item.name}: {str(e)}")

        return stats

def run_cleanup(log_dir: str = "/tmp/nexus_logs", days: int = 7) -> Dict[str, Any]:
    """Helper function to trigger cleanup."""
    manager = LogCleanupManager(log_dir, days)
    return manager.perform_cleanup()
