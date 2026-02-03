#!/usr/bin/env python3
"""
Nexus Memory Update - Extract key points from transcript and update memory.md.

This module extracts important points from a transcript JSONL file using
rule-based extraction (no LLM calls) and updates the global memory.md file.

Memory file location: ~/.nexus/memory.md

Format:
```
# Memory

## project_name
- [2026-02-03] Brief description of what was done
- [2026-02-02] Another action

## another_project
- [2026-02-01] Something else
```

Rules:
- Each project keeps at most 5 entries
- Each entry is at most 50 characters
- Entries are sorted newest first
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def log(message: str) -> None:
    """Log message to stderr for debugging."""
    print(f"[memory_update] {message}", file=sys.stderr)


# Keywords that indicate important actions
ACTION_KEYWORDS = [
    "created",
    "fixed",
    "implemented",
    "added",
    "updated",
    "refactored",
    "removed",
    "deleted",
    "resolved",
    "completed",
    "built",
    "configured",
    "integrated",
    "migrated",
    "optimized",
]

# Maximum entries per project
MAX_ENTRIES_PER_PROJECT = 5

# Maximum characters per entry
MAX_ENTRY_LENGTH = 50


def extract_file_changes(transcript_lines: list[dict]) -> list[str]:
    """Extract file paths from Write/Edit tool calls."""
    files_changed = set()

    for line in transcript_lines:
        # Look for tool_use in content
        if line.get("type") == "assistant":
            content = line.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})

                        if tool_name in ("Write", "Edit"):
                            file_path = tool_input.get("file_path", "")
                            if file_path:
                                # Extract just the filename for brevity
                                filename = Path(file_path).name
                                files_changed.add(filename)

    return list(files_changed)


def extract_action_phrases(transcript_lines: list[dict]) -> list[str]:
    """Extract action phrases from assistant messages."""
    actions = []

    for line in transcript_lines:
        if line.get("type") == "assistant":
            content = line.get("message", {}).get("content", [])

            # Handle text content
            text_blocks = []
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_blocks.append(block.get("text", ""))
            elif isinstance(content, str):
                text_blocks.append(content)

            for text in text_blocks:
                # Look for sentences containing action keywords
                for keyword in ACTION_KEYWORDS:
                    # Case-insensitive search for keyword
                    pattern = rf"(?i)\b{keyword}\b[^.!?\n]{{0,100}}"
                    matches = re.findall(pattern, text)
                    for match in matches:
                        # Clean up and truncate
                        action = match.strip()
                        if len(action) > 10:  # Filter out very short matches
                            actions.append(action)

    return actions


def summarize_changes(files: list[str], actions: list[str]) -> list[str]:
    """Combine file changes and actions into summary points."""
    points = []

    # Add file-based summaries
    if files:
        # Group common file types
        py_files = [f for f in files if f.endswith(".py")]
        md_files = [f for f in files if f.endswith(".md")]
        other_files = [f for f in files if not f.endswith(".py") and not f.endswith(".md")]

        if py_files:
            if len(py_files) <= 2:
                points.append(f"Modified {', '.join(py_files)}")
            else:
                points.append(f"Modified {len(py_files)} Python files")

        if md_files:
            if len(md_files) <= 2:
                points.append(f"Updated {', '.join(md_files)}")
            else:
                points.append(f"Updated {len(md_files)} markdown files")

        if other_files:
            if len(other_files) <= 2:
                points.append(f"Changed {', '.join(other_files)}")
            else:
                points.append(f"Changed {len(other_files)} other files")

    # Add action-based summaries (take unique, most informative ones)
    seen_keywords = set()
    for action in actions:
        # Find which keyword triggered this
        for keyword in ACTION_KEYWORDS:
            if keyword.lower() in action.lower() and keyword not in seen_keywords:
                seen_keywords.add(keyword)
                # Truncate to max length
                truncated = action[:MAX_ENTRY_LENGTH]
                if len(action) > MAX_ENTRY_LENGTH:
                    truncated = truncated.rsplit(" ", 1)[0] + "..."
                points.append(truncated)
                break

        if len(points) >= 3:  # Limit to 3 action-based points
            break

    return points


def extract_points(transcript_path: str) -> list[str]:
    """
    Extract key points from transcript JSONL file.

    Args:
        transcript_path: Path to the JSONL transcript file

    Returns:
        List of summary points (max 3)
    """
    points = []

    try:
        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            log(f"Transcript file not found: {transcript_path}")
            return points

        # Read JSONL file
        lines = []
        with open(transcript_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines

        if not lines:
            log("No valid JSON lines found in transcript")
            return points

        # Extract information
        files_changed = extract_file_changes(lines)
        actions = extract_action_phrases(lines)

        # Summarize
        points = summarize_changes(files_changed, actions)

        # Limit to 3 points
        points = points[:3]

        # Ensure each point is within length limit
        points = [p[:MAX_ENTRY_LENGTH] for p in points]

    except Exception as e:
        log(f"Error extracting points: {e}")

    return points


def parse_memory_file(memory_path: Path) -> dict[str, list[str]]:
    """
    Parse memory.md file into a dictionary.

    Returns:
        Dict mapping project name to list of entries
    """
    memory = {}

    if not memory_path.exists():
        return memory

    try:
        content = memory_path.read_text(encoding="utf-8")
        current_project = None

        for line in content.split("\n"):
            line = line.strip()

            # Check for project header (## project_name)
            if line.startswith("## "):
                current_project = line[3:].strip()
                if current_project not in memory:
                    memory[current_project] = []

            # Check for entry (- [date] text)
            elif line.startswith("- ") and current_project:
                memory[current_project].append(line)

    except Exception as e:
        log(f"Error parsing memory file: {e}")

    return memory


def format_memory_file(memory: dict[str, list[str]]) -> str:
    """Format memory dictionary back to markdown."""
    lines = ["# Memory", ""]

    for project in sorted(memory.keys()):
        entries = memory[project]
        if entries:  # Only include projects with entries
            lines.append(f"## {project}")
            for entry in entries:
                lines.append(entry)
            lines.append("")

    return "\n".join(lines)


def update_memory(project_name: str, new_points: list[str], memory_path: Optional[Path] = None) -> bool:
    """
    Update memory.md with new points for a project.

    Args:
        project_name: Name of the project
        new_points: List of new summary points
        memory_path: Optional custom path for memory file (for testing)

    Returns:
        True if successful, False otherwise
    """
    if not new_points:
        log("No points to add, skipping memory update")
        return True

    if memory_path is None:
        memory_path = Path.home() / ".nexus" / "memory.md"

    try:
        # Ensure parent directory exists
        memory_path.parent.mkdir(parents=True, exist_ok=True)

        # Parse existing memory
        memory = parse_memory_file(memory_path)

        # Get or create project entries
        if project_name not in memory:
            memory[project_name] = []

        # Format new entries with date, truncating points to max length
        today = datetime.now().strftime("%Y-%m-%d")
        new_entries = [f"- [{today}] {point[:MAX_ENTRY_LENGTH]}" for point in new_points]

        # Insert new entries at the top
        memory[project_name] = new_entries + memory[project_name]

        # Truncate to max entries
        memory[project_name] = memory[project_name][:MAX_ENTRIES_PER_PROJECT]

        # Write back
        content = format_memory_file(memory)
        memory_path.write_text(content, encoding="utf-8")

        log(f"Updated memory for {project_name} with {len(new_points)} new points")
        return True

    except Exception as e:
        log(f"Error updating memory: {e}")
        return False


def update_memory_from_transcript(transcript_path: str, project_name: str, memory_path: Optional[Path] = None) -> bool:
    """
    Main entry point: extract points from transcript and update memory.

    Args:
        transcript_path: Path to the JSONL transcript file
        project_name: Name of the project
        memory_path: Optional custom path for memory file (for testing)

    Returns:
        True if successful, False otherwise
    """
    log(f"Processing transcript for project: {project_name}")

    # Extract points
    points = extract_points(transcript_path)

    if not points:
        log("No significant points extracted from transcript")
        return True

    log(f"Extracted {len(points)} points: {points}")

    # Update memory
    return update_memory(project_name, points, memory_path)


if __name__ == "__main__":
    # Can be run standalone for testing
    if len(sys.argv) >= 3:
        transcript = sys.argv[1]
        project = sys.argv[2]
        success = update_memory_from_transcript(transcript, project)
        sys.exit(0 if success else 1)
    else:
        print("Usage: python memory_update.py <transcript_path> <project_name>", file=sys.stderr)
        sys.exit(1)
