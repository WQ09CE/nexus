"""
Tests for the memory_update module.
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Import from the hooks module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "nexus-dist" / "hooks"))

from memory_update import (
    extract_file_changes,
    extract_action_phrases,
    extract_points,
    parse_memory_file,
    format_memory_file,
    update_memory,
    update_memory_from_transcript,
    MAX_ENTRIES_PER_PROJECT,
    MAX_ENTRY_LENGTH,
)


class TestExtractFileChanges:
    """Tests for extract_file_changes function."""

    def test_extract_write_tool(self):
        """Test extracting file paths from Write tool calls."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Write",
                            "input": {"file_path": "/path/to/file.py", "content": "..."},
                        }
                    ]
                },
            }
        ]
        files = extract_file_changes(lines)
        assert "file.py" in files

    def test_extract_edit_tool(self):
        """Test extracting file paths from Edit tool calls."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Edit",
                            "input": {"file_path": "/path/to/another.py", "old_string": "...", "new_string": "..."},
                        }
                    ]
                },
            }
        ]
        files = extract_file_changes(lines)
        assert "another.py" in files

    def test_multiple_files(self):
        """Test extracting multiple file paths."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/a/b/file1.py"}},
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "/c/d/file2.md"}},
                    ]
                },
            }
        ]
        files = extract_file_changes(lines)
        assert "file1.py" in files
        assert "file2.md" in files

    def test_deduplicate_files(self):
        """Test that duplicate files are deduplicated."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "/path/same.py"}},
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "/path/same.py"}},
                    ]
                },
            }
        ]
        files = extract_file_changes(lines)
        assert len(files) == 1
        assert "same.py" in files

    def test_ignore_read_tool(self):
        """Test that Read tool is ignored."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "/path/read.py"}},
                    ]
                },
            }
        ]
        files = extract_file_changes(lines)
        assert len(files) == 0

    def test_empty_transcript(self):
        """Test with empty transcript."""
        files = extract_file_changes([])
        assert files == []


class TestExtractActionPhrases:
    """Tests for extract_action_phrases function."""

    def test_extract_created(self):
        """Test extracting 'created' action."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "I created a new function for handling errors."}
                    ]
                },
            }
        ]
        actions = extract_action_phrases(lines)
        assert len(actions) > 0
        assert any("created" in a.lower() for a in actions)

    def test_extract_fixed(self):
        """Test extracting 'fixed' action."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "I fixed the bug in the parser module."}
                    ]
                },
            }
        ]
        actions = extract_action_phrases(lines)
        assert len(actions) > 0
        assert any("fixed" in a.lower() for a in actions)

    def test_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "I IMPLEMENTED the new feature."}
                    ]
                },
            }
        ]
        actions = extract_action_phrases(lines)
        assert len(actions) > 0

    def test_string_content(self):
        """Test with string content instead of list."""
        lines = [
            {
                "type": "assistant",
                "message": {
                    "content": "I added a new test case for the validator."
                },
            }
        ]
        actions = extract_action_phrases(lines)
        assert len(actions) > 0


class TestParseMemoryFile:
    """Tests for parse_memory_file function."""

    def test_parse_existing_file(self, tmp_path):
        """Test parsing an existing memory file."""
        memory_file = tmp_path / "memory.md"
        memory_file.write_text("""# Memory

## project1
- [2026-02-03] Did something
- [2026-02-02] Did something else

## project2
- [2026-02-01] Another thing
""")
        memory = parse_memory_file(memory_file)
        assert "project1" in memory
        assert "project2" in memory
        assert len(memory["project1"]) == 2
        assert len(memory["project2"]) == 1

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a nonexistent file returns empty dict."""
        memory_file = tmp_path / "nonexistent.md"
        memory = parse_memory_file(memory_file)
        assert memory == {}

    def test_parse_empty_file(self, tmp_path):
        """Test parsing an empty file."""
        memory_file = tmp_path / "empty.md"
        memory_file.write_text("")
        memory = parse_memory_file(memory_file)
        assert memory == {}


class TestFormatMemoryFile:
    """Tests for format_memory_file function."""

    def test_format_single_project(self):
        """Test formatting a single project."""
        memory = {"project1": ["- [2026-02-03] Entry 1", "- [2026-02-02] Entry 2"]}
        content = format_memory_file(memory)
        assert "# Memory" in content
        assert "## project1" in content
        assert "- [2026-02-03] Entry 1" in content

    def test_format_multiple_projects(self):
        """Test formatting multiple projects (sorted alphabetically)."""
        memory = {
            "zebra": ["- [2026-02-03] Z entry"],
            "apple": ["- [2026-02-02] A entry"],
        }
        content = format_memory_file(memory)
        # apple should come before zebra
        apple_pos = content.find("## apple")
        zebra_pos = content.find("## zebra")
        assert apple_pos < zebra_pos

    def test_format_empty_memory(self):
        """Test formatting empty memory."""
        memory = {}
        content = format_memory_file(memory)
        assert "# Memory" in content


class TestUpdateMemory:
    """Tests for update_memory function."""

    def test_create_new_memory_file(self, tmp_path):
        """Test creating a new memory file."""
        memory_file = tmp_path / "memory.md"
        result = update_memory("myproject", ["Point 1", "Point 2"], memory_file)
        assert result is True
        assert memory_file.exists()
        content = memory_file.read_text()
        assert "## myproject" in content
        assert "Point 1" in content
        assert "Point 2" in content

    def test_update_existing_project(self, tmp_path):
        """Test updating an existing project."""
        memory_file = tmp_path / "memory.md"
        memory_file.write_text("""# Memory

## myproject
- [2026-02-02] Old entry
""")
        result = update_memory("myproject", ["New entry"], memory_file)
        assert result is True
        content = memory_file.read_text()
        # New entry should be before old entry
        new_pos = content.find("New entry")
        old_pos = content.find("Old entry")
        assert new_pos < old_pos

    def test_add_new_project(self, tmp_path):
        """Test adding a new project to existing file."""
        memory_file = tmp_path / "memory.md"
        memory_file.write_text("""# Memory

## existing
- [2026-02-02] Existing entry
""")
        result = update_memory("newproject", ["New project entry"], memory_file)
        assert result is True
        content = memory_file.read_text()
        assert "## existing" in content
        assert "## newproject" in content

    def test_truncate_to_max_entries(self, tmp_path):
        """Test that entries are truncated to MAX_ENTRIES_PER_PROJECT."""
        memory_file = tmp_path / "memory.md"
        # Create file with MAX_ENTRIES already
        old_entries = [f"- [2026-02-0{i}] Old entry {i}" for i in range(1, MAX_ENTRIES_PER_PROJECT + 1)]
        memory_file.write_text("# Memory\n\n## myproject\n" + "\n".join(old_entries) + "\n")

        # Add new entries
        result = update_memory("myproject", ["New entry 1", "New entry 2"], memory_file)
        assert result is True

        content = memory_file.read_text()
        # Count entries for myproject
        lines = content.split("\n")
        project_entries = [l for l in lines if l.startswith("- [")]
        assert len(project_entries) == MAX_ENTRIES_PER_PROJECT

    def test_empty_points_skips_update(self, tmp_path):
        """Test that empty points list skips update."""
        memory_file = tmp_path / "memory.md"
        result = update_memory("myproject", [], memory_file)
        assert result is True
        assert not memory_file.exists()

    def test_date_format(self, tmp_path):
        """Test that entries have correct date format."""
        memory_file = tmp_path / "memory.md"
        result = update_memory("myproject", ["Test entry"], memory_file)
        assert result is True
        content = memory_file.read_text()
        today = datetime.now().strftime("%Y-%m-%d")
        assert f"[{today}]" in content


class TestExtractPoints:
    """Tests for extract_points function."""

    def test_extract_from_valid_transcript(self, tmp_path):
        """Test extracting points from a valid transcript."""
        transcript_file = tmp_path / "session.jsonl"
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "I implemented a new feature."},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/path/to/new_feature.py"}},
            ]}},
        ]
        transcript_file.write_text("\n".join(json.dumps(l) for l in lines))

        points = extract_points(str(transcript_file))
        assert len(points) > 0

    def test_extract_from_nonexistent_file(self):
        """Test extracting from nonexistent file returns empty list."""
        points = extract_points("/nonexistent/file.jsonl")
        assert points == []

    def test_extract_from_empty_file(self, tmp_path):
        """Test extracting from empty file."""
        transcript_file = tmp_path / "empty.jsonl"
        transcript_file.write_text("")
        points = extract_points(str(transcript_file))
        assert points == []

    def test_extract_with_malformed_json(self, tmp_path):
        """Test extracting handles malformed JSON gracefully."""
        transcript_file = tmp_path / "malformed.jsonl"
        transcript_file.write_text("not json\n{\"valid\": true}")
        # Should not raise, just skip bad lines
        points = extract_points(str(transcript_file))
        # May or may not have points, but should not crash
        assert isinstance(points, list)

    def test_max_points_limit(self, tmp_path):
        """Test that points are limited to 3."""
        transcript_file = tmp_path / "session.jsonl"
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "I created file1. I fixed bug1. I implemented feature1. I added test1. I updated docs1."},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/a.py"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/b.py"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/c.py"}},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/d.py"}},
            ]}},
        ]
        transcript_file.write_text("\n".join(json.dumps(l) for l in lines))

        points = extract_points(str(transcript_file))
        assert len(points) <= 3


class TestUpdateMemoryFromTranscript:
    """Tests for update_memory_from_transcript function."""

    def test_full_workflow(self, tmp_path):
        """Test the full workflow from transcript to memory update."""
        # Create transcript
        transcript_file = tmp_path / "session.jsonl"
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "I implemented the authentication module."},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/src/auth.py"}},
            ]}},
        ]
        transcript_file.write_text("\n".join(json.dumps(l) for l in lines))

        # Create memory file location
        memory_file = tmp_path / "memory.md"

        # Run the full workflow
        result = update_memory_from_transcript(str(transcript_file), "myproject", memory_file)
        assert result is True

        # Verify memory was updated
        assert memory_file.exists()
        content = memory_file.read_text()
        assert "## myproject" in content

    def test_preserves_other_projects(self, tmp_path):
        """Test that updating one project preserves others."""
        # Create existing memory
        memory_file = tmp_path / "memory.md"
        memory_file.write_text("""# Memory

## other_project
- [2026-02-01] Some other work
""")

        # Create transcript
        transcript_file = tmp_path / "session.jsonl"
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "I added a new feature."},
            ]}},
        ]
        transcript_file.write_text("\n".join(json.dumps(l) for l in lines))

        # Run update
        result = update_memory_from_transcript(str(transcript_file), "newproject", memory_file)
        assert result is True

        # Verify both projects exist
        content = memory_file.read_text()
        assert "## other_project" in content
        assert "## newproject" in content


class TestEntryLengthLimit:
    """Tests for entry length limits."""

    def test_long_entry_truncated(self, tmp_path):
        """Test that long entries are truncated."""
        memory_file = tmp_path / "memory.md"
        long_point = "A" * 100  # Longer than MAX_ENTRY_LENGTH
        result = update_memory("myproject", [long_point], memory_file)
        assert result is True

        content = memory_file.read_text()
        # Entry should be truncated
        # The format is "- [date] point", so we need to find the actual entry
        lines = content.split("\n")
        entry_line = [l for l in lines if l.startswith("- [")][0]
        # Remove the "- [date] " prefix (13 chars like "- [2026-02-03] ")
        entry_content = entry_line.split("] ", 1)[1]
        assert len(entry_content) <= MAX_ENTRY_LENGTH
