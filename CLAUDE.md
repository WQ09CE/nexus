# Nexus Development Guide (for Claude)

> This file provides context for Claude to iterate on the Nexus project correctly.
>
> **See also:** `AGENTS.md` for available agents and their capabilities.

## Core Protocol

Nexus uses a 3-specialist system. **The Orchestrator is the coordinator, not the executor.**

- Core protocol: `~/.claude/rules/00-nexus-core.md`
- Agent definitions: `~/.claude/agents/*.md`

Invoke specialists using Task tool:
```
Task(subagent_type="eye", prompt="...")    # Eye - exploration
Task(subagent_type="body", prompt="...")   # Body - implementation
Task(subagent_type="mind", prompt="...")   # Mind - design
```

## Directory Mapping

```
Source (repo)              ->  Installed (user home)
-----------------------------------------------------
nexus-dist/rules/         ->  ~/.claude/rules/
nexus-dist/agents/        ->  ~/.claude/agents/
nexus-dist/commands/      ->  ~/.claude/commands/
runtime/                  ->  ~/.nexus/runtime/
```

## Development Workflow

```
1. Edit source     ->  nexus-dist/{rules,agents,commands}/*.md
2. Sync to home    ->  ./install.sh
3. Test changes    ->  Use /nexus command to verify
4. Commit & push   ->  git add && git commit && git push
```

## Project Structure

```
nexus/
├── CLAUDE.md              # This file (Claude dev context)
├── AGENTS.md              # Agent registry
├── README.md              # User documentation
├── install.sh             # Installation script
├── nexus-dist/            # Source files (edit here!)
│   ├── rules/             # Core rules (auto-loaded)
│   ├── agents/            # Agent definitions (3 specialists)
│   └── commands/          # Custom commands
├── runtime/               # Runtime components
└── tests/                 # Test suite
```

## Testing Changes

After modifying rules or agents:

1. **Quick test**: Run `/nexus` and check behavior
2. **Verify paths**: `ls ~/.claude/agents/` to confirm files exist

### Automated Tests

```bash
# Run all tests
python -m pytest tests/ -v
```

## Version Control

- **Always commit to repo** (nexus-dist/)
- **Never commit ~/.claude/** (it's user-specific)
- **Sync direction**: repo -> home
