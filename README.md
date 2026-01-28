# Nexus

A multi-agent orchestration framework for Claude Code.

## Overview

Nexus is a multi-agent system with 7 specialized agents. The Orchestrator (main controller) coordinates specialists for efficient task execution.

**Core Principle:** The Orchestrator is the coordinator, not the executor.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/nexus.git
cd nexus

# Run the installer
./install.sh
```

### Usage

Start Claude Code and say:

```
/nexus
```

Or invoke a specific specialist:

```
/nexus @explorer explore the authentication module
/nexus @implementer fix the login bug
/nexus @architect design the caching solution
```

## The 7 Specialists

| Specialist | Purpose | Cost | Background |
|------------|---------|------|------------|
| **Explorer** | Explore, search, observe | CHEAP | Required |
| **Analyst** | Requirements, understanding, clarification | CHEAP | Optional |
| **Reviewer** | Review, detect, security | CHEAP | Required |
| **Tester** | Test, document, verify | MEDIUM | Optional |
| **Implementer** | Implement, fix, refactor | EXPENSIVE | Forbidden |
| **Architect** | Design, architecture, decisions | EXPENSIVE | Forbidden |
| **Planner** | L1 routing, task planning | CHEAP | Optional |

## Execution Tracks

Nexus automatically selects the execution track based on task type:

| Track | Trigger | Pipeline |
|-------|---------|----------|
| **feature** | add, create, new | Analyst+Explorer -> Architect -> Implementer -> Tester+Reviewer |
| **fix** | fix, bug, error | Explorer+Reviewer -> Implementer -> Tester |
| **refactor** | refactor, clean | Explorer -> Architect -> Implementer -> Reviewer+Tester |
| **research** | explore, understand | Explorer |
| **direct** | simple change | Orchestrator direct |

## Commands

| Command | Description |
|---------|-------------|
| `/nexus` | Activate Nexus workflow |
| `/nexus @{specialist}` | Invoke specific specialist |
| `/nexus reflection` | Run reflection and consolidation |
| `/plan <task>` | Analyze and plan task execution |

## Project Structure

```
nexus/
├── AGENTS.md              # Agent registry
├── CLAUDE.md              # Development guide
├── README.md              # This file
├── install.sh             # Installation script
├── nexus-dist/            # Source distribution
│   ├── rules/             # Core rules (auto-loaded)
│   ├── agents/            # Agent definitions (7 specialists)
│   ├── protocol/          # Protocol definitions
│   ├── reflection/        # Reflection system
│   ├── parallel/          # Parallel execution protocol
│   ├── commands/          # Custom commands
│   ├── context/           # Context management
│   └── hooks/             # PreCompact hooks
├── runtime/               # Runtime components
└── tests/                 # Test suite
```

## Installation Mapping

After installation, files are placed at:

```
~/.claude/rules/          <- Core rules (auto-loaded)
~/.claude/agents/         <- Agent definitions
~/.claude/commands/       <- Commands
~/.claude/skills/         <- Protocol, reflection, parallel
~/.nexus/                 <- Runtime data and hooks
```

## Key Concepts

### Orchestrator Iron Law

The Orchestrator coordinates but never executes:
- Exploration tasks -> delegate to Explorer
- Code changes >10 lines -> delegate to Implementer
- Architecture design -> delegate to Architect
- Tests -> delegate to Tester
- Code review -> delegate to Reviewer

### Verification Iron Law

**No evidence = Not complete**

All task completion must be verified:
- File exists (Glob/Read)
- Build passes
- Tests pass

### Parallelization

Specialists can execute in parallel when:
- Tasks are independent
- No data dependencies
- No file conflicts

## License

MIT

## Contributing

Contributions welcome! Please read the CLAUDE.md for development guidelines.
