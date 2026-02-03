"""
Tests for the PreCompact hook.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest


# Path to the hook script
HOOK_SCRIPT = Path(__file__).parent.parent / "nexus-dist" / "hooks" / "precompact_save.py"


def run_hook(input_data: dict) -> tuple[int, str, str]:
    """Run the hook script with given input and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestPrecompactHook:
    """Tests for precompact_save.py hook."""

    def test_successful_save(self, tmp_path):
        """Test successful transcript save."""
        # Create a mock transcript file
        transcript_file = tmp_path / "session.jsonl"
        transcript_file.write_text('{"message": "test"}\n{"message": "test2"}\n')

        # Create a temp context directory
        context_dir = tmp_path / "context"

        # Prepare input
        input_data = {
            "session_id": "test_session_123456",
            "transcript_path": str(transcript_file),
            "cwd": "/path/to/myproject",
            "hook_event_name": "PreCompact",
            "trigger": "auto",
        }

        # Run the hook (it will save to ~/.nexus/context, but we test the logic)
        returncode, stdout, stderr = run_hook(input_data)

        # Check that it succeeded
        assert returncode == 0
        assert "Saved context" in stderr
        assert "myproject" in stderr  # Project name extracted from cwd

    def test_missing_session_id(self):
        """Test error when session_id is missing."""
        input_data = {
            "transcript_path": "/some/path",
            "cwd": "/some/cwd",
        }
        returncode, stdout, stderr = run_hook(input_data)
        assert returncode == 1
        assert "Missing session_id" in stderr

    def test_missing_transcript_path(self):
        """Test error when transcript_path is missing."""
        input_data = {
            "session_id": "abc123",
            "cwd": "/some/cwd",
        }
        returncode, stdout, stderr = run_hook(input_data)
        assert returncode == 1
        assert "Missing transcript_path" in stderr

    def test_missing_cwd(self):
        """Test error when cwd is missing."""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/some/path",
        }
        returncode, stdout, stderr = run_hook(input_data)
        assert returncode == 1
        assert "Missing cwd" in stderr

    def test_transcript_file_not_found(self):
        """Test error when transcript file doesn't exist."""
        input_data = {
            "session_id": "abc123",
            "transcript_path": "/nonexistent/file.jsonl",
            "cwd": "/some/cwd",
        }
        returncode, stdout, stderr = run_hook(input_data)
        assert returncode == 1
        assert "Transcript file not found" in stderr

    def test_empty_input(self):
        """Test error when stdin is empty."""
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "No input received" in result.stderr

    def test_invalid_json(self):
        """Test error when input is not valid JSON."""
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Failed to parse JSON" in result.stderr

    def test_project_name_extraction(self, tmp_path):
        """Test that project name is correctly extracted from cwd."""
        transcript_file = tmp_path / "session.jsonl"
        transcript_file.write_text('{"test": true}\n')

        input_data = {
            "session_id": "test123",
            "transcript_path": str(transcript_file),
            "cwd": "/Users/someone/projects/my-awesome-project",
            "hook_event_name": "PreCompact",
            "trigger": "auto",
        }

        returncode, stdout, stderr = run_hook(input_data)

        assert returncode == 0
        assert "my-awesome-project" in stderr

    def test_filename_format(self, tmp_path):
        """Test that filename follows expected format: {timestamp}_{session_id}.jsonl"""
        transcript_file = tmp_path / "session.jsonl"
        transcript_file.write_text('{"test": true}\n')

        input_data = {
            "session_id": "abcd1234efgh5678",
            "transcript_path": str(transcript_file),
            "cwd": "/path/to/project",
            "hook_event_name": "PreCompact",
            "trigger": "auto",
        }

        returncode, stdout, stderr = run_hook(input_data)

        assert returncode == 0
        # Session ID should be truncated to 8 chars
        assert "abcd1234.jsonl" in stderr
