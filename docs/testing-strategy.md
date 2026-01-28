# Nexus Testing Strategy

> **Version**: 1.0
> **Date**: 2026-01-28
> **Status**: Proposed

## Summary

This document defines a comprehensive, automatable testing strategy for the Nexus multi-agent framework. The strategy is organized into layers, prioritizing tests that can run without Claude API access while maximizing coverage of critical functionality.

## Design

### Architecture Overview

```
                    Testing Pyramid

                         /\
                        /  \
                       / E2E \        <- Manual/Optional (needs Claude API)
                      /________\
                     /          \
                    / Integration \   <- Mock-based agent tests
                   /______________\
                  /                \
                 /   Unit Tests     \  <- Python modules
                /____________________\
               /                      \
              /    Static Analysis     \ <- No runtime needed
             /_________________________\
            /                            \
           /     Installation Tests       \ <- Bash/shell validation
          /________________________________\
```

### Core Components

1. **Static Analysis Layer**: Validates files without execution
2. **Installation Test Layer**: Validates install.sh and file structure
3. **Unit Test Layer**: Tests Python runtime modules
4. **Integration Test Layer**: Tests agent interactions with mocks
5. **E2E Test Layer** (Optional): Manual testing with real Claude API

### Data Flow

```
Source Files (nexus-dist/, runtime/)
        |
        v
[Static Analysis] --> Errors detected early (paths, names, syntax)
        |
        v
[Installation Test] --> Validates install.sh creates correct structure
        |
        v
[Unit Tests] --> Validates Python module logic
        |
        v
[Integration Tests] --> Validates agent prompt format, tool permissions
        |
        v
[Manual E2E] --> Validates end-to-end with real Claude API
```

## Decisions

### Decision 1: Layered Testing Approach
- **Decision**: Implement 5-layer testing pyramid
- **Rationale**:
  - Lower layers catch issues cheaply and quickly
  - Higher layers provide confidence but at higher cost
  - Claude API tests are optional due to cost/reliability concerns
- **Alternatives Considered**:
  - Full E2E only: Too expensive, flaky
  - Static only: Insufficient coverage
- **Risks**: Integration tests with mocks may not catch real API issues

### Decision 2: "wukong" Remnant Detection as First Priority
- **Decision**: Add automated detection of "wukong" references in Nexus codebase
- **Rationale**:
  - Found 50+ occurrences of "wukong" in Nexus codebase
  - This is a high-impact, easy-to-automate check
  - Prevents confusion and incorrect behavior
- **Evidence**: `grep -r "wukong" /Users/wangqing/sourcecode/agent/nexus` returns many matches

### Decision 3: pytest as Test Framework
- **Decision**: Use pytest for all Python tests
- **Rationale**:
  - Industry standard, well-documented
  - Compatible with existing wukong tests
  - Good fixtures and parameterization support
- **Alternatives Considered**: unittest (used in some wukong tests), but pytest is more ergonomic

### Decision 4: shellcheck for Shell Script Validation
- **Decision**: Use shellcheck for install.sh validation
- **Rationale**:
  - Catches common shell scripting errors
  - Already used in wukong CI
  - Prevents portability issues
- **Evidence**: wukong's `ci-check.sh` uses shellcheck successfully

## Test Layers Detail

### Layer 1: Static Analysis (No Runtime)

**Purpose**: Catch structural and naming errors without executing code.

**Tests**:

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| S001 | Path Reference Validation | Check all path references in .md files exist | P0 |
| S002 | No Wukong Remnants | Detect "wukong" strings in source files | P0 |
| S003 | AGENTS.md Format | Validate AGENTS.md follows Claude Code spec | P0 |
| S004 | Agent Definition Format | Validate agent .md files have required frontmatter | P1 |
| S005 | Markdown Syntax | Basic markdown lint (optional) | P2 |
| S006 | Python Syntax Check | `py_compile` all .py files | P0 |
| S007 | JSON Syntax Check | Validate any .json files parse correctly | P1 |
| S008 | Path Consistency | `~/.nexus/` vs `~/.claude/` usage is correct | P0 |

**Implementation**:

```python
# tests/test_static.py

def test_no_wukong_remnants():
    """Ensure no wukong references remain in nexus codebase."""
    # Scan all source files for "wukong" (case insensitive)
    # Allowed exceptions: comments explaining migration, changelogs

def test_path_references_exist():
    """Ensure paths referenced in markdown files exist."""
    # Similar to wukong's test_path_references.py

def test_agents_md_format():
    """Validate AGENTS.md follows Claude Code specification."""
    # Must have: agent table, subagent_type column, tool permissions

def test_agent_definition_frontmatter():
    """Each agent .md must have valid YAML frontmatter."""
    # Required: name, description, tools, disallowedTools, model

def test_path_mapping_consistency():
    """Validate path usage follows convention."""
    # ~/.claude/ for Claude Code config (rules, agents, skills, commands)
    # ~/.nexus/ for runtime data (hooks, context, runtime)
```

### Layer 2: Installation Tests

**Purpose**: Validate install.sh works correctly.

**Tests**:

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| I001 | Shell Lint | shellcheck install.sh | P0 |
| I002 | Install to Temp Dir | Run install.sh to temp directory | P0 |
| I003 | Required Files Created | Verify key files exist after install | P0 |
| I004 | Uninstall Works | Test --uninstall removes correct files | P1 |
| I005 | Clean Install | Test --clean removes old version | P1 |
| I006 | Idempotent Install | Run install twice, no errors | P1 |

**Implementation**:

```bash
# scripts/ci-check.sh

# Shell lint
shellcheck install.sh

# Installation test
TEMP_DIR=$(mktemp -d)
./install.sh "$TEMP_DIR" --force <<< "y"

# Verify structure
test -f "$TEMP_DIR/.claude/rules/00-nexus-core.md"
test -d "$TEMP_DIR/.claude/agents"
test -f "$TEMP_DIR/.claude/agents/explorer.md"
test -d "$TEMP_DIR/.nexus/runtime"
```

### Layer 3: Unit Tests (Python)

**Purpose**: Test Python runtime module logic.

**Modules to Test**:

| Module | Location | Key Functions | Priority |
|--------|----------|---------------|----------|
| state_manager | runtime/ | RuntimeState, StateManager | P0 |
| event_bus | runtime/ | Event, EventBus | P0 |
| scheduler | runtime/ | Scheduler, graph operations | P0 |
| metrics | runtime/ | MetricsCollector, cost calculation | P1 |
| anchor_manager | runtime/ | AnchorManager | P1 |
| aggregator | nexus-dist/context/ | ResultAggregator | P1 |
| importance | nexus-dist/context/ | compress_by_importance | P1 |
| snapshot | nexus-dist/context/ | ContextSnapshot | P2 |

**Implementation** (adapt from wukong's test_runtime.py):

```python
# tests/test_runtime.py

class TestStateManager(unittest.TestCase):
    def test_atomic_write(self):
        """Test atomic file write prevents corruption."""

    def test_start_graph(self):
        """Test starting a task graph."""

    def test_node_lifecycle(self):
        """Test node state transitions: pending -> active -> completed."""

class TestEventBus(unittest.TestCase):
    def test_write_event(self):
        """Test writing events to JSONL file."""

    def test_read_events_with_filters(self):
        """Test reading events with type/node/graph filters."""

class TestScheduler(unittest.TestCase):
    def test_topological_sort(self):
        """Test DAG nodes are sorted correctly."""

    def test_get_ready_nodes(self):
        """Test identifying nodes ready for execution."""
```

### Layer 4: Integration Tests (Mock-based)

**Purpose**: Test agent interactions without real Claude API.

**Tests**:

| Test ID | Test Name | Description | Priority |
|---------|-----------|-------------|----------|
| G001 | Agent Prompt Format | Validate agent prompts are well-formed | P0 |
| G002 | Tool Permission Enforcement | Validate allowed_tools matches agent definition | P0 |
| G003 | Agent Output Contract | Validate expected output structure | P1 |
| G004 | Track Execution Flow | Validate DAG flow for each track type | P1 |
| G005 | Parallel Execution | Validate concurrent agent handling | P2 |

**Implementation**:

```python
# tests/test_integration.py

class TestAgentPromptFormat(unittest.TestCase):
    def test_explorer_prompt_has_required_sections(self):
        """Explorer agent definition has required sections."""
        agent_file = Path("~/.claude/agents/explorer.md").expanduser()
        content = agent_file.read_text()

        # Must have frontmatter
        assert content.startswith("---")

        # Must have tool permissions section
        assert "Tool Permissions" in content or "Tool Allowlist" in content

        # Must have output contract
        assert "Output" in content

    def test_agent_tool_permissions_match_agents_md(self):
        """Agent definition tools match AGENTS.md table."""
        # Parse AGENTS.md for declared tools
        # Compare with each agent's frontmatter

class TestTrackExecution(unittest.TestCase):
    def test_feature_track_dag(self):
        """Feature track follows: analyst+explorer -> architect -> implementer -> tester+reviewer."""
        # Create scheduler, load feature template
        # Verify topological order and parallelization
```

### Layer 5: E2E Tests (Optional, Manual)

**Purpose**: Validate real Claude Code integration.

**Tests** (manual checklist):

| Test ID | Test Name | Description |
|---------|-----------|-------------|
| E001 | /nexus Command | Run /nexus, verify activation |
| E002 | Agent Invocation | Verify Task() invokes correct agent |
| E003 | Background Agent | Verify run_in_background=True works |
| E004 | Agent Output | Verify agent returns structured output |
| E005 | Track Completion | Complete a full track (e.g., fix) |

## Test Tools and Libraries

| Tool | Purpose | Installation |
|------|---------|--------------|
| pytest | Test framework | `pip install pytest` |
| shellcheck | Shell lint | `brew install shellcheck` (macOS) |
| py_compile | Python syntax | Built-in |
| pyyaml | YAML parsing | `pip install pyyaml` (for frontmatter) |

## CI/CD Integration

### CI Script (scripts/ci-check.sh)

```bash
#!/bin/bash
set -e

echo "=== Nexus CI Check ==="

# 1. Shell Lint
echo "[1/4] Shell Lint"
shellcheck install.sh

# 2. Python Syntax
echo "[2/4] Python Syntax"
find . -name "*.py" -not -path "./.git/*" -exec python3 -m py_compile {} \;

# 3. Static Tests
echo "[3/4] Static Tests"
python3 -m pytest tests/test_static.py -v

# 4. Unit Tests
echo "[4/4] Unit Tests"
python3 -m pytest tests/test_runtime.py tests/test_context.py -v

# 5. Installation Test (optional)
if [ "$1" != "--quick" ]; then
    echo "[5/5] Installation Test"
    TEMP_DIR=$(mktemp -d)
    ./install.sh "$TEMP_DIR" --force <<< "y"
    test -f "$TEMP_DIR/.claude/rules/00-nexus-core.md"
    rm -rf "$TEMP_DIR"
fi

echo "=== All checks passed ==="
```

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pyyaml
          sudo apt-get install -y shellcheck

      - name: Run CI checks
        run: ./scripts/ci-check.sh
```

## Implementation Priority

### Phase 1: Critical (Week 1)
- [ ] S002: No Wukong Remnants test
- [ ] S001: Path Reference Validation
- [ ] S006: Python Syntax Check
- [ ] I001: Shell Lint
- [ ] I002: Install to Temp Dir

### Phase 2: Important (Week 2)
- [ ] S003: AGENTS.md Format
- [ ] S004: Agent Definition Format
- [ ] S008: Path Consistency
- [ ] Adapt wukong's test_runtime.py for Nexus
- [ ] Adapt wukong's test_context.py for Nexus

### Phase 3: Nice-to-Have (Week 3+)
- [ ] G001-G005: Integration tests
- [ ] I004-I006: Additional install tests
- [ ] S005, S007: Optional linting

## Tradeoffs

1. **Coverage vs Speed**: Chose to skip real Claude API tests in CI. Tradeoff: Faster CI, but some integration issues may slip through. Mitigation: Manual E2E testing before releases.

2. **Mock Accuracy vs Simplicity**: Integration tests use simplified mocks rather than realistic Claude responses. Tradeoff: Tests may pass when real integration would fail. Mitigation: Focus mocks on structure validation, not content.

3. **Test Maintenance vs Thoroughness**: Agent output contract tests require updating when agent definitions change. Tradeoff: More maintenance burden. Mitigation: Keep contract tests focused on structure, not specific content.

## Constraints

- **Technical Constraints**:
  - No Claude API access in CI (cost, reliability)
  - Python 3.8+ compatibility required
  - Cross-platform support (macOS, Linux)

- **Business Constraints**:
  - Must not increase PR merge time significantly (< 5 min)
  - Tests must be deterministic (no flaky tests)

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Mock tests don't catch real API issues | Medium | High | Manual E2E before releases |
| Tests become outdated as agents evolve | Medium | Medium | Regular test review, contract-based tests |
| CI becomes slow with full test suite | Low | Medium | Parallel test execution, --quick mode |
| Shell portability issues | Low | Low | Test on both macOS and Linux in CI |

## Evidence

- **Sources**:
  - `/Users/wangqing/sourcecode/agent/wukong/tests/test_path_references.py` - Path validation pattern
  - `/Users/wangqing/sourcecode/agent/wukong/scripts/ci-check.sh` - CI script structure
  - `/Users/wangqing/sourcecode/agent/wukong/tests/test_runtime.py` - Runtime test patterns
  - `/Users/wangqing/sourcecode/agent/nexus/AGENTS.md` - Agent definitions
  - `/Users/wangqing/sourcecode/agent/nexus/install.sh` - Installation script

- **Assumptions**:
  - pytest is acceptable as test framework (no explicit requirement stated)
  - GitHub Actions will be used for CI (standard assumption)
  - "wukong" remnants are bugs to be fixed, not intentional references

## Test Case Inventory

### Static Tests (test_static.py)

```python
# Test: S002 - No Wukong Remnants
# Files to scan: all .md, .py files in nexus-dist/ and runtime/
# Exceptions:
#   - docs/migration-from-wukong.md (if exists)
#   - CHANGELOG.md (history references)

# Test: S001 - Path Reference Validation
# Path mappings:
#   ~/.claude/skills/ -> nexus-dist/protocol/, reflection/, parallel/
#   ~/.claude/rules/ -> nexus-dist/rules/
#   ~/.claude/agents/ -> nexus-dist/agents/
#   ~/.claude/commands/ -> nexus-dist/commands/
#   ~/.nexus/context/ -> nexus-dist/context/
#   ~/.nexus/hooks/ -> nexus-dist/hooks/
#   ~/.nexus/runtime/ -> runtime/

# Test: S003 - AGENTS.md Format
# Required sections:
#   - Available Agents table with: Agent, Alias, Model, Cost, Background, Purpose
#   - Agent Boundaries table with: CAN DO, CANNOT DO
#   - Tracks table

# Test: S004 - Agent Definition Format
# Required frontmatter fields:
#   - name: string
#   - description: string
#   - tools: comma-separated list
#   - disallowedTools: comma-separated list
#   - model: sonnet | opus | haiku

# Test: S008 - Path Consistency
# Correct patterns:
#   ~/.claude/ for: rules/, agents/, skills/, commands/
#   ~/.nexus/ for: hooks/, context/, runtime/, notepads/, plans/
# Wrong patterns to detect:
#   ~/.nexus/skills/ (should be ~/.claude/skills/)
#   ~/.nexus/rules/ (should be ~/.claude/rules/)
#   ~/.claude/hooks/ (should be ~/.nexus/hooks/)
```

### Installation Tests (test_install.sh)

```bash
# Test: I002 - Install to Temp Dir
# Expected files after install:
#   $TEMP/.claude/rules/00-nexus-core.md
#   $TEMP/.claude/agents/explorer.md
#   $TEMP/.claude/agents/implementer.md
#   $TEMP/.claude/agents/architect.md
#   $TEMP/.claude/agents/reviewer.md
#   $TEMP/.claude/agents/tester.md
#   $TEMP/.claude/agents/analyst.md
#   $TEMP/.claude/agents/planner.md
#   $TEMP/.claude/commands/nexus.md
#   $TEMP/.claude/commands/plan.md
#   $TEMP/.claude/skills/protocol/agent-protocol.md
#   $TEMP/.nexus/runtime/*.py
#   $TEMP/.nexus/hooks/*.py
#   $TEMP/.nexus/context/*.py

# Test: I003 - Required Files Created
# Count checks:
#   7 agent files in ~/.claude/agents/
#   3+ command files in ~/.claude/commands/
#   3+ skill directories in ~/.claude/skills/
```

### Unit Tests (test_runtime.py, test_context.py)

See wukong's existing tests as template. Key adaptations:
- Change `wukong-dist` to `nexus-dist` in path setup
- Change `.wukong` to `.nexus` in default paths
- Update role names if different (eye->explorer, body->implementer, etc.)

## Next Steps

1. **Immediate**: Create `tests/` directory structure
2. **Week 1**: Implement P0 static tests (S001, S002, S006)
3. **Week 1**: Implement CI script (ci-check.sh)
4. **Week 2**: Adapt runtime tests from wukong
5. **Week 2**: Set up GitHub Actions workflow
6. **Week 3+**: Add integration tests as needed

## Appendix: Wukong Remnant Locations

The following files contain "wukong" references that need to be updated:

```
nexus-dist/hooks/on_stop.py (2 occurrences)
nexus-dist/hooks/reflection-extract.py (18+ occurrences)
nexus-dist/context/example_usage.py (2 occurrences)
runtime/metrics.py (3 occurrences)
runtime/visualizer.py (4 occurrences)
runtime/artifact_manager.py (1 occurrence)
runtime/anchor_manager.py (1 occurrence)
runtime/state_manager.py (1 occurrence)
runtime/scheduler.py (1 occurrence)
runtime/selfcheck.py (10+ occurrences)
runtime/__init__.py (1 occurrence)
runtime/cli.py (8+ occurrences)
runtime/event_bus.py (1 occurrence)
```

These should be renamed to use "nexus" consistently.
