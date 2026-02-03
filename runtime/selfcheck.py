#!/usr/bin/env python3
"""
Nexus Self-Check - Environment validation for Nexus

Usage:
    python3 ~/.nexus/runtime/selfcheck.py

This script validates the Nexus installation and configuration.
"""

import os
import sys
from pathlib import Path
from typing import Tuple, List


# Status icons
ICON_OK = "\u2713"      # checkmark
ICON_FAIL = "\u2717"    # X mark
ICON_WARN = "\u26a0"    # warning


def get_home() -> Path:
    """Get user home directory (cross-platform)."""
    return Path.home()


def get_nexus_dir() -> Path:
    """Get Nexus runtime directory."""
    return get_home() / ".nexus"


def get_claude_dir() -> Path:
    """Get Claude configuration directory."""
    return get_home() / ".claude"


def count_files(directory: Path, pattern: str = "*.md") -> int:
    """Count files matching pattern in directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def check_files_exist(directory: Path, filenames: List[str]) -> Tuple[int, int]:
    """
    Check which files exist in a directory.

    Returns:
        Tuple of (found_count, missing_count)
    """
    found = 0
    missing = 0
    for filename in filenames:
        if (directory / filename).exists():
            found += 1
        else:
            missing += 1
    return found, missing


def print_header() -> None:
    """Print the self-check header."""
    print("=" * 45)
    print(" Nexus Self-Check")
    print("=" * 45)
    print()


def print_footer() -> None:
    """Print the self-check footer."""
    print()
    print("=" * 45)
    print(" Self-Check Complete")
    print("=" * 45)


def check_rules() -> bool:
    """Check rule files."""
    print("1. Rules (~/.claude/rules/)")
    cwd = Path.cwd()

    # Check project-level first
    project_rules = count_files(cwd / ".claude" / "rules")
    if project_rules > 0:
        print(f"   {ICON_OK} Found {project_rules} rule files (project)")
        return True

    # Check global
    global_rules = count_files(get_claude_dir() / "rules")
    if global_rules > 0:
        print(f"   {ICON_OK} Found {global_rules} rule files (global)")
        return True

    print(f"   {ICON_FAIL} No rule files found (run install.sh)")
    return False


def check_agents() -> bool:
    """Check agent files."""
    print()
    print("2. Agents (~/.claude/agents/)")

    agents_dir = get_claude_dir() / "agents"
    agent_files = ["eye.md", "body.md", "mind.md"]

    found, missing = check_files_exist(agents_dir, agent_files)
    total = found + missing

    if missing == 0:
        print(f"   {ICON_OK} All {found} agents present")
        return True
    else:
        print(f"   {ICON_WARN} {found}/{total} agents present")
        for agent in agent_files:
            if not (agents_dir / agent).exists():
                print(f"      Missing: {agent}")
        return False


def check_commands() -> bool:
    """Check command files."""
    print()
    print("3. Commands (~/.claude/commands/)")

    commands_dir = get_claude_dir() / "commands"
    command_files = ["nexus.md"]

    found, missing = check_files_exist(commands_dir, command_files)
    total = found + missing

    if missing == 0:
        print(f"   {ICON_OK} All {found} commands present")
        return True
    else:
        print(f"   {ICON_WARN} {found}/{total} commands present")
        return False


def main() -> int:
    """
    Run all self-checks.

    Returns:
        0 if all checks pass, 1 if any critical check fails
    """
    print_header()

    results = []

    # Run all checks
    results.append(("Rules", check_rules()))
    results.append(("Agents", check_agents()))
    results.append(("Commands", check_commands()))

    print_footer()

    # Critical checks: Rules and Agents
    critical_checks = ["Rules", "Agents"]
    critical_failed = any(
        not passed for name, passed in results if name in critical_checks
    )

    return 1 if critical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
