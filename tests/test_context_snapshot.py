#!/usr/bin/env python3
"""
Tests for nexus-dist/context/snapshot.py
Tests the parallel snapshot mechanism.
"""

import sys
from pathlib import Path

# Add nexus-dist/context to path
sys.path.insert(0, str(Path(__file__).parent.parent / "nexus-dist" / "context"))

import pytest
from datetime import datetime
from snapshot import (
    Anchor,
    ContextSnapshot,
    create_snapshot,
    get_snapshot_for_task,
)


class TestAnchor:
    """Test Anchor dataclass."""

    def test_create_anchor(self):
        """Test creating an Anchor."""
        anchor = Anchor(
            anchor_type="D",
            content="Use JWT for authentication",
            metadata={"priority": "high"},
        )

        assert anchor.anchor_type == "D"
        assert anchor.content == "Use JWT for authentication"
        assert anchor.metadata == {"priority": "high"}

    def test_anchor_immutable(self):
        """Test that Anchor is immutable (frozen)."""
        anchor = Anchor(anchor_type="D", content="test")

        with pytest.raises(AttributeError):
            anchor.anchor_type = "C"

    def test_anchor_default_metadata(self):
        """Test Anchor with default metadata."""
        anchor = Anchor(anchor_type="D", content="test")
        assert anchor.metadata == {}


class TestContextSnapshot:
    """Test ContextSnapshot dataclass."""

    def test_create_snapshot(self):
        """Test creating a ContextSnapshot."""
        anchors = [
            Anchor(anchor_type="D", content="decision 1"),
            Anchor(anchor_type="C", content="constraint 1"),
        ]

        snapshot = ContextSnapshot(
            session_id="session-123",
            timestamp=datetime.now(),
            compact_context="Test context",
            anchors=anchors,
            metadata={"project": "test"},
        )

        assert snapshot.session_id == "session-123"
        assert snapshot.compact_context == "Test context"
        assert len(snapshot.anchors) == 2
        assert snapshot.metadata == {"project": "test"}

    def test_snapshot_immutable(self):
        """Test that ContextSnapshot is immutable (frozen)."""
        snapshot = ContextSnapshot(
            session_id="test",
            timestamp=datetime.now(),
            compact_context="test",
            anchors=[],
        )

        with pytest.raises(AttributeError):
            snapshot.session_id = "changed"

    def test_snapshot_default_metadata(self):
        """Test ContextSnapshot with default metadata."""
        snapshot = ContextSnapshot(
            session_id="test",
            timestamp=datetime.now(),
            compact_context="test",
            anchors=[],
        )
        assert snapshot.metadata == {}


class TestCreateSnapshot:
    """Test the create_snapshot() function."""

    def test_create_snapshot_basic(self):
        """Test creating a basic snapshot."""
        snapshot = create_snapshot(
            session_id="session-abc",
            compact_context="Working on authentication",
            anchors=[
                {"type": "D", "content": "Use JWT"},
                {"type": "C", "content": "HTTPS required"},
            ],
        )

        assert snapshot.session_id == "session-abc"
        assert snapshot.compact_context == "Working on authentication"
        assert len(snapshot.anchors) == 2
        assert isinstance(snapshot.timestamp, datetime)

    def test_create_snapshot_with_metadata(self):
        """Test creating snapshot with metadata."""
        snapshot = create_snapshot(
            session_id="session-abc",
            compact_context="Test",
            anchors=[],
            metadata={"project": "nexus", "phase": 1},
        )

        assert snapshot.metadata == {"project": "nexus", "phase": 1}

    def test_create_snapshot_default_anchor_type(self):
        """Test that anchors without type default to 'P'."""
        snapshot = create_snapshot(
            session_id="test",
            compact_context="test",
            anchors=[
                {"content": "no type specified"},
            ],
        )

        assert snapshot.anchors[0].anchor_type == "P"

    def test_create_snapshot_anchor_metadata(self):
        """Test that anchor metadata is preserved."""
        snapshot = create_snapshot(
            session_id="test",
            compact_context="test",
            anchors=[
                {
                    "type": "D",
                    "content": "decision",
                    "priority": "high",
                    "author": "architect",
                },
            ],
        )

        anchor = snapshot.anchors[0]
        assert anchor.anchor_type == "D"
        assert anchor.content == "decision"
        assert anchor.metadata == {"priority": "high", "author": "architect"}

    def test_create_snapshot_immutability(self):
        """Test that created snapshot is immutable."""
        snapshot = create_snapshot(
            session_id="test",
            compact_context="test",
            anchors=[],
        )

        with pytest.raises(AttributeError):
            snapshot.compact_context = "modified"


class TestGetSnapshotForTask:
    """Test the get_snapshot_for_task() function."""

    def test_format_basic_snapshot(self):
        """Test formatting a basic snapshot."""
        snapshot = create_snapshot(
            session_id="session-123",
            compact_context="Working on auth module",
            anchors=[
                {"type": "D", "content": "Use JWT"},
            ],
        )

        prompt = get_snapshot_for_task(snapshot, "task-001")

        # Should contain headers
        assert "## 上下文快照 (Context Snapshot)" in prompt
        assert "Session: session-123" in prompt
        assert "Task: task-001" in prompt

        # Should contain context
        assert "### 缩形态上下文" in prompt
        assert "Working on auth module" in prompt

        # Should contain anchors
        assert "### 相关锚点" in prompt
        assert "[D] Use JWT" in prompt

    def test_format_snapshot_no_anchors(self):
        """Test formatting snapshot without anchors."""
        snapshot = create_snapshot(
            session_id="session-123",
            compact_context="Test context",
            anchors=[],
        )

        prompt = get_snapshot_for_task(snapshot, "task-001")

        # Should still have session and context
        assert "Session: session-123" in prompt
        assert "Test context" in prompt

        # Should not have anchor section
        assert "### 相关锚点" not in prompt

    def test_format_snapshot_multiple_anchors(self):
        """Test formatting snapshot with multiple anchors."""
        snapshot = create_snapshot(
            session_id="session-123",
            compact_context="Test",
            anchors=[
                {"type": "D", "content": "Decision 1"},
                {"type": "C", "content": "Constraint 1"},
                {"type": "I", "content": "Interface 1"},
            ],
        )

        prompt = get_snapshot_for_task(snapshot, "task-001")

        # Should contain all anchors
        assert "[D] Decision 1" in prompt
        assert "[C] Constraint 1" in prompt
        assert "[I] Interface 1" in prompt

    def test_format_consistent_for_same_snapshot(self):
        """Test that the same snapshot produces consistent output for different tasks."""
        snapshot = create_snapshot(
            session_id="session-123",
            compact_context="Test context",
            anchors=[{"type": "D", "content": "Decision"}],
        )

        prompt1 = get_snapshot_for_task(snapshot, "task-001")
        prompt2 = get_snapshot_for_task(snapshot, "task-002")

        # Context should be identical except task ID
        assert "session-123" in prompt1
        assert "session-123" in prompt2
        assert "Test context" in prompt1
        assert "Test context" in prompt2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
