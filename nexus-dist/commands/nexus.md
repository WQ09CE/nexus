---
allowed-tools: Task, Read, Glob, Grep
---

# Nexus Command

Activate Nexus multi-agent workflow.

## Usage

```
/nexus              # Activate
/nexus @eye ...     # Direct invoke eye
/nexus @body ...    # Direct invoke body
/nexus @mind ...    # Direct invoke mind
```

## @ Syntax

| Tag | Agent | Example |
|-----|-------|---------|
| @eye | Explorer | `/nexus @eye explore auth module` |
| @body | Implementer | `/nexus @body fix login bug` |
| @mind | Architect | `/nexus @mind design cache layer` |

## Workflow

1. Receive task
2. CHECKPOINT: Decide delegation
3. Invoke specialist(s)
4. Verify results
5. Report to user

## Starting

If no specific task provided, respond:

"Nexus ready! Tell me what you need help with?

**Direct invoke:** `/nexus @eye explore xxx` or `/nexus @body fix xxx`
**Auto selection:** `/nexus add login feature`"
