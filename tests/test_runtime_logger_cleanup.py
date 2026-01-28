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
    exact_file = temp_log_dir / "exact.log"
    new_file = temp_log_dir / "new.log"
    
    old_file.write_text("old")
    exact_file.write_text("exact")
    new_file.write_text("new")
    
    # Set old_file to 10 days ago
    ten_days_ago = now - (10 * 24 * 60 * 60)
    os.utime(old_file, (ten_days_ago, ten_days_ago))
    
    # Set exact_file to exactly 7 days ago (minus a small buffer to ensure it's not BEFORE the cutoff)
    seven_days_ago = now - (7 * 24 * 60 * 60) + 60
    os.utime(exact_file, (seven_days_ago, seven_days_ago))
    
    manager = LogCleanupManager(log_dir=str(temp_log_dir), retention_days=7)
    stats = manager.perform_cleanup()
    
    # Files < 7 days kept. 10 days deleted. 
    # Current logic: mtime < cutoff (deleted). 
    # 7 days ago is exactly the cutoff. 
    assert stats["deleted"] == 1 # only the 10-day one
    assert stats["kept"] == 2
    assert not old_file.exists()
    assert exact_file.exists()
    assert new_file.exists()

def test_non_existent_dir_behavior(tmp_path):
    non_existent = tmp_path / "ghost_logs"
    manager = LogCleanupManager(log_dir=str(non_existent))
    
    # Should create and return 0 stats
    stats = manager.perform_cleanup()
    assert non_existent.exists()
    assert stats["deleted"] == 0
    assert stats["kept"] == 0

def test_permission_error_handling(temp_log_dir):
    # Create a file that we can't delete
    protected_file = temp_log_dir / "protected.log"
    protected_file.write_text("protected")
    
    # Set to old
    ten_days_ago = time.time() - (10 * 24 * 60 * 60)
    os.utime(protected_file, (ten_days_ago, ten_days_ago))
    
    # Make directory non-writable (so unlinking fails)
    os.chmod(temp_log_dir, 0o555)
    
    try:
        manager = LogCleanupManager(log_dir=str(temp_log_dir), retention_days=7)
        stats = manager.perform_cleanup()
        
        assert len(stats["errors"]) > 0
        assert stats["deleted"] == 0
    finally:
        # Restore permissions for cleanup
        os.chmod(temp_log_dir, 0o755)
