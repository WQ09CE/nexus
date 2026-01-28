# Parallel Execution Protocol

> Execute in parallel when possible - the essence of multi-agent is **simultaneous execution**, not queuing.

---

## Cost-Based Routing

> Cost routing configuration managed by Scheduler, see `~/.nexus/runtime/scheduler.py` for `AGENT_CONFIG`
>
> Quick reference: CHEAP(explorer/analyst/reviewer) 10+ concurrent background | MEDIUM(tester) 2-3 concurrent | EXPENSIVE(implementer/architect) 1 blocking

---

## Background Mode

> Explorer and Reviewer **forced background**, avoid output entering main context

### Background Specialist Configuration

| Specialist | Background Mode | Reason |
|------------|-----------------|--------|
| Explorer | **Required** | Exploration output large, should not enter main context |
| Reviewer | **Required** | Review results transferred via files |
| Analyst | Optional | Depends on task complexity |
| Tester | Optional | Depends on task complexity |
| Implementer | **Forbidden** | Must block execution, verify results |
| Architect | **Forbidden** | Design decisions need immediate interaction |

### Background Specialist Result Retrieval

```
After background specialist completes, two ways to get results:

1. Read output file
   ├── Applicable: Specialist generated output file
   └── Example: Read(".nexus/outputs/explorer-report.md")

2. TaskOutput retrieval
   ├── Applicable: Get specialist's direct output
   └── Example: TaskOutput(task_id="Explore auth module")
```

---

## Philosophy

The Parallel Protocol enables multiple specialists to **fly simultaneously**:
- Independent tasks execute in parallel, efficiency multiplied
- Dependent tasks execute serially, avoid chaos
- File territories are mutually exclusive, prevent conflicts
- Resources allocated reasonably, stable and controllable

---

## The Parallelization Decision Tree

```
Start task analysis
     |
     v
+------------------------------------------+
| Q1: Can task be decomposed into multiple |
|     independent subtasks?                 |
+------------------------------------------+
     |
     ├── NO --> Single specialist serial execution
     |
     v YES
+------------------------------------------+
| Q2: Are there data dependencies between   |
|     subtasks?                             |
|     (One's output is another's input)     |
+------------------------------------------+
     |
     ├── YES --> Serial in dependency order
     |
     v NO
+------------------------------------------+
| Q3: Will subtasks modify the same file?   |
+------------------------------------------+
     |
     ├── YES --> Serial (avoid conflict) or territory partitioning
     |
     v NO
+------------------------------------------+
| Can parallelize! Invoke multiple          |
| specialists simultaneously                |
+------------------------------------------+
```

---

## Parallelization Patterns

### Pattern 1: Specialist Swarm (Multi-Module Implementation)

**Scenario**: Implement multiple independent modules (no mutual dependencies)
**Speedup**: Theoretical Nx (N = module count)

```
After design complete:
     |
     ├──> [Implementer A] Implement module_a.py  ──┐
     ├──> [Implementer B] Implement module_b.py  ──┼──> Merge verification
     └──> [Implementer C] Implement module_c.py  ──┘

# Invocation (send multiple Tasks in same message)
Task(subagent_type="implementer", prompt="Implement module_a", run_in_background=true)
Task(subagent_type="implementer", prompt="Implement module_b", run_in_background=true)
Task(subagent_type="implementer", prompt="Implement module_c", run_in_background=true)
```

**Applicable Conditions**:
- No call dependencies between modules
- Each module has independent files
- Interface contracts defined beforehand

---

### Pattern 2: Scout & Infantry

**Scenario**: Need to constantly reference during implementation
**Speedup**: Reduces wait time

```
Start implementation:
     |
     ├──> [Explorer] Research related APIs and patterns (background)
     |         |
     |         └──> Continuously provide reference info
     |
     └──> [Implementer] Start implementing code
               |
               └──> When uncertain, get answers from Explorer

# Invocation
Task(subagent_type="explorer", prompt="Research library X usage and best practices", run_in_background=true)
Task(subagent_type="implementer", prompt="Implement feature Y, reference Explorer's findings")
```

**Applicable Conditions**:
- Implementation needs lots of reference materials
- Exploration and implementation can be synchronous
- Explorer's findings can be injected in real-time

---

### Pattern 3: TDD Pincer (Test + Implement Pincer)

**Scenario**: Interface already clearly defined (design doc/header file)
**Speedup**: ~2x

```
After interface definition complete:
     |
     ├──> [Tester] Write tests based on interface (background)
     |
     └──> [Implementer] Implement interface (background)
               |
               v
          [Merge] --> Run tests --> Verify

# Invocation
Task(subagent_type="tester", prompt="Write tests based on interface definition", run_in_background=true)
Task(subagent_type="implementer", prompt="Implement interface", run_in_background=true)
# Run tests after both complete
```

**Applicable Conditions**:
- Interface contract clear and specific
- Test cases derivable from interface
- Implementation and testing independent

---

### Pattern 4: Code + Config Parallel

**Scenario**: Prepare deployment config while implementing code
**Speedup**: ~1.5x

```
After design complete:
     |
     ├──> [Implementer] Implement core code
     |
     └──> [Architect] Prepare Dockerfile / CI config (background)
               |
               └──> Container config doesn't depend on implementation details

# Invocation
Task(subagent_type="implementer", prompt="Implement core functionality code")
Task(subagent_type="architect", prompt="Prepare Dockerfile and docker-compose", run_in_background=true)
```

**Applicable Conditions**:
- Config only depends on design, not implementation details
- Deployment structure already determined
- Config and code file changes don't overlap

---

### Pattern 5: Swarm Mode (Mass Operations)

**Scenario**: Batch refactor/migrate multiple independent files
**Speedup**: ~Nx

```
After refactoring plan confirmed:
     |
     ├──> [Implementer A] Refactor file_1.py  ──┐
     ├──> [Implementer B] Refactor file_2.py  ──┤
     ├──> [Implementer C] Refactor file_3.py  ──┼──> Merge
     └──> [Implementer D] Refactor file_4.py  ──┘

# Invocation (limit 3-4 specialists at once)
Task(subagent_type="implementer", prompt="Refactor file_1", run_in_background=true)
Task(subagent_type="implementer", prompt="Refactor file_2", run_in_background=true)
Task(subagent_type="implementer", prompt="Refactor file_3", run_in_background=true)
```

**Applicable Conditions**:
- Each file refactored independently
- Refactoring rules uniform
- No cross-file dependency changes

---

## Parallelization Rules

### Can Parallelize Scenarios

| Scenario | Pattern | Max Parallel |
|----------|---------|--------------|
| Implement multiple independent modules | Specialist swarm | 3-4 |
| Implement + explore reference | Scout+infantry | 2 |
| Implement + write tests (interface defined) | TDD pincer | 2 |
| Code + deploy config | Code+config parallel | 2 |
| Batch file modification | Swarm mode | 3-4 |
| Multi-file code review | Reviewer group | 3-4 |
| Multi-module code exploration | Explorer group | 3-4 |

### Must Serialize Scenarios

| Scenario | Reason |
|----------|--------|
| Requirements -> Architecture -> Implementation | Depends on upstream output |
| Multiple tasks modifying same file | Will cause conflict |
| Tests depend on incomplete code | Will fail |
| Decision points needing user confirmation | Blocking wait |
| A's output is B's input | Data dependency |
| Interface change + caller modification | Interface must stabilize first |

---

## Parallel Execution Syntax

**Key**: Send multiple Task calls in **same message**

```python
# Correct: Multiple Tasks in same message (parallel execution)
<message>
Task(subagent_type="implementer", prompt="Task A", run_in_background=true)
Task(subagent_type="implementer", prompt="Task B", run_in_background=true)
Task(subagent_type="implementer", prompt="Task C", run_in_background=true)
</message>

# Wrong: Sent separately (serial execution)
<message>Task(...Task A...)</message>
<message>Task(...Task B...)</message>
<message>Task(...Task C...)</message>
```

### Pre-Invocation Self-Check Checklist

Before launching parallel tasks, Orchestrator must self-ask:

```
[ ] How many independent files/modules do these tasks involve?
  --> If >= 2 independent files, consider parallel

[ ] Are there data dependencies between tasks?
  --> If A's output is B's input, must serialize

[ ] Will tasks modify same file?
  --> If yes, must serialize or territory partition

[ ] Are resources sufficient?
  --> Max 3-4 specialists simultaneously

[ ] Can launch in one message?
  --> Parallel tasks must launch simultaneously
```

---

## File Territory Protocol

> **Easiest collision during parallel implementation: two specialists modify same file** - Use territory protocol to avoid conflicts.

### Territory Declaration Rules

```
+---------------------------------------------------------------+
|  1. Declare territory before implementation                    |
|     Implementer must declare modification territory before     |
|     starting:                                                  |
|                                                                |
|     ```                                                        |
|     ## Territory Declaration                                   |
|     Specialist: Implementer A                                  |
|     Territory:                                                 |
|     - src/auth/login.py (entire file)                         |
|     - src/auth/utils.py (function: validate_token)            |
|     - tests/test_auth.py (new)                                |
|     ```                                                        |
+---------------------------------------------------------------+
|  2. Territory Mutual Exclusion                                 |
|     Other specialists must not write implementation content    |
|     in same territory                                          |
|     Allowed: Read, comment, suggest                           |
|     Forbidden: Edit, write, modify                            |
+---------------------------------------------------------------+
|  3. Conflict Handling                                          |
|     If overlap necessary (two specialists need same file):     |
|     - Orchestrator repartitions (split into non-overlapping)  |
|     - Or serialize (finish one, then start another)           |
+---------------------------------------------------------------+
```

### Territory Types

| Type | Format | Description |
|------|--------|-------------|
| Full file | `src/module.py` | Exclusive for entire file |
| Function level | `src/module.py:func_name` | Only modify specific function |
| Class level | `src/module.py:ClassName` | Only modify specific class |
| New | `src/new_file.py (new)` | Create new file |

### Territory Conflict Detection

```
Orchestrator checks territory conflicts before task distribution:

Task distribution:
├── Implementer A: src/auth.py, src/utils.py
├── Implementer B: src/api.py, src/utils.py  <-- Conflict!
|                           ^
|                    Overlaps with A's utils.py
|
└── Conflict resolution:
    ├── Option 1: Repartition
    |   - A: src/auth.py, src/utils.py:validate_*
    |   - B: src/api.py, src/utils.py:format_*
    |
    └── Option 2: Serialize
        - A finishes first --> B starts
```

### Territory Release

```
Specialist auto-releases territory after completing task:

Implementer A complete:
├── Output implementation report
├── Mark: Territory released
└── Other specialists can take over
```

---

## Resource Management

```
Parallel specialist limits:
├── Max simultaneous: 3-4 specialists
├── Background exploration: Not counted
└── When exceeded: Batch execution

Example (8 independent modules):
├── Batch 1: Modules 1, 2, 3, 4 (parallel)
├── Wait for completion
└── Batch 2: Modules 5, 6, 7, 8 (parallel)
```

### Resource Allocation Principles

| Task Type | Priority | Background? | Notes |
|-----------|----------|-------------|-------|
| Core implementation | High | No | Uses main resources |
| Code exploration | Medium | Yes | Background not counted |
| Code review | Medium | Yes | Can parallel in background |
| Config preparation | Low | Yes | Low priority background |

### Batch Execution Strategy

When task count exceeds parallel limit:

```
1. Sort tasks by priority
2. High priority tasks enter first batch first
3. Tasks within batch execute in parallel
4. Wait for current batch to complete
5. Start next batch
6. Repeat until all complete
```

---

## Merge Protocol

After parallel tasks complete:

```
1. Collect all specialist outputs
   ├── Implementation reports
   ├── Changed file lists
   └── Self-check results

2. Check for conflicts
   ├── File-level conflict: Two specialists modified same file
   └── Logic conflict: Interface mismatch

3. If conflict --> Manual resolution
   ├── Rollback conflicting changes
   ├── Designate one specialist to fix
   └── Re-merge

4. Run complete verification (build + test)
   ├── Compile/syntax check
   ├── Unit tests
   └── Integration tests

5. Continue after confirmation
```

### Merge Checklist

```
[ ] All specialists completed tasks
[ ] No file territory conflicts
[ ] Interface contracts consistent
[ ] Build passes
[ ] Tests pass
[ ] No regression issues
```

---

## Anti-Patterns

### Forbidden Behaviors

```
X Package multiple independent file modifications for one specialist
   --> Should be one specialist per file

X Serial execution of parallelizable exploration tasks
   --> Exploration tasks should parallel

X Start modifying without territory declaration
   --> Must declare first, then implement

X Ignore conflict and continue merging
   --> Must resolve conflict first

X Force parallel beyond resource limits
   --> Should batch execute
```

### Correct Approaches

```
O Analyze tasks, identify parallelizable parts
O Define interface contracts before parallel implementation
O Each specialist clearly declares territory
O Check conflicts before merge
O Batch execute when resources insufficient
```

---

## Quick Reference

### Parallelization Decision

| Question | Yes | No |
|----------|-----|-----|
| Task decomposable? | Continue checking | Serialize |
| Data dependencies? | Serialize | Continue checking |
| Modify same file? | Serialize/partition | Can parallel |

### Pattern Selection

| Scenario | Pattern |
|----------|---------|
| Multi-module implementation | Specialist swarm |
| Need reference | Scout+infantry |
| Interface defined | TDD pincer |
| Code+config | Code+config parallel |
| Batch modification | Swarm mode |

### Resource Limits

| Type | Limit |
|------|-------|
| Max parallel | 3-4 |
| Background tasks | Not counted |
| Exceeded handling | Batch execute |
