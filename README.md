# Nexus

A minimal multi-agent orchestration framework for Claude Code.

## Overview

Nexus is a 3-specialist system. The Orchestrator coordinates specialists for efficient task execution.

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
/nexus @eye explore the authentication module
/nexus @body fix the login bug
/nexus @mind design the caching solution
```

## The 3 Specialists

| Specialist | Purpose | Cost | Background |
|------------|---------|------|------------|
| **eye** | Explore, search, observe | CHEAP | Required |
| **body** | Implement, fix, refactor | EXPENSIVE | Forbidden |
| **mind** | Design, architecture, decisions | EXPENSIVE | Forbidden |

## Project Structure

```
nexus/
├── AGENTS.md              # Agent registry
├── CLAUDE.md              # Development guide
├── README.md              # This file
├── install.sh             # Installation script
├── nexus-dist/            # Source distribution
│   ├── rules/             # Core rules (auto-loaded)
│   ├── agents/            # Agent definitions (3 specialists)
│   └── commands/          # Custom commands
├── runtime/               # Runtime components
└── tests/                 # Test suite
```

## Installation Mapping

After installation, files are placed at:

```
~/.claude/rules/          <- Core rules (auto-loaded)
~/.claude/agents/         <- Agent definitions
~/.claude/commands/       <- Commands
~/.nexus/runtime/         <- Runtime data
```

## Key Concepts

### Orchestrator Iron Law

The Orchestrator coordinates but never executes:
- Exploration tasks -> delegate to @eye
- Code changes >10 lines -> delegate to @body
- Architecture design -> delegate to @mind

### Verification Iron Law

**No evidence = Not complete**

All task completion must be verified:
- File exists (Glob/Read)
- Build passes
- Tests pass

## License

MIT

## Contributing

Contributions welcome! Please read the CLAUDE.md for development guidelines.
