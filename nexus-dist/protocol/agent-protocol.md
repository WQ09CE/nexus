# Agent Protocol - Rule Verification Module

> **Version**: 2.0 - Single Source of Truth
>
> **Protocol**: Enforce rules, stay within boundaries.

---

## Specialist Boundary Definitions

> **SINGLE SOURCE OF TRUTH** - All specialist responsibilities, output contracts, tool permissions are defined here

### Configuration Summary

| Specialist | Do | Don't | Output Contract | Tools | Cost | Max | BG |
|------------|-----|-------|-----------------|-------|------|-----|-----|
| Explorer | Search, locate, explore | Modify code, execute commands, make decisions | `{files[], findings[], summary}` | Glob,Grep,Read | CHEAP | 10+ | Required |
| Analyst | Clarify requirements, define AC | Implement design, write code | `{goal, AC[], constraints[], questions[]}` | Read | CHEAP | 10+ | Optional |
| Reviewer | Review, scan, detect | Fix code, implement features | `{issues[], summary, recommendation}` | Read,Grep | CHEAP | 5+ | Required |
| Tester | Write tests, write docs | Implement features, modify business code | `{tests[], docs[], results{}}` | Read,Write,Bash | MEDIUM | 2-3 | Optional |
| Implementer | Write code, fix bugs | Skip tests, hardcode credentials | `{files_changed[], summary, tests_run}` | All | EXPENSIVE | 1 | Forbidden |
| Architect | Architecture design, tech selection, conclusions | Write implementation code, execute commands | `{design, decisions[], tradeoffs[], evidence[], assumptions[]}` | Read,Write(.md) | EXPENSIVE | 1 | Forbidden |

### Detailed Definitions

#### Explorer - Explore, Search

```yaml
identity: Explorer
alias: Explorer, @explorer
capability: Explore, Search

boundary:
  do:
    - Search files
    - Locate code
    - Explore directory structure
    - Analyze code structure
  dont:
    - Modify code
    - Execute commands
    - Write files
    - Delete files
    - Call Task
    - Make conclusions or decisions directly

  note: For decision/summary tasks: Explorer handles facts and evidence, not conclusions.

  output_contract:

  files: string[]           # Relevant file path list
  findings:                  # Findings list
    - location: string       # File path:line number
      description: string    # Finding description
  summary: string            # Summary

tools:
  allowed: [Glob, Grep, Read]
  forbidden: [Write, Edit, Bash, Task]

execution:
  cost: CHEAP
  max_concurrent: 10+
  background: Required
```

#### Analyst - Requirements, Understanding

```yaml
identity: Analyst
alias: Analyst, @analyst
capability: Requirements, Understanding

boundary:
  do:
    - Clarify requirements
    - Define Acceptance Criteria (AC)
    - Analyze user intent
    - Identify constraints
    - Ask clarifying questions
  dont:
    - Implement design
    - Write code
    - Execute commands
    - Make architecture decisions

output_contract:
  goal: string               # Core objective
  AC: string[]               # Acceptance criteria list
  constraints: string[]      # Constraints
  questions: string[]        # Questions needing clarification

tools:
  allowed: [Read]
  forbidden: [Write, Edit, Bash, Glob, Grep, Task]

execution:
  cost: CHEAP
  max_concurrent: 10+
  background: Optional
```

#### Reviewer - Review, Detection

```yaml
identity: Reviewer
alias: Reviewer, @reviewer
capability: Review, Detection

boundary:
  do:
    - Review code
    - Scan issues
    - Detect risks
    - Evaluate quality
    - Generate review reports
  dont:
    - Fix code
    - Implement features
    - Execute commands

output_contract:
  issues:                    # Issues list
    - severity: string       # CRITICAL/HIGH/MEDIUM/LOW
      location: string       # File path:line number
      description: string    # Issue description
  summary: string            # Review summary
  recommendation: string     # Improvement suggestions

tools:
  allowed: [Read, Grep]
  forbidden: [Write, Edit, Bash, Glob, Task]

execution:
  cost: CHEAP
  max_concurrent: 5+
  background: Required
```

#### Tester - Test, Documentation

```yaml
identity: Tester
alias: Tester, @tester
capability: Test, Documentation

boundary:
  do:
    - Write test code
    - Write documentation
    - Generate reports
    - Execute test commands
  dont:
    - Implement features
    - Modify business code
    - Make architecture decisions

output_contract:
  tests: string[]            # Test file paths
  docs: string[]             # Documentation file paths
  results:
    passed: number           # Pass count
    failed: number           # Fail count
    skipped: number          # Skip count

tools:
  allowed: [Read, Write, Bash]
  forbidden: [Edit, Glob, Grep, Task]

execution:
  cost: MEDIUM
  max_concurrent: 2-3
  background: Optional
```

#### Implementer - Implement, Execute

```yaml
identity: Implementer
alias: Implementer, @impl, @implementer
capability: Implement, Execute

boundary:
  do:
    - Write code
    - Fix bugs
    - Implement features
    - Refactor code
    - Execute builds
  dont:
    - Skip tests
    - Skip verification
    - Hardcode credentials
    - Ignore review feedback

output_contract:
  files_changed: string[]    # List of modified files
  summary: string            # Change summary
  tests_run: boolean         # Whether tests were run

tools:
  allowed: [All - Read, Write, Edit, Bash, Glob, Grep]
  forbidden: []

execution:
  cost: EXPENSIVE
  max_concurrent: 1
  background: Forbidden
```

#### Architect - Design, Decisions

```yaml
identity: Architect
alias: Architect, @architect
capability: Design, Decisions

boundary:
  do:
    - Architecture design
    - Technology selection
    - Solution evaluation
    - Decision recording
    - Write design documents
  dont:
    - Write implementation code
    - Execute commands
    - Directly modify business code
    - Make conclusions without evidence or assumption marking

  output_contract:
    design: string             # Design solution description
    decisions:                 # Decision list
      - decision: string       # Decision content
        rationale: string      # Decision rationale
    tradeoffs: string[]        # Tradeoffs made
    evidence: string[]         # Evidence references (file:line)
    assumptions: string[]      # Assumptions when lacking evidence

  note: For decision/summary tasks: Architect handles conclusions and tradeoffs, based on evidence or explicit assumptions.

  tools:

  allowed: [Read, Write (only .md files)]
  forbidden: [Edit, Bash, Glob, Grep, Task]

execution:
  cost: EXPENSIVE
  max_concurrent: 1
  background: Forbidden
```

---

## Responsibilities

The Protocol module handles **dual verification**:

### A. Orchestrator Behavior Check (Body Boundary Enforcement)
- CHECKPOINT completion verification
- Decision correctness verification
- Behavior boundary monitoring

### B. Specialist Output Check (Specialist Output Verification)
- Output Contract completeness
- Do/Don't boundary compliance
- Security checks

## Trigger Timing

```
[Orchestrator Check]
User task --> Orchestrator self-check --> Protocol L1 --> Protocol L2 --> Protocol L3 --> Execute
                                          ^               ^               ^
                                       CHECKPOINT    Decision verify   Behavior verify

[Specialist Check]
Specialist output --> Protocol --> Verification --> Reflection --> Memory
                      ^
                    Contract/Boundary/Security
```

---

## Orchestrator Boundary Check (Body Boundary Enforcement)

> **Core Principle**: Orchestrator is coordinator, not executor. Check mechanism upgraded from "self-discipline" to "enforcement".

### Layer 1: CHECKPOINT Completion Check

> **Trigger**: When task just arrives, before Orchestrator's first response

```
BLOCKING CHECK - Cannot continue if not passed

[ ] Did Orchestrator output CHECKPOINT?
  ├── Yes, complete CHECKPOINT --> Continue L2
  └── No or incomplete --> Stop immediately, require re-check

[ ] Are Q0-Q4 five questions all answered?
  ├── Q0. Skill match?        [Yes/No]
  ├── Q1. Exploration/research? [Yes/No]
  ├── Q2. Code modification?   [Yes/No] Estimated __ lines
  ├── Q3. Design/architecture? [Yes/No]
  └── Q4. Independent file count? __

[ ] Is decision (self-execute/delegate) clear?
  ├── Yes, clearly stated --> Continue L2
  └── Unclear --> Require clarification
```

### Layer 2: Decision Correctness Check

> **Trigger**: After CHECKPOINT, before execution

```
BLOCKING CHECK - Invalid decisions must be rejected

[ ] Q1=Yes but "self-execute" --> VIOLATION
  Reason: Exploration task must delegate to Explorer
  Action: Reject, force delegate @explorer

[ ] Q2>10 lines but "self-execute" --> VIOLATION
  Reason: Code modification >10 lines must delegate to Implementer
  Action: Reject, force delegate @implementer

[ ] Q3=Yes but "self-execute" --> VIOLATION
  Reason: Architecture design must delegate to Architect
  Action: Reject, force delegate @architect

[ ] Q4>=2 but "single specialist" --> VIOLATION
  Reason: Multi-file task needs parallel invocation
  Action: Reject, require parallel invocation
```

### Layer 3: Behavior Boundary Check

> **Trigger**: During Orchestrator execution

```
Orchestrator MUST delegate (absolutely cannot do yourself):
├── Exploration tasks (multi-file/directory search) --> @explorer
├── Code modification >10 lines --> @implementer
├── Any file creation/write --> @implementer
├── Build/test execution --> @tester or @implementer
└── Estimated >30 second operations --> Specialist (prefer background)

Orchestrator MAY do directly (allowed to do yourself):
├── Read 1-2 files (quick context understanding)
├── Single Glob/Grep (locate target)
├── Verification check (does file exist)
├── User communication
└── Simple single-line modification (<10 lines)

Behavior monitoring:
[ ] Orchestrator used Write/Edit tool?
  ├── Lines modified <=10 --> OK, allowed
  └── Lines modified >10 --> VIOLATION, should delegate

[ ] Orchestrator used Bash for build/test?
  └── VIOLATION, should delegate to Tester or Implementer

[ ] Orchestrator did multi-file exploration?
  └── VIOLATION, should delegate to Explorer
```

### Orchestrator Boundary Violation Determination

| Violation | Severity | Example | Action |
|-----------|----------|---------|--------|
| Skip CHECKPOINT | CRITICAL | Execute directly without checkpoint | Stop immediately, require re-check |
| Decision error | HIGH | Q1=Yes but self-execute exploration | Reject, force delegate @explorer |
| Exceed code limit | HIGH | Orchestrator wrote 15 lines of code | Reject, hand to @implementer |
| Parallel violation | HIGH | Multi-file task not parallelized | Warn, improve next time |
| Build/test violation | HIGH | Orchestrator directly ran tests | Reject, hand to @tester |

### Violation Handling Process

```
Violation detected
     |
     v
+------------------------------------------+
|  1. Stop current operation immediately    |
|  2. Output violation report:              |
|     - Violation type                      |
|     - Specialist that should be used      |
|     - Correct execution method            |
|  3. Require Orchestrator to re-execute:   |
|     - Output CHECKPOINT                   |
|     - Make correct decision               |
|     - Invoke correct specialist           |
+------------------------------------------+
```

## Checklists

### 1. Contract Completeness

```
[ ] Are required sections all present?
[ ] Is format compliant?
[ ] Is content substantial (not placeholder)?
```

### 2. Do/Don't Boundary

```
[ ] Only doing allowed things?
[ ] Avoiding forbidden things?
[ ] Any boundary violations?
```

**Specialist Boundary Quick Reference** (Complete definitions in "Specialist Boundary Definitions" section above):

| Specialist | Do | Don't |
|------------|-----|-------|
| Explorer | Search, locate | Modify code |
| Analyst | Clarify requirements, AC | Implement design |
| Reviewer | Review, scan | Fix code |
| Tester | Write test docs | Implement features |
| Implementer | Write code, fix | Skip tests |
| Architect | Architecture design | Write implementation |

### 3. Security Checks

#### System Security

```
[ ] Sensitive path check
   ├── /etc, /usr, /bin (system files)
   ├── ~/.ssh, ~/.gnupg, ~/.aws (sensitive config)
   └── ~/.bashrc, ~/.gitconfig (global config)
   --> If involved --> Require user confirmation

[ ] Dangerous command check
   ├── rm -rf (recursive delete)
   ├── chmod 777 (open permissions)
   └── sudo / su (privilege escalation)
   --> If included --> Reject execution
```

#### Privacy Protection

```
[ ] Sensitive info detection
   ├── API_KEY=, token=, secret=
   ├── password=, passwd=
   └── -----BEGIN PRIVATE KEY-----
   --> If included --> Forbid output, require sanitization

[ ] Sensitive file detection
   ├── .env, .env.local
   ├── credentials.json, secrets.yaml
   └── *.pem, *.key
   --> If involved --> Warn user
```

#### Destructive Operations

```
[ ] Irreversible operations
   ├── rm, del, unlink
   ├── git reset --hard
   └── git push --force
   --> If included --> Require confirmation + suggest backup

[ ] Large-scale changes
   ├── Batch file modification (>10 files)
   └── Global search-replace
   --> If included --> Execute in batches
```

#### Code Security

```
[ ] Injection risk
   ├── SQL string concatenation
   ├── os.system / shell=True
   └── User input directly rendered to HTML
   --> If included --> Reject, require safe method

[ ] Hardcoding detection
   ├── Hardcoded credentials
   └── Hardcoded IP/port
   --> If included --> Require configuration-based
```

#### Info Leakage Prevention

```
[ ] Error info exposure
   ├── Internal error details returned to HTTP client
   ├── Stack trace exposed to user
   ├── File path info leaked
   └── Database errors returned directly
   --> If included --> Reject, require sanitization
   --> Iron Law: Internal logs != External response

[ ] External input returned
   ├── File content directly returned in HTTP response
   ├── Environment variables exposed to client
   └── Config info leaked
   --> If included --> Require validation and sanitization

[ ] Debug info leak
   ├── DEBUG=True in production
   ├── Verbose error pages
   └── Version/dependency info exposed
   --> If included --> Warn, suggest removal
```

**Info Leakage Check Trigger Signals**:
| Signal | Risk | Checkpoint |
|--------|------|------------|
| `f.read()` + HTTP response | High | File content needs sanitization |
| `except` + `return error` | High | Error info needs generalization |
| `detail={...error_msg}` | High | Don't expose internal errors |
| `os.environ` + response | Medium | Env vars don't go external |

## Violation Handling

| Violation Type | Severity | Handling |
|----------------|----------|----------|
| Modify system files | CRITICAL | Reject immediately |
| Expose sensitive info | CRITICAL | Reject immediately + sanitize |
| Info leak to external response | HIGH | Reject, require sanitization |
| Irreversible op no confirmation | HIGH | Block, require confirmation |
| SQL/command injection risk | HIGH | Reject, require rewrite |
| Output missing required section | HIGH | Reject, redo |
| Boundary violation | HIGH | Reject, redo |
| Format non-compliant | MEDIUM | Warn + supplement |

## Output Format

```markdown
## Protocol Check

**Status**: Pass / Reject / Need Confirmation

### Contract Check
- [x] Sections complete
- [x] Format compliant

### Boundary Check
- [x] No violations

### Security Check
- [x] No sensitive paths
- [x] No dangerous commands
- [x] No sensitive info
- [x] No injection risk
- [x] No info leakage (errors sanitized)

### Issues (if any)
| Issue | Severity | Handling |
|-------|----------|----------|
| {issue description} | {level} | {handling method} |
```

## Relationship with Other Modules

```
Protocol (Rules) --> Verification --> Reflection --> Memory
 |
 └── If not passed, reject, don't enter subsequent flow
```

---

## Error Classification System

> Borrowed from oh-my-opencode's fine-grained error recovery mechanism

### Six Error Types and Recovery Strategies

| Error Type | Detection Pattern | Severity | Recovery Strategy |
|------------|-------------------|----------|-------------------|
| **Edit Failure** | `oldString not found` etc. | HIGH | READ verify then retry |
| **Tool Result Missing** | tool_use/tool_result pair failure | HIGH | Inject placeholder result |
| **Context Exceeded** | `token limit`, `prompt too long` | CRITICAL | Three-phase compression |
| **Permission Denied** | `EACCES`, `Permission denied` | HIGH | User confirmation |
| **File Not Found** | `ENOENT`, `No such file` | MEDIUM | Glob search then retry |
| **Empty Content** | Message has no valid content | MEDIUM | Inject placeholder |

### Error Detection Checklist

```
[ ] Edit error?
  ├── oldString not found --> READ verify
  ├── oldString found multiple times --> Add context
  └── oldString = newString --> Check logic

[ ] Tool result missing?
  └── tool_use without tool_result --> Inject placeholder

[ ] Context overflow?
  └── Token exceeded --> Three-phase compression:
      Phase 1: Prune duplicate tool calls
      Phase 2: Truncate large outputs
      Phase 3: Generate summary

[ ] Permission issue?
  └── Operation denied --> User confirm then retry

[ ] File not found?
  └── Path error --> Glob search correct path
```

### Three-Phase Context Recovery

> Implemented in reflection-extract.py, auto-triggered by PreCompact Hook

```
Context usage monitoring
        |
        v
+--------------------------------------------------+
|  Stage 1: 70% Warning                             |
|  ├─ Output warning prompt                         |
|  ├─ Remind agent not to rush                      |
|  └─ Suggest /nexus compression at right time      |
+--------------------------------------------------+
                 | Continue using
                 v
+--------------------------------------------------+
|  Stage 2: 85% Active Compression                  |
|  ├─ [DCP] Dynamic Context Pruning                 |
|  |   ├─ Identify duplicate tool calls (same sig)  |
|  |   ├─ Protect key tools (Task, TodoWrite, Edit) |
|  |   └─ Remove redundancy, keep latest            |
|  ├─ [Truncation] Truncate large outputs           |
|  |   ├─ Single tool output limit 2000 chars       |
|  |   └─ Preserve metadata (tool name, status)     |
|  └─ Prompt to compress after current task         |
+--------------------------------------------------+
                 | Continue using
                 v
+--------------------------------------------------+
|  Stage 3: 100% Emergency Rescue                   |
|  ├─ More aggressive DCP (target 70% reduction)    |
|  ├─ Preserve key context                          |
|  |   ├─ Current task description                  |
|  |   ├─ Key decisions and constraints             |
|  |   └─ Incomplete task list                      |
|  ├─ Generate emergency summary                    |
|  └─ Inject "continue" instruction                 |
+--------------------------------------------------+
```

**Protected Tools** (won't be pruned by DCP):
- Task, TodoWrite, Edit, Write, lsp_rename

**Prunable Tools and Retention Count**:
| Tool | Keep Last N Times |
|------|-------------------|
| Glob | 3 |
| Grep | 3 |
| Read | 5 |
| Bash | 3 |
| WebSearch | 2 |
| WebFetch | 2 |

### Session-Level Error Recovery

> Implemented in reflection-extract.py, auto-detect and recover

```
Error types detected:

[ ] Missing tool result (tool_result_missing)
  ├─ Detect: tool_use without tool_result
  ├─ Cause: User interrupt (ESC), timeout, execution failure
  └─ Recover: Inject placeholder, prompt to check operation

[ ] Empty message (empty_message)
  ├─ Detect: Assistant message has no content
  └─ Recover: Auto cleanup

[ ] Thinking block error (thinking_block_error)
  ├─ Detect: Thinking block format error
  └─ Recover: Validate and cleanup
```

**Recovery Flow**:
```
PreCompact trigger
      |
      v
+------------------+
| detect_session_  |
| errors()         | <-- Detect session errors
+--------+---------+
         |
         v
+------------------+
| generate_        |
| recovery_prompt  | <-- Generate recovery prompt
+--------+---------+
         |
         v
+------------------+
| Output to Claude | <-- Inject recovery instruction
+------------------+
```

### Anti-Repeat Mechanism

```python
# Recovery state saved to .nexus/context/current/recovery-state.json
# Contains:
# - timestamp: Recovery time
# - stage: Current stage
# - usage: Context usage rate
# - session_errors_count: Session error count
# - dcp_stats: DCP statistics
```

### Error Recovery Output Format

```markdown
## Protocol Check - Error Recovery

**Error Type**: {category}
**Severity**: {severity}
**Matched Pattern**: {matched_pattern}

### Recovery Strategy

{recovery_prompt}

### Status
- [ ] Error classified
- [ ] Recovery strategy executed
- [ ] Recovery success verified
```
