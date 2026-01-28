# Nexus Multi-Agent System

**Version:** 1.0
**Purpose:** Specialist-based multi-agent orchestration system

## Overview

Nexus is a multi-agent orchestration system with 7 specialized agents. The Orchestrator (main controller) coordinates specialists for task execution.

**Core Principle:** The Orchestrator is the coordinator, not the executor.

## Agent Discovery

Claude Code invokes specialists via the Task tool:

```
Task(subagent_type="explorer", prompt="...")   # Explorer
Task(subagent_type="implementer", prompt="...")  # Implementer
```

## Available Agents (6 Specialists + Planner)

| Agent | Alias | Model | Cost | Background | Purpose |
|-------|-------|-------|------|------------|---------|
| `explorer` | Explorer | Sonnet | CHEAP | Required | Explore, search, observe |
| `analyst` | Analyst | Sonnet | CHEAP | Optional | Requirements, understanding, clarification |
| `reviewer` | Reviewer | Sonnet | CHEAP | Required | Review, detect, security |
| `tester` | Tester | Sonnet | MEDIUM | Optional | Test, document, verify |
| `implementer` | Implementer | Opus | EXPENSIVE | Forbidden | Implement, fix, refactor |
| `architect` | Architect | Opus | EXPENSIVE | Forbidden | Design, architecture, decisions |
| `planner` | Planner | Haiku | CHEAP | Optional | L1 routing, task planning |

### Planner Agent (L1 Intelligent Routing)

Planner is a lightweight agent for L1 routing layer:

- **Trigger**: When L0 rule routing returns `confidence < 0.7`
- **Responsibility**: Analyze task, return track + phases + complexity
- **Model**: Haiku (fast, low cost)
- **Input**: `TASK: {task description}` + `L0_RESULT: {rule match result}`
- **Output**: JSON execution plan

```
L0 Rule Routing -> confidence < 0.7 -> Planner (Haiku) -> Execution Plan
               -> confidence >= 0.7 -> Use L0 result directly
```

### Agent Selection Guide

| Task Type | Best Agent | @Syntax |
|-----------|------------|---------|
| Explore codebase, search files | `explorer` | `@explorer` |
| Analyze requirements, clarify intent | `analyst` | `@analyst` |
| Code review, security scan | `reviewer` | `@reviewer` |
| Write tests, generate docs | `tester` | `@tester` |
| Implement features, fix bugs | `implementer` | `@impl` |
| Architecture design, technical decisions | `architect` | `@architect` |

### Agent Boundaries (Critical)

Each specialist has strict responsibility boundaries:

| Agent | CAN DO | CANNOT DO |
|-------|--------|-----------|
| `explorer` | Read, Glob, Grep, WebSearch | Write, Edit, Bash, Task |
| `analyst` | Read | Write, Edit, Bash, Glob, Grep, Task |
| `reviewer` | Read, Glob, Grep | Write, Edit, Bash, Task |
| `tester` | Read, Write (tests/docs only), Bash, Glob | Edit, Task |
| `implementer` | Read, Write, Edit, Bash, Glob, Grep | Task |
| `architect` | Read, Write (.md only), Glob, Grep | Edit, Bash, Task |

## Tracks (Execution Pipelines)

Track selection based on task type:

| Track | Trigger Keywords | DAG Flow |
|-------|------------------|----------|
| **feature** | add, create, new, implement | [analyst+explorer] -> [architect] -> [implementer] -> [tester+reviewer] |
| **fix** | fix, bug, error, crash | [explorer+reviewer] -> [implementer] -> [tester] |
| **refactor** | refactor, clean, optimize | [explorer] -> [architect] -> [implementer] -> [reviewer+tester] |
| **research** | explore, research, understand | [explorer] |
| **direct** | simple, single-line | (Orchestrator direct execution) |

## Parallelization

- **CHEAP agents** (explorer, analyst, reviewer): 10+ concurrent, explorer/reviewer forced background
- **MEDIUM agents** (tester): 2-3 concurrent, optional background
- **EXPENSIVE agents** (implementer, architect): 1 blocking, background forbidden

Agents in the same Phase can execute in parallel: `[analyst+explorer]` means analyst and explorer run simultaneously.

## Core Protocol Reference

Detailed protocols at:
- `~/.claude/rules/00-nexus-core.md` - Core protocol
- `~/.claude/skills/protocol/agent-protocol.md` - Agent boundary definitions
- `~/.claude/skills/parallel/parallel-protocol.md` - Parallel protocol

## Agent Definition Files

Agent definition file location: `~/.claude/agents/` (Claude Code standard location)

```
~/.claude/agents/
├── explorer.md      # Explorer definition
├── analyst.md       # Analyst definition
├── reviewer.md      # Reviewer definition
├── tester.md        # Tester definition
├── implementer.md   # Implementer definition
├── architect.md     # Architect definition
└── planner.md       # Planner definition (L1 routing)
```

> **Important**: Must be in `~/.claude/agents/` directory for Claude Code Task tool to recognize custom `subagent_type`.

## Commands

| Command | Description |
|---------|-------------|
| `/nexus` | Activate Nexus multi-agent workflow |
| `/nexus reflection` | Run reflection and consolidation |
| `/plan` | Task analysis and route selection |

## Anti-Patterns (Forbidden Behaviors)

- **Orchestrator direct implementation**: Code over 10 lines must be delegated to implementer
- **Skip CHECKPOINT**: Must analyze task before execution
- **Serial execution of parallelizable tasks**: Same-Phase agents should run in parallel
- **Specialist invoking specialist**: Specialists cannot use Task tool
- **Report completion without verification**: Must have Evidence

## Verification (Iron Law)

**Iron Law:** No evidence = Not complete

```
Verification Checklist:
[ ] File exists (Glob/Read)
[ ] Build passes (build command)
[ ] Tests pass (test command)
[ ] Type check (type check)
```
