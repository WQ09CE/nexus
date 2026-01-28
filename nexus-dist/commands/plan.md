# Plan Command

> **Intelligent Planning** - Analyze tasks, plan optimal execution path
>
> **Layered Routing**: L0 Rule Matching (0ms) -> L1 Haiku Planner (~300ms, only when needed)

## Usage

```
/plan <task description>
/plan --dry-run <task description>    # Only analyze, don't execute
/plan --force-llm <task description>  # Force use Haiku Planner
```

## Two-Layer Routing Architecture

```
User task
    |
    v
+-------------------------------------+
|  L0: Python Rule Matching (0ms)     |
|  - @ syntax parsing                 |
|  - Keyword matching                 |
|  - Returns track + confidence       |
+-------------------------------------+
    |
    v
confidence >= 0.7? --YES--> Output result directly
    |
    NO (needs_llm=true)
    |
    v
+-------------------------------------+
|  L1: Haiku Planner (~300ms)         |
|  - Task(model="haiku")              |
|  - Precise classification +         |
|    complexity judgment              |
|  - Returns track + complexity +     |
|    phases                           |
+-------------------------------------+
    |
    v
Output final result
```

## Execution Steps

### Step 1: L0 Rule Matching

Run Python CLI for quick analysis:

```bash
python3 ~/.nexus/runtime/cli.py analyze "{user_task}"
```

Parse returned JSON:
- `track`: Track (fix/feature/refactor/direct)
- `confidence`: Confidence (0.0-1.0)
- `needs_llm`: Whether Haiku Planner needed
- `phases`: Execution phases

### Step 2: Determine if L1 Needed

**Skip L1 Conditions**:
- `confidence >= 0.7`
- User didn't specify `--force-llm`

**Need L1 Conditions**:
- `confidence < 0.7` (needs_llm=true)
- User specified `--force-llm`

### Step 3: L1 Haiku Planner (if needed)

If L1 needed, invoke Haiku Planner:

```
Invoke Haiku Planner:
- Specialist: planner
- Model: haiku
- Reason: L0 confidence insufficient, need more precise task classification
- Skill: Read planner.md agent definition
- Expected: JSON format {track, complexity, confidence, reasoning, phases}
```

**Task Tool Call**:
```json
{
  "subagent_type": "planner",
  "model": "haiku",
  "prompt": "You are Nexus's Planner...\n\nTASK: {user_task}\nL0_RESULT: {l0_result_json}\n\nPlease analyze task and output JSON format planning result."
}
```

**Haiku Planner Prompt Template**:
```
You are Nexus's Planner - responsible for analyzing tasks and selecting optimal execution track.

## Input
TASK: {user_task}
L0_RESULT: {l0_result_json}

## Output Format
Output this JSON format (no other text):
{
  "track": "feature|fix|refactor|research|direct",
  "complexity": "simple|medium|complex",
  "confidence": 0.0-1.0,
  "reasoning": "brief reason",
  "phases": [
    {"phase": 0, "nodes": ["agent1", "agent2"], "parallel": true},
    {"phase": 1, "nodes": ["agent3"], "parallel": false}
  ]
}

## Track Definitions
- feature: Add new feature, implement new capability
- fix: Fix bug, solve problem
- refactor: Refactor, optimize, clean code
- research: Explore, research, understand code
- direct: Simple operation, single-line change

## Complexity Definitions
- simple: Single file, <50 line changes
- medium: 2-3 files, medium changes
- complex: 4+ files, architecture changes

## Agent Nodes (CRITICAL - USE EXACT IDs)
- explorer_explore: Explorer (exploration)
- analyst_understand: Analyst (requirements)
- reviewer_analyze / reviewer_review: Reviewer (analysis/review)
- tester_verify: Tester (testing)
- implementer_implement: Implementer (implementation)
- architect_design: Architect (design)

**Forbidden variants**: ear_analyst, eye_explorer, mind_architect, body_impl, tongue_tester, nose_reviewer etc.
```

### Step 4: Output Result

Output this Markdown format:

```markdown
## Planning Analysis Result

### Routing Info
- **Routing Layer**: {L0 / L1}
- **Confidence**: {confidence}%

### Task Info
- **Description**: {task_description}
- **Detected Track**: {track} (Feature/Fix/Refactor/Research/Direct)
- **Complexity**: {complexity} (if available)

### Execution Plan

| Phase | Specialist | Parallel | Description |
|-------|------------|----------|-------------|
| 0 | Explorer + Analyst | Yes | Explore + understand requirements |
| 1 | Architect | No | Architecture design |
| 2 | Implementer | No | Code implementation |
| 3 | Tester + Reviewer | Yes | Test + review |

### Suggested Actions
{Suggestions based on analysis}
```

## Now Execute

Read user's task description, execute this flow:

1. **Parse Parameters**
   - `--dry-run`: Only output analysis, don't suggest execution
   - `--force-llm`: Force use Haiku Planner
   - No parameters: Auto-determine if L1 needed

2. **Run L0 Analysis**
   ```bash
   python3 ~/.nexus/runtime/cli.py analyze "{user_task}"
   ```

3. **Determine if L1 Needed**
   - If `needs_llm=true` or `--force-llm`
   - Then invoke Haiku Planner (using Task tool)

4. **Format Output**
   - Use Markdown format defined above
   - Include routing layer info

## Planner Configuration Reference

### Specialist Cost Configuration

| Specialist | Cost | Model | Max Concurrent | Background |
|------------|------|-------|----------------|------------|
| Explorer | CHEAP | haiku | 10+ | Required |
| Analyst | CHEAP | haiku | 10+ | Optional |
| Reviewer | CHEAP | haiku | 5+ | Required |
| Tester | MEDIUM | sonnet | 3 | Optional |
| Implementer | EXPENSIVE | sonnet | 1 | Forbidden |
| Architect | EXPENSIVE | opus | 1 | Forbidden |

### Track DAGs

**Feature**: Analyst+Explorer -> Architect -> Implementer -> Tester+Reviewer
**Fix**: Explorer+Reviewer -> Implementer -> Tester
**Refactor**: Explorer -> Architect -> Implementer -> Reviewer+Tester
**Research**: Explorer
**Direct**: Direct execution

## Error Handling

- If Python CLI doesn't exist, prompt to check `~/.nexus/runtime/` directory
- If Haiku Planner returns non-JSON, try to extract JSON portion
- If task description is empty, prompt user to provide task

---

**Ready**! Please provide task description, I will analyze and generate optimal planning.
