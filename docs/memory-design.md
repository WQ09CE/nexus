# Nexus Memory System Design

> Design Version: 1.0
> Designer: Architect (Mind)
> Date: 2026-02-03

## Summary

Design a layered memory system based on saved transcripts (`~/.nexus/context/`), providing cross-session memory through session summaries, a recent sessions index, and a project knowledge base. Optimized for token efficiency and practical utility.

---

## Design

### Architecture Overview

```
                           ┌──────────────────────────┐
                           │    New Session Start     │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                           ┌──────────────────────────┐
                           │   Memory Injection       │
                           │   (context loader)       │
                           └────────────┬─────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │  Project KB      │ │  Recent Index    │ │  Relevant        │
         │  (knowledge.md)  │ │  (recent.md)     │ │  Summaries       │
         └──────────────────┘ └──────────────────┘ └──────────────────┘
                                        ▲
                                        │
                    ┌───────────────────┴───────────────────┐
                    │         Summarization Layer           │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
         ┌─────────────────────────────────────────────────────────────┐
         │                   Transcript Storage                         │
         │  ~/.nexus/context/{project}/{timestamp}_{session_id}.jsonl  │
         └─────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                           ┌────────────┴─────────────┐
                           │   PreCompact Hook        │
                           │   (existing)             │
                           └──────────────────────────┘
```

### Core Components

1. **Transcript Storage** (existing)
   - Location: `~/.nexus/context/{project}/{timestamp}_{session_id}.jsonl`
   - Role: Raw conversation backup, source of truth
   - Already implemented via `precompact_save.py`

2. **Session Summarizer** (new)
   - Role: Generate concise summary from transcript
   - Output: `~/.nexus/memory/{project}/summaries/{timestamp}_{session_id}.md`
   - Triggered: Post PreCompact hook

3. **Recent Sessions Index** (new)
   - Location: `~/.nexus/memory/{project}/recent.md`
   - Content: Last N session summaries (rolling window)
   - Purpose: Quick context for new sessions

4. **Project Knowledge Base** (new)
   - Location: `~/.nexus/memory/{project}/knowledge.md`
   - Content: Extracted decisions, conventions, learnings
   - Growth: Slow, curated (manual or periodic merge)

5. **Memory Injector** (new)
   - Role: Load relevant memory into new session context
   - Trigger: Session start or `/nexus memory` command
   - Strategy: recent.md + optionally knowledge.md

### Data Flow

```
Session N (active)
       │
       │ PreCompact triggered
       ▼
┌─────────────────────────┐
│ precompact_save.py      │  ──── saves ────>  transcript.jsonl
└─────────────────────────┘
       │
       │ Post-save hook
       ▼
┌─────────────────────────┐
│ memory_summarize.py     │  ──── generates ──>  summary.md
└─────────────────────────┘
       │
       │ Update index
       ▼
┌─────────────────────────┐
│ memory_index.py         │  ──── updates ────>  recent.md
└─────────────────────────┘

Session N+1 (new)
       │
       │ Start / /nexus memory
       ▼
┌─────────────────────────┐
│ Memory Injector         │  ──── loads ──────>  recent.md, knowledge.md
└─────────────────────────┘
       │
       ▼
   Context enriched with cross-session memory
```

---

## Storage Format

### 1. Session Summary (`summaries/{timestamp}_{session_id}.md`)

```markdown
# Session Summary

**Date**: 2026-02-03 14:31:18
**Project**: nexus
**Duration**: ~45 min (estimated from message count)

## What Was Done
- Implemented PreCompact hook for transcript saving
- Added tests for the hook
- Fixed path reference issues

## Key Decisions
- Use project name from cwd (last path component)
- Truncate session_id to 8 chars in filename
- Store in ~/.nexus/context/ not ~/.claude/context/

## Files Changed
- `nexus-dist/hooks/precompact_save.py` (created)
- `tests/test_precompact_hook.py` (created)

## Open Items
- Need to design memory aggregation system

## Tags
#hooks #context-management #testing
```

**Size budget**: ~200-500 tokens per summary

### 2. Recent Sessions Index (`recent.md`)

```markdown
# Recent Sessions - nexus

*Last updated: 2026-02-03 15:00:00*
*Showing last 5 sessions*

---

## 2026-02-03 14:31 (abcd1234)

**Focus**: PreCompact hook implementation
**Outcome**: Completed hook + tests
**Key files**: precompact_save.py, test_precompact_hook.py

---

## 2026-02-02 10:15 (efgh5678)

**Focus**: Trim design for Nexus
**Outcome**: Designed 3-specialist system
**Key files**: docs/trim-design.md

---

(older sessions...)
```

**Size budget**: ~100 tokens per session * 5 = 500 tokens max

### 3. Project Knowledge Base (`knowledge.md`)

```markdown
# Project Knowledge - nexus

*Last updated: 2026-02-03*

## Architecture Decisions

### AD-1: 3 Specialist System
- **Decision**: Use body/eye/mind instead of 7 specialists
- **Rationale**: Simplicity over flexibility
- **Date**: 2026-02-02

### AD-2: Context Storage Location
- **Decision**: Use ~/.nexus/context/ for transcripts
- **Rationale**: Separate from Claude config (~/.claude/)
- **Date**: 2026-02-03

## Conventions

- File paths in hooks must be absolute
- Session IDs truncated to 8 chars in filenames
- Hook errors logged to stderr, not stdout

## Gotchas

- PreCompact hook receives JSON via stdin, not args
- transcript_path may not exist if session is new

## User Preferences

- Prefers minimal, evidence-based designs
- Values token efficiency
- Likes Chinese terminology (body=身, eye=眼, mind=意)
```

**Size budget**: ~500-1000 tokens, grows slowly

---

## Implementation Steps

### Phase 1: Summary Generation (Priority: High)

1. Create `~/.nexus/hooks/memory_summarize.py`
   - Input: transcript JSONL path
   - Output: summary markdown file
   - Logic: Extract key information from conversation

2. Modify hook chain to call summarizer after precompact_save
   - Option A: Chain in settings.json
   - Option B: precompact_save calls summarizer directly

### Phase 2: Recent Index (Priority: High)

1. Create `~/.nexus/hooks/memory_index.py`
   - Reads all summaries for project
   - Generates recent.md (last N sessions)
   - Triggered after summary generation

### Phase 3: Memory Injection (Priority: Medium)

1. Create `/nexus memory` command
   - Loads recent.md into context
   - Optionally loads knowledge.md

2. Auto-injection option (in settings.json or CLAUDE.md)
   - Inject on session start

### Phase 4: Knowledge Extraction (Priority: Low)

1. Manual curation first
   - User reviews summaries
   - Manually updates knowledge.md

2. Later: Semi-automated extraction
   - Periodic merge of patterns from summaries

---

## Decisions

### Decision 1: Layered Memory over Flat Storage

- **Decision**: Use 3 layers (transcripts -> summaries -> index/KB) instead of raw transcript search
- **Rationale**:
  - Raw transcripts too large for context injection
  - Summaries compress 10-100x while preserving key info
  - Index provides quick navigation
- **Alternatives considered**:
  - Vector search: Too complex, requires external dependencies
  - Single summary file: Loses granularity
- **Risk**: Summarization may lose important details

### Decision 2: Markdown Format for Summaries

- **Decision**: Use markdown (.md) instead of JSON for summaries
- **Rationale**:
  - Human-readable and editable
  - Can be directly injected into context
  - Compatible with existing CLAUDE.md convention
- **Alternatives considered**:
  - JSON: Harder to read, needs parsing for injection
  - YAML: Similar benefits to MD, but less common
- **Risk**: None significant

### Decision 3: Rolling Window for Recent Index

- **Decision**: Keep only last N sessions (default 5) in recent.md
- **Rationale**:
  - Bounds token cost
  - Most recent context usually most relevant
  - Older sessions accessible via individual summaries
- **Alternatives considered**:
  - All sessions: Unbounded growth
  - Time-based: Sessions vary in importance
- **Risk**: May lose context from important older sessions

### Decision 4: Post-Compact Summarization

- **Decision**: Generate summary after PreCompact, not during session
- **Rationale**:
  - Session is complete, has full context
  - No interruption to active work
  - Can process asynchronously
- **Alternatives considered**:
  - Real-time: Too expensive, incomplete
  - Manual: User burden
- **Risk**: Summarization quality depends on transcript structure

### Decision 5: Manual Knowledge Curation (Initially)

- **Decision**: Start with manual knowledge.md updates
- **Rationale**:
  - Automated extraction is hard to get right
  - Manual curation ensures quality
  - Can automate later based on patterns
- **Alternatives considered**:
  - Full automation: Risk of garbage accumulation
  - LLM-based extraction: Token cost, quality uncertain
- **Risk**: User may neglect updates

---

## Tradeoffs

1. **Completeness vs Token Cost**
   - Choice: Concise summaries (~300 tokens) over full transcripts
   - Sacrifice: Some details lost
   - Gain: 10-100x compression, fast injection

2. **Automation vs Quality**
   - Choice: Manual knowledge curation initially
   - Sacrifice: Convenience
   - Gain: High-quality, curated knowledge base

3. **Simplicity vs Flexibility**
   - Choice: Fixed summary format over configurable
   - Sacrifice: Customization
   - Gain: Consistency, easier parsing

4. **Recency vs Coverage**
   - Choice: Rolling window of N sessions
   - Sacrifice: Older session visibility
   - Gain: Bounded context size

---

## Constraints

- **Token Budget**: recent.md + knowledge.md should stay under 2000 tokens combined
- **Storage**: summaries/ can grow, but capped per project (e.g., 100 sessions)
- **Dependencies**: No external libraries (pure Python + Claude)
- **Compatibility**: Must work with existing precompact_save.py

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Summaries miss key info | Medium | Medium | Include "raw excerpt" option for important items |
| Index grows too large | Low | Medium | Enforce rolling window, archive old summaries |
| Knowledge.md stale | Medium | Low | Timestamp entries, periodic review prompts |
| Summarizer fails silently | Medium | High | Add error logging, validation in tests |
| User ignores memory system | Medium | Medium | Make injection optional but visible |

---

## Evidence

- Sources:
  - `/Users/DennisWang/SourceCode/ai-coding/nexus/nexus-dist/hooks/precompact_save.py:1-125` - Existing hook implementation
  - `/Users/DennisWang/SourceCode/ai-coding/nexus/docs/trim-design.md:1-483` - Previous design showing minimal approach preference
  - `/Users/DennisWang/.nexus/context/*/` - Actual transcript storage location

- Assumptions:
  - Claude Code transcript format is JSONL with role/content structure (common format, not verified)
  - Users will have 1-10 sessions per project per week (estimated usage)
  - Summaries can be generated with simple heuristics (may need LLM for quality)

---

## File Structure (After Implementation)

```
~/.nexus/
├── context/                         # Raw transcripts (existing)
│   └── {project}/
│       └── {timestamp}_{session}.jsonl
│
├── memory/                          # NEW: Memory system
│   └── {project}/
│       ├── summaries/               # Per-session summaries
│       │   └── {timestamp}_{session}.md
│       ├── recent.md                # Rolling recent sessions index
│       └── knowledge.md             # Project knowledge base
│
└── hooks/
    ├── precompact_save.py          # (existing)
    ├── memory_summarize.py         # NEW: Summary generator
    └── memory_index.py             # NEW: Index updater
```

---

## Next Steps

1. **Implement summary generator** (`memory_summarize.py`)
   - Parse JSONL transcript
   - Extract: what was done, decisions, files changed
   - Generate markdown summary

2. **Implement index updater** (`memory_index.py`)
   - Read all summaries for project
   - Generate recent.md with last N

3. **Create `/nexus memory` command**
   - Load and display recent.md
   - Option to load knowledge.md

4. **Add tests**
   - Summary generation
   - Index update
   - Memory injection

5. **Documentation**
   - Update README with memory system
   - Add usage examples

---

## Example Usage (Future)

```bash
# View memory for current project
/nexus memory

# Inject memory into current context
/nexus memory inject

# Update knowledge base manually
# (edit ~/.nexus/memory/{project}/knowledge.md)

# Force re-summarize a session
/nexus memory summarize ~/.nexus/context/nexus/20260203_143118_abcd1234.jsonl
```

---

## Alternative Designs Considered

### A: Vector Search Memory

```
Transcripts -> Chunk -> Embed -> Vector DB -> Semantic Search
```

**Pros**: Powerful retrieval, handles large history
**Cons**: Requires external deps (embeddings, vector DB), overkill for most cases
**Verdict**: Too complex for minimal system, consider for v2

### B: Single Rolling Summary

```
All sessions -> One growing summary file (append-only)
```

**Pros**: Simple, one file to manage
**Cons**: Unbounded growth, hard to find specific info
**Verdict**: Loses granularity, rejected

### C: LLM-Based Knowledge Extraction

```
Session -> LLM prompt -> Extracted facts/rules -> knowledge.md
```

**Pros**: High-quality extraction, automated
**Cons**: Token cost, extraction errors, complexity
**Verdict**: Consider for v2 when manual curation patterns are clear

---

## Appendix: Transcript Format (Expected)

Based on common Claude/Anthropic conventions, transcript JSONL likely contains:

```jsonl
{"type": "user", "content": "...", "timestamp": "..."}
{"type": "assistant", "content": "...", "timestamp": "..."}
{"type": "tool_use", "name": "Read", "input": {...}, "timestamp": "..."}
{"type": "tool_result", "output": "...", "timestamp": "..."}
```

**Note**: Actual format needs verification. Summarizer should be robust to format variations.
