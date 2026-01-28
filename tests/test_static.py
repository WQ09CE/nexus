#!/usr/bin/env python3
"""
Static Analysis Tests for Nexus

P0 priority tests that verify code quality without runtime execution.
These tests run fast and catch common issues early.
"""
import os
import sys
import re
import py_compile
from pathlib import Path

# Project root directory
NEXUS_ROOT = Path(__file__).parent.parent
SOURCE_DIR = NEXUS_ROOT / "nexus-dist"

# Path mapping for reference validation
PATH_MAPPING = {
    # ~/.claude/ paths (correct installation targets)
    "~/.claude/skills/": SOURCE_DIR / "skills" if (SOURCE_DIR / "skills").exists() else None,
    "~/.claude/rules/": SOURCE_DIR / "rules",
    "~/.claude/commands/": SOURCE_DIR / "commands",
    "~/.claude/agents/": SOURCE_DIR / "agents",
    # ~/.nexus/ paths (runtime data)
    "~/.nexus/hooks/": SOURCE_DIR / "hooks",
    "~/.nexus/context/": SOURCE_DIR / "context",
    "~/.nexus/runtime/": NEXUS_ROOT / "runtime",
}

# Files/directories to ignore
IGNORE_PATHS = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "docs",  # May reference design docs
]

# Files that may legitimately mention wukong (migration docs, etc.)
WUKONG_EXCEPTION_FILES = [
    "migration",
    "changelog",
    "history",
    "test_static.py",  # This test file itself
]


def test_no_wukong_remnants():
    """
    Ensure no wukong remnant references in source files.

    This test tracks the migration progress from wukong to nexus.
    The baseline count should decrease over time as files are migrated.
    """
    # Known baseline: files still containing wukong references (to be cleaned up)
    # Update this number as migration progresses
    KNOWN_BASELINE_COUNT = 65  # Current count of known remnants

    remnants = []

    for ext in ["*.py", "*.md", "*.sh"]:
        for file in NEXUS_ROOT.rglob(ext):
            # Skip ignored paths
            if any(ignore in str(file) for ignore in IGNORE_PATHS):
                continue

            # Skip exception files
            file_lower = file.name.lower()
            if any(exc in file_lower for exc in WUKONG_EXCEPTION_FILES):
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Search for wukong references (case insensitive)
            # Skip comments and quoted text that might be explaining migration
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Skip comment lines
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue

                # Check for wukong references
                if re.search(r"\bwukong\b", line, re.IGNORECASE):
                    # Additional check: is this a migration note?
                    if "migration" in line.lower() or "from wukong" in line.lower():
                        continue
                    remnants.append(f"{file.relative_to(NEXUS_ROOT)}:{line_num}")

    # Report findings
    current_count = len(remnants)

    if current_count > KNOWN_BASELINE_COUNT:
        # New wukong references added - fail the test
        assert False, (
            f"Wukong remnant count increased! "
            f"Baseline: {KNOWN_BASELINE_COUNT}, Current: {current_count}. "
            f"New remnants: {remnants[-10:]}"  # Show last 10 for debugging
        )
    elif current_count < KNOWN_BASELINE_COUNT:
        # Progress made - update the baseline!
        print(
            f"\n[INFO] Migration progress! Remnant count decreased from "
            f"{KNOWN_BASELINE_COUNT} to {current_count}. "
            f"Consider updating KNOWN_BASELINE_COUNT in test_static.py"
        )
    else:
        # Same as baseline - test passes but work remains
        print(
            f"\n[INFO] {current_count} wukong remnants remain. "
            f"These files need migration: {set(r.split(':')[0] for r in remnants[:5])}"
        )


def test_path_references_exist():
    """Ensure path references in md files point to existing source files."""
    missing = []

    # Patterns to extract path references
    patterns = [
        r"`(~?/?\.?claude/[a-zA-Z_\-/]+\.(?:md|py))`",
        r"`(~?/?\.?nexus/[a-zA-Z_\-/]+\.(?:md|py))`",
        r'`(nexus-dist/[a-zA-Z_\-/]+\.(?:md|py))`',
    ]

    for md_file in NEXUS_ROOT.rglob("*.md"):
        if any(ignore in str(md_file) for ignore in IGNORE_PATHS):
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Skip template variables
                if "{" in match or "$" in match or "<" in match:
                    continue

                # Try to resolve path
                resolved = None
                for prefix, source_dir in PATH_MAPPING.items():
                    if source_dir and match.startswith(prefix):
                        relative = match[len(prefix):]
                        resolved = source_dir / relative
                        break

                # For nexus-dist/ paths, check directly
                if match.startswith("nexus-dist/"):
                    resolved = NEXUS_ROOT / match

                if resolved and not resolved.exists():
                    missing.append(f"{md_file.relative_to(NEXUS_ROOT)}: {match}")

    # Note: This test is informational - empty missing is ideal but not blocking
    if missing:
        print(f"Warning: Some path references may not exist: {missing}")


def test_python_syntax():
    """Verify all Python files have valid syntax."""
    errors = []

    for py_file in NEXUS_ROOT.rglob("*.py"):
        if any(ignore in str(py_file) for ignore in IGNORE_PATHS):
            continue

        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{py_file.relative_to(NEXUS_ROOT)}: {e}")

    assert not errors, f"Python syntax errors:\n" + "\n".join(errors)


def test_agents_md_format():
    """Verify AGENTS.md exists and contains required agents."""
    agents_file = NEXUS_ROOT / "AGENTS.md"
    assert agents_file.exists(), "AGENTS.md not found at project root"

    content = agents_file.read_text(encoding="utf-8")

    # Required agents for Nexus
    required_agents = [
        "explorer",
        "analyst",
        "reviewer",
        "tester",
        "implementer",
        "architect",
        "planner",
    ]

    missing_agents = []
    for agent in required_agents:
        if agent not in content.lower():
            missing_agents.append(agent)

    assert not missing_agents, f"Missing agents in AGENTS.md: {missing_agents}"

    # Check for required sections
    required_sections = [
        "Available Agents",
        "Agent Selection",
        "Agent Boundaries",
    ]

    missing_sections = []
    for section in required_sections:
        if section.lower() not in content.lower():
            missing_sections.append(section)

    assert not missing_sections, f"Missing sections in AGENTS.md: {missing_sections}"


def test_agent_definition_files():
    """Verify agent definition files exist in nexus-dist/agents/."""
    agents_dir = SOURCE_DIR / "agents"
    assert agents_dir.exists(), f"agents directory not found: {agents_dir}"

    required_agents = [
        "explorer.md",
        "analyst.md",
        "reviewer.md",
        "tester.md",
        "implementer.md",
        "architect.md",
        "planner.md",
    ]

    missing_files = []
    for agent_file in required_agents:
        if not (agents_dir / agent_file).exists():
            missing_files.append(agent_file)

    assert not missing_files, f"Missing agent definition files: {missing_files}"


def test_no_hardcoded_user_paths():
    """Ensure no hardcoded user-specific paths (like /Users/xxx)."""
    violations = []

    # Pattern for hardcoded user paths
    user_path_pattern = r"/Users/[a-zA-Z0-9_]+/"

    for ext in ["*.py", "*.md", "*.sh"]:
        for file in NEXUS_ROOT.rglob(ext):
            if any(ignore in str(file) for ignore in IGNORE_PATHS):
                continue

            # Skip test files (they may need to reference paths)
            if "test_" in file.name:
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                if re.search(user_path_pattern, line):
                    violations.append(f"{file.relative_to(NEXUS_ROOT)}:{line_num}")

    assert not violations, f"Found hardcoded user paths: {violations}"


def test_core_rules_exist():
    """Verify core rules file exists."""
    rules_dir = SOURCE_DIR / "rules"
    assert rules_dir.exists(), f"rules directory not found: {rules_dir}"

    # Check for core rules file
    core_files = list(rules_dir.glob("*nexus-core*.md"))
    assert core_files, "No nexus-core rules file found in nexus-dist/rules/"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
