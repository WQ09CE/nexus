# Reflection Module

> **Reflection**: Gain insight into essence, transcend appearances. Reflect timely, consolidate timely.

## Responsibilities

The Reflection module is Nexus's "wisdom core", responsible for:
- **Bias Scanning** - Detect assumptions/biases (cross-cutting capability)
- **Introspection** - Diagnose deviations, propose rule patches
- **Result Verification** - Check verification sufficiency
- **Context Refinement** - Extract key information
- **Trigger Memory Write** - Identify anchors worth consolidating

## Trigger Timing

```
Specialist output --> Protocol --> Verification --> Reflection --> Memory
                                                    ^
                                                 Current location

Additional triggers:
├── /nexus reflection     (manual)
├── PreCompact Hook       (auto before compression)
└── After complex task    (auto)
```

## Bias Scanning (Cross-Cutting Capability)

> Bias scanning is not in the pipeline, but a **cross-cutting capability**, detecting assumptions and biases in specialist output anytime.

### Scanning Mode

```
Any specialist output --> Bias Scan
                          |
                          ├─ Assumptions: Implicit assumptions
                          ├─ Evidence missing: Missing evidence
                          ├─ Scope creep: Scope creep risk
                          └─ Suggested checks: Suggested verifications
```

### Danger Signals (Must Intercept)

```
L0 Speculative language:
├── "should be able to..." / "probably can..."
├── "I think..." / "I believe..."
├── "generally..." / "usually..."
├── "obviously..." / "of course..."
└── "no problem" / "should be fine"

Action: Mark + require evidence
```

### Healthy Signals (Can Pass)

```
With evidence support:
├── "According to {path}:{line}, ..."
├── "Executed {command} output {result}"
├── "Test {test_name} passed"
└── "[D001] Decision: ..."

Action: Pass
```

### Context Anchoring Bias

> **Common Trap**: Being anchored by current session context, ignoring broader data

```
Anchoring trigger words:
├── "today all/total work" --> May have multiple sessions
├── "all my projects" --> May span multiple projects
├── "recent changes" --> May span branches/projects
└── "summarize" --> Need to confirm scope

Wrong behavior: Only look at current session/project
Correct behavior: First scan cross-session data
```

| User Says | Wrong Understanding | Correct Understanding |
|-----------|---------------------|----------------------|
| "today all work" | Current session work | All sessions today |
| "all my projects" | Current project | All active projects |
| "recent changes" | Current branch changes | May span branches/projects |

**Action**: Identify anchoring trigger words --> Scan cross-session data --> Then summarize

### Bias Scan Output

```markdown
## Bias Check

**Input**: {specialist output summary}

### Detected Assumptions
| Assumption | Type | Risk | Action |
|------------|------|------|--------|
| "This function should handle null values" | L0 speculation | High | Need test |

### Filter Decision
- Pass: {trustworthy content}
- Pending verification: {content needing verification}
- Reject: {L0 speculation, need redo}
```

## Introspection

> Introspection focuses on discovering systemic issues and proposing rule patches.
>
> **Complete introspection execution flow see**: `~/.claude/commands/reflection.md`

### Introspection Command

```
/nexus reflection
```

When executing introspection, **must follow BLOCKING checklist** (see `reflection.md`):

1. **Step 1**: Read `~/.nexus/context/index.json`
2. **Step 2**: Read ALL relevant `sessions/*/compact.md`
3. **Step 3**: Read `~/.nexus/context/anchors.md`
4. **Step 4**: Generate output

> **Warning**: Skipping any step = Protocol violation. Common mistake: Only read index.json and anchors, miss sessions directory.

### Introspection Three Things

```
+----------------------------------------------------------+
|  1. Deviation Diagnosis                                    |
|     Where was the biggest waste in this collaboration?     |
|     Why?                                                   |
+----------------------------------------------------------+
|  2. Rule Patch                                             |
|     Which rules need to be added/tightened/loosened?       |
+----------------------------------------------------------+
|  3. Distillation                                           |
|     What info is worth writing to Memory?                  |
+----------------------------------------------------------+
```

### Review Dimensions

1. **Specialist Coordination** - Was selection correct? Any omissions?
2. **Parallelization Efficiency** - Any missed parallel opportunities?
3. **Context Transfer** - Was info transferred completely?
4. **Verification Quality** - Was verification sufficient?
5. **User Interaction** - Was communication clear?
6. **Efficiency Analysis** - Any obvious bottlenecks?

### Introspection Output

```markdown
## Introspection Report: {task_name}

### 1. Deviation Diagnosis
**Efficiency Loss Point**: {specific description}
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
| P0xx | Pitfall | {pitfall} | Repeat>=2 | Y/N |
```

## Verification Sufficiency Check

```
[ ] Do core paths have L2/L3 verification?
[ ] Are boundary conditions tested?
[ ] Is error handling verified?
```

### Verification Scoring

| Grade | Description |
|-------|-------------|
| A | L3 verification + boundary + error handling |
| B | L2 verification + partial boundary |
| C | L2 verification, insufficient boundary |
| D | L1 or lower, needs supplementation |

## Context Refinement

> Prepare refined context for Memory module.

### Three-Form Compression

```
Giant form (complete) --> Normal form (structured) --> Compact form (<500 chars)
```

### Refinement Principles

**Keep**:
- Decision conclusions (not discussion process)
- Interface signatures (not implementation details)
- Constraint rules (not background explanation)
- Current state (not historical process)
- Anchor references

**Discard**:
- Exploratory discussions
- Rejected solutions
- Temporary debug info
- Repeated confirmation dialogues

## Anchor Extraction

> Identify info worth consolidating to Memory.

### Write Threshold (at least one must be met)

```
[ ] Repeat >= 2: Similar issue/decision appeared twice or more
[ ] High Impact: Involves architecture, security, performance, multi-module
[ ] Reusable: Has reference value for other projects/scenarios
```

### Anchor Types

| Type | Prefix | Description |
|------|--------|-------------|
| Decision | D | Architecture/technical decisions |
| Constraint | C | Rules that must be followed |
| Interface | I | Key interface definitions |
| Problem | P | Known issues/pitfalls |
| Pattern | M | Reusable patterns |

### Anchor Format

```markdown
## [D001] {Decision Title}

**Date**: {date}
**Status**: Active / Pending Verification / Deprecated

### Decision
{What decision was made}

### Alternatives
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

### Why
{Reason for choice}

### Impact
{Scope of impact}

### Rollback
{How to rollback}
```

## PreCompact Hook Integration

> Reflection module can trigger via PreCompact Hook before auto-compression.

### Hook Configuration

```json
{
  "hooks": {
    "PreCompact": [{
      "matcher": "auto",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.nexus/hooks/reflection-extract.py"
      }]
    }]
  }
}
```

### Hook Execution Flow

```
PreCompact trigger
      |
      v
reflection-extract.py
      |
      ├─ Read transcript_path (complete conversation)
      ├─ Bias scan (detect assumptions)
      ├─ Extract key info (decisions/constraints/interfaces)
      ├─ Generate refined context
      └─ Trigger Memory write
            |
            ├─ current/compact.md
            └─ anchors.md (new anchors)
```

## Relationship with Other Modules

```
Protocol (Rules) --> Verification --> Reflection --> Memory
                                      |
                                      ├─ Bias Scan: Can scan any specialist output anytime
                                      ├─ Introspection: Manual or triggered after task completion
                                      └─ PreCompact: Triggered before auto-compression
```

## Taboos

**NEVER**:
- Reflect for the sake of reflecting (simple tasks don't need deep introspection)
- Only criticize without suggesting
- Speak in generalities (suggestions must be specific and actionable)
- Skip threshold check and directly consolidate

**ALWAYS**:
- Evaluate objectively and neutrally
- Provide specific actionable suggestions
- Balance affirmation and improvement
- Check thresholds before triggering Memory write

---

## Introspection Specialist Invocation Guide

> The following content is integrated from introspector.md, providing detailed introspection execution guide.

### Trigger Timing (When to Invoke)

Introspection should be triggered at these times:

1. **After task completion** - Standard reflection flow (`/nexus reflection`)
2. **After task failure** - Analyze failure causes
3. **User explicit request** - "reflect on this", "summarize"
4. **After complex task** - Multi-specialist collaboration tasks
5. **Before archiving** - Auto-trigger T3 write flow

### Review Dimension Detailed Templates

#### 1. Specialist Coordination Analysis

```
Review questions:
├── Was specialist selection correct?
├── Were any unnecessary specialists invoked?
├── Were any needed specialists missed?
├── Was handoff between specialists smooth?
└── Was there responsibility overlap or gap?
```

**Output template**:
```markdown
## Specialist Coordination Analysis

### Specialists Invoked
| Specialist | Task | Performance | Improvement Suggestion |
|------------|------|-------------|----------------------|
| {specialist} | {task} | Pass/Warn/Fail | {suggestion} |

### Selection Evaluation
- Correct selections: {list}
- Unnecessary invocations: {list}
- Should have but didn't invoke: {list}

### Handoff Quality
{handoff analysis}
```

#### 2. Parallelization Efficiency Analysis

```
Review questions:
├── Which tasks could be parallel but were actually serial?
├── Was the parallel pattern used optimal?
├── How was resource utilization?
├── Were there unnecessary waits?
└── Was parallel task merging smooth?
```

**Output template**:
```markdown
## Parallelization Efficiency Analysis

### Execution Pattern
Actual: {actual_pattern}
Optimal: {optimal_pattern}
Efficiency loss: {efficiency_loss}

### Missed Parallel Opportunities
| Task A | Task B | Reason | Estimated Savings |
|--------|--------|--------|-------------------|
| {task_a} | {task_b} | {reason} | {time_saved} |

### Parallel Pattern Usage
- Specialist swarm: {used/not_used}
- Scout+infantry: {used/not_used}
- TDD pincer: {used/not_used}
```

#### 3. Context Transfer Analysis

```
Review questions:
├── Was info transfer between specialists complete?
├── Was there duplicate exploration/work?
├── Was knowledge properly recorded?
├── Was prior knowledge utilized?
└── Was context overloaded?
```

**Output template**:
```markdown
## Context Transfer Analysis

### Information Flow
{source} --> {specialist_1} --> {specialist_2} --> {output}

### Issues Found
- Info lost: {lost_context}
- Duplicate work: {duplicate_work}
- Context overload: {overload_issues}

### Knowledge Management
- Recorded knowledge: {recorded}
- Should have recorded but didn't: {missing}
- Reused knowledge: {reused}
```

#### 4. Verification Quality Analysis

```
Review questions:
├── Was specialist output sufficiently verified?
├── Was there over-trust in specialist claims?
├── Did verification cover all deliverables?
├── Were there missed boundary conditions?
└── Was final state clean?
```

**Output template**:
```markdown
## Verification Quality Analysis

### Verification Execution Status
| Verification Item | Executed | Result | Notes |
|-------------------|----------|--------|-------|
| File exists | Yes/No | {result} | |
| Syntax check | Yes/No | {result} | |
| Build passes | Yes/No | {result} | |
| Tests pass | Yes/No | {result} | |

### Trust Issues
- Over-trusted claims: {trusted_claims}
- Should verify but didn't: {unverified}
```

#### 5. User Interaction Analysis

```
Review questions:
├── Was progress reported timely?
├── Were users asked when needed?
├── Did final delivery match expectations?
├── Was there over-asking?
└── Was communication style appropriate?
```

**Output template**:
```markdown
## User Interaction Analysis

### Communication Quality
- Progress reports: {frequency} times
- Confirmation asks: {count} times
- User satisfaction: {assessment}

### Delivery Match
User request: {user_request}
Actual delivery: {actual_delivery}
Match rate: {match_percentage}
```

#### 6. Efficiency Analysis

```
Review questions:
├── Was total execution time reasonable?
├── Were there obvious bottlenecks?
├── Was tool usage efficient?
├── Was there rework/redo?
└── How to be faster next time?
```

**Output template**:
```markdown
## Efficiency Analysis

### Time Distribution
| Phase | Time | Percentage | Reasonable |
|-------|------|------------|------------|
| Requirements understanding | {time} | {pct}% | Yes/No |
| Exploration research | {time} | {pct}% | Yes/No |
| Design | {time} | {pct}% | Yes/No |
| Implementation | {time} | {pct}% | Yes/No |
| Verification | {time} | {pct}% | Yes/No |

### Bottleneck Identification
Main bottleneck: {bottleneck}
Cause: {reason}
Optimizable: {optimization}
```

### Memory T3: Memory Write Flow

> **Introspection is Memory's "read-write portal"** - Trigger T3 write flow before archiving.

#### T3 Trigger Conditions

| Condition | Description |
|-----------|-------------|
| User triggers `archive` / `compress` command | Explicit archive request |
| Context usage > 85% | Auto-trigger archive |
| Session about to end | Ensure knowledge not lost |
| Deep introspection complete | Standard reflection flow ends |

#### T3 Write Flow

```
Introspection complete / Archive trigger
        |
        v
+----------------------------------------+
|  Step 1: Collect Candidate Anchors      |
|  Extract from Distillation section      |
|  Candidate types: D(Decision),          |
|  P(Pitfall), M(Pattern)                 |
+-----------------+----------------------+
                  |
                  v
+----------------------------------------+
|  Step 2: Write Threshold Check          |
|  (at least one met)                     |
|  +----------------------------------+   |
|  | [ ] Repeat: Similar issue >=2    |   |
|  | [ ] Impact: Arch/Security/Perf   |   |
|  | [ ] Reusable: Other project ref  |   |
|  +----------------------------------+   |
|  Threshold not met --> Skip, don't write|
+-----------------+----------------------+
                  |
                  v
+----------------------------------------+
|  Step 3: Dedup Check                    |
|  - Find existing anchors similarity >0.8|
|  - Similar title --> Merge or update    |
|  - Decision conflict --> Mark for review|
+-----------------+----------------------+
                  |
                  v
+----------------------------------------+
|  Step 4: Execute Write                  |
|  - New anchor --> Write to              |
|    .nexus/context/anchors.md            |
|  - Merge anchor --> Update existing     |
|  - Pending review --> Write to          |
|    anchors-pending.md                   |
+----------------------------------------+
```

#### T3 Output Format

```markdown
## [Memory T3] Write Report

### Write Check Results
| ID | Type | Content | Threshold | Dedup | Result |
|----|------|---------|-----------|-------|--------|
| D0xx | Decision | {content} | Impact high | No dup | Write |
| P0xx | Pitfall | {content} | Repeat>=2 | Merge to P003 | Update |

### Write Statistics
- New anchors: {count}
- Merge updates: {count}
- Pending review: {count}
- Skipped: {count}
```

### Reflection Depth Guide

```
Quick reflection (1-2 minutes):
- Only look at key dimensions
- Output brief suggestions

Deep reflection (5-10 minutes):
- Complete review of all dimensions
- Output detailed report
- Trigger T3 write flow
```
