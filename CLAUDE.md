# Nexus Development Guide (for Claude)

> This file provides context for Claude to iterate on the Nexus project correctly.
>
> **See also:** `AGENTS.md` for available agents and their capabilities.

## Core Protocol

Nexus uses a 7-specialist system. **The Orchestrator is the coordinator, not the executor.**

- Core protocol: `~/.claude/rules/00-nexus-core.md`
- Agent definitions: `~/.claude/agents/*.md`
- Agent boundaries: `~/.claude/skills/protocol/agent-protocol.md`

Invoke specialists using Task tool:
```
Task(subagent_type="explorer", prompt="...")   # Explorer - exploration
Task(subagent_type="implementer", prompt="...")  # Implementer - implementation
Task(subagent_type="architect", prompt="...")  # Architect - design
```

## Directory Mapping

```
Source (repo)              ->  Installed (user home)
-----------------------------------------------------
nexus-dist/rules/         ->  ~/.claude/rules/
nexus-dist/agents/        ->  ~/.claude/agents/
nexus-dist/commands/      ->  ~/.claude/commands/
nexus-dist/protocol/      ->  ~/.claude/skills/protocol/
nexus-dist/reflection/    ->  ~/.claude/skills/reflection/
nexus-dist/parallel/      ->  ~/.claude/skills/parallel/
nexus-dist/context/       ->  ~/.nexus/context/
nexus-dist/hooks/         ->  ~/.nexus/hooks/
runtime/                  ->  ~/.nexus/runtime/
```

**Key Insight:**
- `~/.claude/` = Claude Code configuration (rules, skills, commands, agents)
- `~/.nexus/` = Runtime data (hooks, context, notepads, plans)

## Development Workflow

```
1. Edit source     ->  nexus-dist/{rules,agents,commands}/*.md
2. Sync to home    ->  cp nexus-dist/xxx ~/.claude/xxx
                      (or run install.sh for full sync)
3. Test changes    ->  Use /nexus command to verify
4. Commit & push   ->  git add && git commit && git push
```

**Reverse Sync** (if edited in ~/.claude first):
```bash
cp ~/.claude/rules/00-nexus-core.md nexus-dist/rules/
```

## Common Pitfalls

| Wrong | Correct | Note |
|-------|---------|------|
| `~/.nexus/skills/` | `~/.claude/skills/` | Skills are in .claude, not .nexus |
| `~/.nexus/rules/` | `~/.claude/rules/` | Rules are in .claude, not .nexus |
| Edit ~/.claude directly | Edit nexus-dist/ first | Source of truth is repo |

## Quick Commands

```bash
# Sync single file to installed location
cp nexus-dist/rules/00-nexus-core.md ~/.claude/rules/

# Sync all rules
cp nexus-dist/rules/*.md ~/.claude/rules/

# Sync all agents
cp nexus-dist/agents/*.md ~/.claude/agents/

# Full install (recommended for major changes)
./install.sh

# Reverse sync (from installed back to repo)
cp ~/.claude/rules/00-nexus-core.md nexus-dist/rules/
```

## Project Structure

```
nexus/
├── CLAUDE.md              # This file (Claude dev context)
├── AGENTS.md              # Agent registry (Claude Code reads this!)
├── README.md              # User documentation
├── install.sh             # Installation script (Mac/Linux)
├── nexus-dist/            # Source files (edit here!)
│   ├── rules/             # Core rules (auto-loaded)
│   ├── agents/            # Agent definitions (7 specialists)
│   ├── protocol/          # Protocol definitions
│   ├── reflection/        # Reflection system
│   ├── parallel/          # Parallel execution protocol
│   ├── commands/          # Custom commands
│   ├── context/           # Context management
│   └── hooks/             # PreCompact hooks etc.
├── runtime/               # Runtime components (Python)
└── tests/                 # Test suite
```

## Testing Changes

After modifying rules or agents:

1. **Quick test**: Run `/nexus` and check behavior
2. **Verify paths**: `ls ~/.claude/agents/` to confirm files exist
3. **Check syntax**: Ensure markdown renders correctly

### Automated Tests

```bash
# Run path reference validation (catches wrong path errors)
python -m pytest tests/test_path_references.py -v

# Run all tests
python -m pytest tests/ -v
```

## Version Control

- **Always commit to repo** (nexus-dist/)
- **Never commit ~/.claude/** (it's user-specific)
- **Sync direction**: repo -> home (not reverse, unless recovering edits)
