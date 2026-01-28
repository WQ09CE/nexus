"""
Session Cleanup Module (会话清理模块)

Provides utilities for cleaning up old session data from ~/.nexus/context/sessions/.
"""

import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class CleanupStats:
    """Statistics from a cleanup operation."""
    sessions_deleted: int
    bytes_freed: int
    sessions_kept: int
    errors: List[str]

    @property
    def bytes_freed_human(self) -> str:
        """Return human-readable size."""
        size = self.bytes_freed
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class SessionInfo:
    """Information about a session directory."""
    path: Path
    name: str
    size_bytes: int
    modified_time: datetime
    age_days: int

    @property
    def size_human(self) -> str:
        """Return human-readable size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def get_sessions_dir(base_dir: Optional[Path] = None) -> Path:
    """
    Get the sessions directory path.

    Args:
        base_dir: Optional base directory. Defaults to ~/.nexus/context/sessions

    Returns:
        Path to sessions directory
    """
    if base_dir:
        return Path(base_dir).expanduser()
    return Path("~/.nexus/context/sessions").expanduser()


def get_dir_size(path: Path) -> int:
    """
    Calculate total size of a directory.

    Args:
        path: Directory path

    Returns:
        Total size in bytes
    """
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (OSError, PermissionError):
        pass
    return total


def list_sessions(
    base_dir: Optional[Path] = None,
    max_age_days: Optional[int] = None,
) -> List[SessionInfo]:
    """
    List all sessions in the sessions directory.

    Args:
        base_dir: Optional base directory for sessions
        max_age_days: If provided, only return sessions older than this

    Returns:
        List of SessionInfo objects sorted by age (oldest first)
    """
    sessions_dir = get_sessions_dir(base_dir)

    if not sessions_dir.exists():
        return []

    now = datetime.now(timezone.utc)
    sessions = []

    for item in sessions_dir.iterdir():
        if item.is_dir():
            try:
                stat = item.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                age = (now - mtime).days

                # Filter by age if specified
                if max_age_days is not None and age < max_age_days:
                    continue

                sessions.append(SessionInfo(
                    path=item,
                    name=item.name,
                    size_bytes=get_dir_size(item),
                    modified_time=mtime,
                    age_days=age,
                ))
            except (OSError, PermissionError):
                continue

    # Sort by age (oldest first)
    sessions.sort(key=lambda s: s.modified_time)
    return sessions


def cleanup_old_sessions(
    max_age_days: int = 30,
    base_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> CleanupStats:
    """
    Clean up sessions older than the specified number of days.

    Args:
        max_age_days: Delete sessions older than this many days (default: 30)
        base_dir: Optional base directory for sessions
        dry_run: If True, only preview what would be deleted without actually deleting

    Returns:
        CleanupStats with information about the cleanup operation

    Example:
        # Preview what would be deleted
        stats = cleanup_old_sessions(max_age_days=30, dry_run=True)
        print(f"Would delete {stats.sessions_deleted} sessions, freeing {stats.bytes_freed_human}")

        # Actually delete
        stats = cleanup_old_sessions(max_age_days=30)
        print(f"Deleted {stats.sessions_deleted} sessions, freed {stats.bytes_freed_human}")
    """
    sessions_dir = get_sessions_dir(base_dir)

    # Get sessions to delete
    old_sessions = list_sessions(base_dir, max_age_days=max_age_days)

    # Count sessions that would be kept
    all_sessions = list_sessions(base_dir)
    sessions_kept = len(all_sessions) - len(old_sessions)

    stats = CleanupStats(
        sessions_deleted=0,
        bytes_freed=0,
        sessions_kept=sessions_kept,
        errors=[],
    )

    for session in old_sessions:
        if dry_run:
            # Just count what would be deleted
            stats.sessions_deleted += 1
            stats.bytes_freed += session.size_bytes
        else:
            # Actually delete
            try:
                shutil.rmtree(session.path)
                stats.sessions_deleted += 1
                stats.bytes_freed += session.size_bytes
            except (OSError, PermissionError) as e:
                stats.errors.append(f"Failed to delete {session.path}: {e}")

    return stats


def preview_cleanup(
    max_age_days: int = 30,
    base_dir: Optional[Path] = None,
) -> str:
    """
    Preview what would be cleaned up without actually deleting.

    Args:
        max_age_days: Sessions older than this many days would be deleted
        base_dir: Optional base directory for sessions

    Returns:
        Human-readable preview string
    """
    sessions = list_sessions(base_dir, max_age_days=max_age_days)

    if not sessions:
        return f"No sessions older than {max_age_days} days found."

    lines = [
        f"Sessions to be deleted (older than {max_age_days} days):",
        "-" * 60,
    ]

    total_size = 0
    for session in sessions:
        lines.append(
            f"  {session.name}: {session.size_human}, "
            f"{session.age_days} days old"
        )
        total_size += session.size_bytes

    lines.append("-" * 60)
    lines.append(f"Total: {len(sessions)} sessions, {CleanupStats(0, total_size, 0, []).bytes_freed_human}")

    return "\n".join(lines)


def get_cleanup_summary(
    base_dir: Optional[Path] = None,
) -> str:
    """
    Get a summary of the sessions directory.

    Args:
        base_dir: Optional base directory for sessions

    Returns:
        Human-readable summary string
    """
    sessions_dir = get_sessions_dir(base_dir)

    if not sessions_dir.exists():
        return f"Sessions directory does not exist: {sessions_dir}"

    sessions = list_sessions(base_dir)

    if not sessions:
        return "No sessions found."

    total_size = sum(s.size_bytes for s in sessions)
    oldest = sessions[0] if sessions else None
    newest = sessions[-1] if sessions else None

    lines = [
        "Session Storage Summary",
        "-" * 40,
        f"Directory: {sessions_dir}",
        f"Total sessions: {len(sessions)}",
        f"Total size: {CleanupStats(0, total_size, 0, []).bytes_freed_human}",
    ]

    if oldest:
        lines.append(f"Oldest session: {oldest.name} ({oldest.age_days} days old)")
    if newest and newest != oldest:
        lines.append(f"Newest session: {newest.name} ({newest.age_days} days old)")

    # Age distribution
    age_30 = sum(1 for s in sessions if s.age_days > 30)
    age_7 = sum(1 for s in sessions if s.age_days > 7)

    lines.append("")
    lines.append("Age distribution:")
    lines.append(f"  > 30 days: {age_30} sessions")
    lines.append(f"  > 7 days: {age_7} sessions")
    lines.append(f"  <= 7 days: {len(sessions) - age_7} sessions")

    return "\n".join(lines)
