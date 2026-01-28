#!/usr/bin/env python3
"""
Tests for runtime/state_manager.py
Tests atomic state management.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add runtime to path
sys.path.insert(0, str(Path(__file__).parent.parent / "runtime"))

import pytest
from state_manager import StateManager, RuntimeState


class TestRuntimeState:
    """Test RuntimeState dataclass."""

    def test_create_runtime_state(self):
        """Test creating a RuntimeState."""
        state = RuntimeState(
            current_graph_id="graph-123",
            current_phase=1,
            status="running",
        )

        assert state.current_graph_id == "graph-123"
        assert state.current_phase == 1
        assert state.status == "running"

    def test_runtime_state_defaults(self):
        """Test RuntimeState default values."""
        state = RuntimeState()

        assert state.current_graph_id is None
        assert state.current_phase == 0
        assert state.active_nodes == []
        assert state.completed_nodes == []
        assert state.failed_nodes == []
        assert state.status == "idle"
        assert state.metadata == {}
        assert state.heartbeats == {}

    def test_to_dict(self):
        """Test converting RuntimeState to dict."""
        state = RuntimeState(
            current_graph_id="graph-123",
            status="running",
            active_nodes=["node-1", "node-2"],
        )

        data = state.to_dict()

        assert data["current_graph_id"] == "graph-123"
        assert data["status"] == "running"
        assert data["active_nodes"] == ["node-1", "node-2"]

    def test_from_dict(self):
        """Test creating RuntimeState from dict."""
        data = {
            "current_graph_id": "graph-123",
            "status": "running",
            "active_nodes": ["node-1"],
        }

        state = RuntimeState.from_dict(data)

        assert state.current_graph_id == "graph-123"
        assert state.status == "running"
        assert state.active_nodes == ["node-1"]


class TestStateManager:
    """Test StateManager class."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        fd, path = tempfile.mkstemp(suffix=".json")
        yield Path(path)
        if Path(path).exists():
            Path(path).unlink()

    @pytest.fixture
    def manager(self, temp_file):
        """Create a StateManager instance."""
        return StateManager(temp_file)

    def test_init_creates_parent_directory(self, temp_file):
        """Test that initialization creates parent directory."""
        nested_path = temp_file.parent / "subdir" / "state.json"
        manager = StateManager(nested_path)

        assert nested_path.parent.exists()

    def test_get_state_returns_default_if_not_exists(self, manager):
        """Test that get_state returns default state if file doesn't exist."""
        state = manager.get_state()

        assert state["status"] == "idle"
        assert state["current_graph_id"] is None

    def test_set_and_get_state(self, manager):
        """Test setting and getting state."""
        new_state = {
            "current_graph_id": "graph-123",
            "status": "running",
            "current_phase": 1,
        }

        manager.set_state(new_state)
        retrieved = manager.get_state()

        assert retrieved["current_graph_id"] == "graph-123"
        assert retrieved["status"] == "running"
        assert retrieved["current_phase"] == 1

    def test_set_state_adds_timestamp(self, manager):
        """Test that set_state adds updated_at timestamp."""
        manager.set_state({"status": "running"})
        state = manager.get_state()

        assert "updated_at" in state
        assert state["updated_at"] is not None

    def test_update_state(self, manager):
        """Test updating specific fields."""
        manager.set_state({"status": "idle", "current_phase": 0})

        manager.update_state(status="running", current_phase=1)
        state = manager.get_state()

        assert state["status"] == "running"
        assert state["current_phase"] == 1

    def test_reset_state(self, manager):
        """Test resetting state to defaults."""
        manager.set_state({
            "status": "running",
            "current_graph_id": "graph-123",
            "current_phase": 5,
        })

        manager.reset_state()
        state = manager.get_state()

        assert state["status"] == "idle"
        assert state["current_graph_id"] is None
        assert state["current_phase"] == 0

    def test_start_graph(self, manager):
        """Test starting a task graph."""
        state = manager.start_graph("graph-123", "session-abc")

        assert state["current_graph_id"] == "graph-123"
        assert state["session_id"] == "session-abc"
        assert state["status"] == "running"
        assert state["current_phase"] == 0
        assert state["active_nodes"] == []
        assert state["completed_nodes"] == []
        assert state["failed_nodes"] == []

    def test_complete_graph(self, manager):
        """Test completing a graph."""
        manager.start_graph("graph-123", "session-abc")
        manager.update_state(active_nodes=["node-1", "node-2"])

        state = manager.complete_graph()

        assert state["status"] == "completed"
        assert state["active_nodes"] == []

    def test_abort_graph(self, manager):
        """Test aborting a graph."""
        manager.start_graph("graph-123", "session-abc")

        state = manager.abort_graph(reason="User cancelled")

        assert state["status"] == "aborted"
        assert state["active_nodes"] == []
        assert state["metadata"]["abort_reason"] == "User cancelled"

    def test_activate_node(self, manager):
        """Test activating a node."""
        manager.start_graph("graph-123", "session-abc")

        state = manager.activate_node("node-1")
        assert "node-1" in state["active_nodes"]

        state = manager.activate_node("node-2")
        assert "node-1" in state["active_nodes"]
        assert "node-2" in state["active_nodes"]

    def test_activate_node_no_duplicates(self, manager):
        """Test that activating same node doesn't create duplicates."""
        manager.start_graph("graph-123", "session-abc")

        manager.activate_node("node-1")
        manager.activate_node("node-1")

        state = manager.get_state()
        assert state["active_nodes"].count("node-1") == 1

    def test_complete_node(self, manager):
        """Test completing a node."""
        manager.start_graph("graph-123", "session-abc")
        manager.activate_node("node-1")

        state = manager.complete_node("node-1")

        assert "node-1" not in state["active_nodes"]
        assert "node-1" in state["completed_nodes"]

    def test_fail_node(self, manager):
        """Test failing a node."""
        manager.start_graph("graph-123", "session-abc")
        manager.activate_node("node-1")

        state = manager.fail_node("node-1")

        assert "node-1" not in state["active_nodes"]
        assert "node-1" in state["failed_nodes"]

    def test_advance_phase(self, manager):
        """Test advancing execution phase."""
        manager.start_graph("graph-123", "session-abc")

        state = manager.advance_phase()
        assert state["current_phase"] == 1

        state = manager.advance_phase()
        assert state["current_phase"] == 2

    def test_pause_graph(self, manager):
        """Test pausing graph execution."""
        manager.start_graph("graph-123", "session-abc")

        state = manager.pause_graph()
        assert state["status"] == "paused"

    def test_get_interrupted_nodes(self, manager):
        """Test getting interrupted nodes."""
        manager.start_graph("graph-123", "session-abc")
        manager.activate_node("node-1")
        manager.activate_node("node-2")

        interrupted = manager.get_interrupted_nodes()

        assert "node-1" in interrupted
        assert "node-2" in interrupted

    def test_prepare_for_resume(self, manager):
        """Test preparing for resume."""
        manager.start_graph("graph-123", "session-abc")
        manager.activate_node("node-1")
        manager.activate_node("node-2")

        result = manager.prepare_for_resume()

        assert result["success"] is True
        assert "node-1" in result["resumed_nodes"]
        assert "node-2" in result["resumed_nodes"]
        assert result["status"] == "running"
        assert result["graph_id"] == "graph-123"

        # Active nodes should be cleared
        state = manager.get_state()
        assert state["active_nodes"] == []

    def test_prepare_for_resume_no_task(self, manager):
        """Test prepare_for_resume with no task."""
        result = manager.prepare_for_resume()

        assert result["success"] is False
        assert "No task to resume" in result["error"]

    def test_prepare_for_resume_completed_task(self, manager):
        """Test prepare_for_resume with completed task."""
        manager.start_graph("graph-123", "session-abc")
        manager.complete_graph()

        result = manager.prepare_for_resume()

        assert result["success"] is False
        assert "already completed" in result["error"]

    def test_record_retry(self, manager):
        """Test recording retry attempts."""
        manager.start_graph("graph-123", "session-abc")
        manager.fail_node("node-1")

        state = manager.record_retry("node-1")

        assert "node-1" not in state["failed_nodes"]
        assert state["metadata"]["retry_counts"]["node-1"] == 1

        manager.record_retry("node-1")
        state = manager.get_state()
        assert state["metadata"]["retry_counts"]["node-1"] == 2

    def test_get_retry_count(self, manager):
        """Test getting retry count."""
        manager.start_graph("graph-123", "session-abc")

        assert manager.get_retry_count("node-1") == 0

        manager.record_retry("node-1")
        assert manager.get_retry_count("node-1") == 1

        manager.record_retry("node-1")
        assert manager.get_retry_count("node-1") == 2

    def test_atomic_write_crash_safety(self, manager, temp_file):
        """Test that atomic write ensures crash safety."""
        manager.set_state({"status": "running"})

        # File should exist and be readable
        assert temp_file.exists()
        state = manager.get_state()
        assert state["status"] == "running"

        # No .tmp files should remain
        temp_files = list(temp_file.parent.glob("state_*.json.tmp"))
        assert len(temp_files) == 0

    def test_get_runtime_state(self, manager):
        """Test getting state as RuntimeState object."""
        manager.set_state({
            "current_graph_id": "graph-123",
            "status": "running",
            "current_phase": 1,
        })

        state = manager.get_runtime_state()

        assert isinstance(state, RuntimeState)
        assert state.current_graph_id == "graph-123"
        assert state.status == "running"
        assert state.current_phase == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
