# Reflection Command

> **BLOCKING checklist** - Complete ALL steps before producing output.

## Trigger

```
/nexus reflection
```

## Pre-Check: Scope Confirmation (Prevent Anchoring Bias)

> **STOP** - Before introspection, confirm the scope first!

```
+-----------------------------------------------------------+
|  Q1. Does user mention "today/all/total/summary"?          |
|      today/all/total/summary                               |
|                                                            |
|      YES -> Cross-session introspection required           |
|      NO  -> Current session only                           |
+-----------------------------------------------------------+
```

**Anchoring Bias Triggers:**
| User Says | Wrong | Correct |
|-----------|-------|---------|
| "today all work" | Current session only | All sessions today |
| "all my projects" | Current project | All active projects |
| "summarize" | Current context | Confirm scope first |

---

## BLOCKING CHECKLIST (4 Steps)

> **Must complete ALL 4 steps. Skipping any step = Protocol Violation**

### Step 1: Read Session Index

```bash
# MUST execute - Use robust JSON reading to avoid parse errors
INDEX_FILE=~/.nexus/context/index.json
if [ -f "$INDEX_FILE" ] && [ -s "$INDEX_FILE" ]; then
    cat "$INDEX_FILE"
else
    echo "INDEX_NOT_EXIST_OR_EMPTY"
fi
```

**Expected data:**
- Session list with IDs and metadata
- Project associations
- Timestamps

**If file doesn't exist or empty:** Create empty introspection for current session only.

> **Pitfall [P001]**: Never pipe directly to JSON parser without checking file existence first. Empty input causes `JSONDecodeError`.

---

### Step 2: Read Relevant Sessions

> **Critical step - DO NOT SKIP**

```python
# Filter sessions by date (for "today" requests)
today = "YYYYMMDD"  # Current date
relevant_sessions = [s for s in index["sessions"] if today in s["id"]]

# Read EACH session's compact.md
for session in relevant_sessions:
    path = f"~/.nexus/context/sessions/{session['id']}/compact.md"
    # Read(path)
```

**Must collect from each session:**
- [ ] Project name
- [ ] Main tasks completed
- [ ] Key decisions made
- [ ] Issues encountered

**Checklist:**
```
[ ] Identified relevant sessions: ___
[ ] Read compact.md for EACH: [list files read]
[ ] No session skipped: [confirm]
```

---

### Step 2.5: Read Session Reflection Output

> **Critical step - DO NOT SKIP**

For each relevant session, read the full Reflection output (decisions, constraints, problems, interfaces):

```bash
# For each session directory from Step 2
REFLECTION_OUTPUT=~/.nexus/context/sessions/${SESSION_DIR}/reflection-output.json
if [ -f "$REFLECTION_OUTPUT" ]; then
    cat "$REFLECTION_OUTPUT"
fi
```

**Must extract from reflection-output.json:**
- [ ] decisions: Key decisions made
- [ ] constraints: Constraints discovered
- [ ] problems: Issues encountered
- [ ] interfaces: Important interfaces

**Checklist:**
```
[ ] Read reflection-output.json for EACH session: [list files read]
[ ] Extracted all decision/constraint/problem/interface entries
```

---

### Step 3: Read Existing Anchors

```bash
# MUST execute - Detect project name from git root or current directory
PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
PROJECT_ANCHORS=~/.nexus/context/anchors/projects/${PROJECT_NAME}.md

# Read project-specific anchors
if [ -f "$PROJECT_ANCHORS" ]; then
    echo "=== Project Anchors: $PROJECT_NAME ==="
    cat "$PROJECT_ANCHORS"
else
    echo "PROJECT_ANCHORS_NOT_EXIST: $PROJECT_ANCHORS"
fi
```

**Purpose:**
- Check for related existing anchors (project-level)
- Avoid duplicate entries
- Find patterns across sessions

**If files don't exist:** Note that no prior anchors exist for this scope.

---

### Step 4: Generate Introspection Output

**Only after completing Steps 1-3, produce the output.**

---

## Output Template

### Single Session Output

```markdown
## Introspection Report: {task_name}
**Session**: {session_id}
**Project**: {project_name}

### 1. Deviation Diagnosis
**Efficiency Loss**: {specific_description}
**Root Cause**: {analysis}

### 2. Rule Patch
```yaml
rule_patch:
  - action: add|tighten|loosen|remove
    target: "{rule_file}.md"
    rule: "{content}"
    reason: "{reason}"
```

### 3. Distillation
| ID | Type | Content | Threshold Met | Write? |
|----|------|---------|---------------|--------|
| D0xx | Decision | {decision} | Impact high | Y/N |
| P0xx | Pitfall | {pitfall} | Repeat >= 2 | Y/N |
```

### Cross-Session Output

```markdown
## Today's Work Introspection: {date}

### Session Overview
| Session | Project | Main Tasks | Key Decisions |
|---------|---------|------------|---------------|
| {id1} | {proj1} | {task1} | {decision1} |
| {id2} | {proj2} | {task2} | {decision2} |

### Cross-Session Patterns
- **Common patterns**: {patterns found}
- **Related issues**: {cross-session correlations}

### Per-Session Details

#### Session: {id1} - {project1}
{introspection for session 1}

#### Session: {id2} - {project2}
{introspection for session 2}

### Consolidation Suggestions
{content worth writing to .nexus/context}
```

---

## Write Threshold Check

> Before writing any anchor, verify at least ONE threshold is met:

```
[ ] Repetition >= 2: Similar issue/decision appeared twice+
[ ] High Impact: Architecture/Security/Performance/Multi-module
[ ] Reusable: Has reference value for other projects/scenarios
```

**If NO threshold met -> Do NOT write to anchors.md**

---

## Completion Verification

Before finishing, confirm:

```
+-----------------------------------------------------------+
|  COMPLETION CHECKLIST                                      |
|                                                            |
|  [ ] Step 1: index.json read (or confirmed missing)        |
|  [ ] Step 2: ALL relevant session compact.md read          |
|  [ ] Step 2.5: ALL relevant session reflection-output.json |
|                read                                        |
|  [ ] Step 3: Project anchors AND global anchors read       |
|  [ ] Step 4: Output generated with correct template        |
|  [ ] Anchoring bias: Scope confirmed before analysis       |
|                                                            |
|  ALL checked -> Introspection complete                     |
|  ANY missing -> GO BACK and complete missing steps         |
+-----------------------------------------------------------+
```

---

## Quick Reference

**File Paths:**
- Session index: `~/.nexus/context/index.json`
- Session data: `~/.nexus/context/sessions/{session_dir}/compact.md`
- Session reflection output: `~/.nexus/context/sessions/{session_dir}/reflection-output.json`
- Project anchors: `~/.nexus/context/anchors/projects/{project}.md`

**Introspection Dimensions:**
1. Specialist coordination
2. Parallelization efficiency
3. Context transfer
4. Verification quality
5. User interaction
6. Efficiency analysis

**See also:** `~/.claude/skills/reflection/reflection.md` for detailed templates and T3 write process.
