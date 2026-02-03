#!/usr/bin/env python3
"""
Nexus PreCompact Hook - Save full context before compaction.

This hook is triggered before Claude Code compacts the conversation.
It copies the full transcript to a timestamped backup location.

Usage in ~/.claude/settings.json:
{
  "hooks": {
    "PreCompact": [{
      "matcher": "auto",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.nexus/hooks/precompact_save.py"
      }]
    }]
  }
}

Input (stdin):
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/DennisWang/SourceCode/ai-coding/nexus",
  "hook_event_name": "PreCompact",
  "trigger": "auto"
}

Output:
Saves transcript to ~/.nexus/context/{project_name}/{timestamp}_{session_id}.jsonl
Also updates ~/.nexus/memory.md with key points from the transcript.
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Import memory update function (same directory)
try:
    from memory_update import update_memory_from_transcript
    MEMORY_UPDATE_AVAILABLE = True
except ImportError:
    MEMORY_UPDATE_AVAILABLE = False


def log(message: str) -> None:
    """Log message to stderr for debugging."""
    print(f"[precompact_save] {message}", file=sys.stderr)


def get_project_name(cwd: str) -> str:
    """Extract project name from working directory (last path component)."""
    path = Path(cwd)
    return path.name or "unknown"


def generate_filename(session_id: str) -> str:
    """Generate unique filename with timestamp and session_id."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use first 8 chars of session_id for brevity
    short_id = session_id[:8] if len(session_id) > 8 else session_id
    return f"{timestamp}_{short_id}.jsonl"


def main() -> int:
    """Main entry point."""
    try:
        # 1. Read hook data from stdin
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            log("ERROR: No input received from stdin")
            return 1

        try:
            hook_data = json.loads(raw_input)
        except json.JSONDecodeError as e:
            log(f"ERROR: Failed to parse JSON input: {e}")
            return 1

        # 2. Extract required fields
        session_id = hook_data.get("session_id", "")
        transcript_path = hook_data.get("transcript_path", "")
        cwd = hook_data.get("cwd", "")

        if not session_id:
            log("ERROR: Missing session_id in hook data")
            return 1

        if not transcript_path:
            log("ERROR: Missing transcript_path in hook data")
            return 1

        if not cwd:
            log("ERROR: Missing cwd in hook data")
            return 1

        # 3. Validate source file exists
        source_path = Path(transcript_path)
        if not source_path.exists():
            log(f"ERROR: Transcript file not found: {transcript_path}")
            return 1

        # 4. Build destination path
        project_name = get_project_name(cwd)
        filename = generate_filename(session_id)

        context_dir = Path.home() / ".nexus" / "context" / project_name
        dest_path = context_dir / filename

        # 5. Create directory if needed
        context_dir.mkdir(parents=True, exist_ok=True)

        # 6. Copy transcript file
        shutil.copy2(source_path, dest_path)

        # 7. Log success
        log(f"Saved context: {dest_path}")
        log(f"  Source: {transcript_path}")
        log(f"  Size: {dest_path.stat().st_size} bytes")

        # 8. Update memory.md with key points from transcript
        if MEMORY_UPDATE_AVAILABLE:
            try:
                update_memory_from_transcript(transcript_path, project_name)
                log("Memory update completed")
            except Exception as e:
                # Memory update failure should not fail the main hook
                log(f"WARNING: Memory update failed: {e}")
        else:
            log("WARNING: memory_update module not available, skipping memory update")

        return 0

    except Exception as e:
        log(f"ERROR: Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
