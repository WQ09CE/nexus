"""
Tests for runtime/logger_cleanup.py
"""

import os
import time
import shutil
import pytest
from pathlib import Path
from runtime.logger_cleanup import LogCleanupManager

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory for testing."""
    d = tmp_path / "nexus_logs"
    d.mkdir()
    return d

def test_log_cleanup_retention(temp_log_dir):
    # Setup files
    now = time.time()
    old_file = temp_log_dir / "old.log"
    new_file = temp_log_dir / "new.log"
    
    old_file.write_text("old")
    new_file.write_text("new")
    
    # Set old_file to 10 days ago
    ten_days_ago = now - (10 * 24 * 60 * 60)
    os.utime(old_file, (ten_days_ago, ten_days_ago))
    
    manager = LogCleanupManager(log_dir=str(temp_log_dir), retention_days=7)
    stats = manager.perform_cleanup()
    
    assert stats["deleted"] == 1
    assert stats["kept"] == 1
    assert not old_file.exists()
    assert new_file.exists()

def test_ensure_dir_creates_if_missing(tmp_path):
    missing_dir = tmp_path / "missing_logs"
    manager = LogCleanupManager(log_dir=str(missing_dir))
    
    assert not missing_dir.exists()
    manager.ensure_dir()
    assert missing_dir.exists()
