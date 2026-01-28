#!/usr/bin/env python3
"""
Tests for nexus-dist/context/cleanup.py
Tests the session cleanup system.
"""

import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add nexus-dist/context to path
sys.path.insert(0, str(Path(__file__).parent.parent / "nexus-dist" / "context"))

import pytest
from cleanup import (
    cleanup_old_sessions,
    list_sessions,
    preview_cleanup,
    get_cleanup_summary,
    get_sessions_dir,
    get_dir_size,
    CleanupStats,
    SessionInfo,
)


class TestGetSessionsDir:
    """Test get_sessions_dir function."""

    def test_default_path(self):
        """Test default sessions directory path."""
        path = get_sessions_dir()
        assert str(path).endswith(".nexus/context/sessions")

    def test_custom_path(self):
        """Test custom sessions directory path."""
        custom = Path("/tmp/custom/sessions")
        path = get_sessions_dir(custom)
        assert path == custom


class TestGetDirSize:
    """Test get_dir_size function."""

    def test_empty_dir(self):
        """Test size of empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            size = get_dir_size(Path(tmpdir))
            assert size == 0

    def test_dir_with_files(self):
        """Test size of directory with files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            # Create a file with known content
            test_file = tmppath / "test.txt"
            test_file.write_text("hello world")  # 11 bytes
            size = get_dir_size(tmppath)
            assert size == 11

    def test_nonexistent_dir(self):
        """Test size of nonexistent directory."""
        size = get_dir_size(Path("/nonexistent/path"))
        assert size == 0


class TestListSessions:
    """Test list_sessions function."""

    def test_empty_sessions_dir(self):
        """Test listing when sessions directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions = list_sessions(Path(tmpdir) / "nonexistent")
            assert sessions == []

    def test_list_sessions(self):
        """Test listing sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create some session directories
            (tmppath / "session-001").mkdir()
            (tmppath / "session-002").mkdir()
            (tmppath / "session-003").mkdir()

            sessions = list_sessions(tmppath)

            assert len(sessions) == 3
            session_names = [s.name for s in sessions]
            assert "session-001" in session_names
            assert "session-002" in session_names
            assert "session-003" in session_names

    def test_list_sessions_with_age_filter(self):
        """Test listing sessions with age filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a session directory
            session = tmppath / "old-session"
            session.mkdir()

            # Sessions created just now won't be older than 30 days
            sessions = list_sessions(tmppath, max_age_days=30)
            assert len(sessions) == 0

            # But they should appear with 0 days filter
            sessions = list_sessions(tmppath, max_age_days=0)
            assert len(sessions) == 1


class TestCleanupOldSessions:
    """Test cleanup_old_sessions function."""

    def test_cleanup_empty_dir(self):
        """Test cleanup when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = cleanup_old_sessions(
                max_age_days=30,
                base_dir=Path(tmpdir) / "nonexistent",
            )
            assert stats.sessions_deleted == 0
            assert stats.bytes_freed == 0
            assert stats.errors == []

    def test_cleanup_dry_run(self):
        """Test dry run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create session directories
            session = tmppath / "session-001"
            session.mkdir()
            (session / "data.txt").write_text("test data")

            # Dry run with 0 days age (should match all)
            stats = cleanup_old_sessions(
                max_age_days=0,
                base_dir=tmppath,
                dry_run=True,
            )

            # Should report what would be deleted
            assert stats.sessions_deleted == 1
            assert stats.bytes_freed > 0

            # But directory should still exist
            assert session.exists()

    def test_cleanup_actually_deletes(self):
        """Test that cleanup actually deletes sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create session directories
            session = tmppath / "session-001"
            session.mkdir()
            (session / "data.txt").write_text("test data")

            # Actually delete (0 days age matches all)
            stats = cleanup_old_sessions(
                max_age_days=0,
                base_dir=tmppath,
                dry_run=False,
            )

            # Should have deleted
            assert stats.sessions_deleted == 1
            assert stats.bytes_freed > 0

            # Directory should be gone
            assert not session.exists()

    def test_cleanup_keeps_recent_sessions(self):
        """Test that recent sessions are kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create a session directory (created now, so 0 days old)
            session = tmppath / "recent-session"
            session.mkdir()

            # Try to delete sessions older than 30 days
            stats = cleanup_old_sessions(
                max_age_days=30,
                base_dir=tmppath,
                dry_run=False,
            )

            # Should not delete (too recent)
            assert stats.sessions_deleted == 0
            assert stats.sessions_kept == 1
            assert session.exists()


class TestPreviewCleanup:
    """Test preview_cleanup function."""

    def test_preview_no_sessions(self):
        """Test preview when no sessions to delete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preview_cleanup(max_age_days=30, base_dir=Path(tmpdir))
            assert "No sessions" in result

    def test_preview_with_sessions(self):
        """Test preview when there are sessions to delete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create session directories
            session = tmppath / "session-001"
            session.mkdir()

            # Use 0 days to match all
            result = preview_cleanup(max_age_days=0, base_dir=tmppath)

            assert "session-001" in result
            assert "Total:" in result


class TestGetCleanupSummary:
    """Test get_cleanup_summary function."""

    def test_summary_nonexistent_dir(self):
        """Test summary when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_cleanup_summary(Path(tmpdir) / "nonexistent")
            assert "does not exist" in result

    def test_summary_empty_dir(self):
        """Test summary when directory is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_cleanup_summary(Path(tmpdir))
            assert "No sessions found" in result

    def test_summary_with_sessions(self):
        """Test summary with sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create session directories
            (tmppath / "session-001").mkdir()
            (tmppath / "session-002").mkdir()

            result = get_cleanup_summary(tmppath)

            assert "Session Storage Summary" in result
            assert "Total sessions: 2" in result
            assert "Age distribution:" in result


class TestCleanupStats:
    """Test CleanupStats dataclass."""

    def test_bytes_freed_human_bytes(self):
        """Test human-readable size for bytes."""
        stats = CleanupStats(0, 100, 0, [])
        assert stats.bytes_freed_human == "100.0 B"

    def test_bytes_freed_human_kb(self):
        """Test human-readable size for kilobytes."""
        stats = CleanupStats(0, 2048, 0, [])
        assert stats.bytes_freed_human == "2.0 KB"

    def test_bytes_freed_human_mb(self):
        """Test human-readable size for megabytes."""
        stats = CleanupStats(0, 5 * 1024 * 1024, 0, [])
        assert stats.bytes_freed_human == "5.0 MB"


class TestSessionInfo:
    """Test SessionInfo dataclass."""

    def test_size_human(self):
        """Test human-readable size."""
        info = SessionInfo(
            path=Path("/tmp/test"),
            name="test",
            size_bytes=1024,
            modified_time=datetime.now(),
            age_days=0,
        )
        assert info.size_human == "1.0 KB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
