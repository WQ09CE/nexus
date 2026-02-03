# Nexus Multi-Agent System

**3 Specialists** - Minimal but Complete

## Agents

| Agent | Alias | Cost | Background | Purpose |
|-------|-------|------|------------|---------|
| `eye` | @eye, @explorer | CHEAP | Required | Explore, search |
| `body` | @body, @impl | EXPENSIVE | Forbidden | Implement, fix |
| `mind` | @mind, @architect | EXPENSIVE | Forbidden | Design, decide |

## Invocation

```python
Task(subagent_type="eye", prompt="...", run_in_background=True)
Task(subagent_type="body", prompt="...")
Task(subagent_type="mind", prompt="...")
```

## Agent Boundaries

| Agent | CAN DO | CANNOT DO |
|-------|--------|-----------|
| `eye` | Read, Glob, Grep, WebSearch, WebFetch | Write, Edit, Bash, Task |
| `body` | Read, Write, Edit, Bash, Glob, Grep | Task |
| `mind` | Read, Write (.md), Glob, Grep | Edit, Bash, Task |

## Agent Files

```
~/.claude/agents/
├── eye.md
├── body.md
└── mind.md
```

## Verification (Iron Law)

**No evidence = Not complete**

```
[ ] File exists (Glob/Read)
[ ] Build passes
[ ] Tests pass
```
