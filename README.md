# Empire

A Claude Code plugin that maintains persistent context across sessions through a dynasty succession model.

## Problem

Claude Code starts every session from scratch. Previous decisions, their reasoning, and accumulated project knowledge are lost. You end up re-explaining the same things, and Claude re-discovers the same patterns.

## How it works

Empire keeps a rolling window of structured context that automatically rotates as it grows stale. It uses three roles inspired by Foundation's Brother Dawn/Day/Dusk:

- **Day** — active context driving current decisions
- **Dawn** — staged context prepared for the next ruler
- **Dusk** — archived wisdom distilled from previous rulers

Each generation is named (Claude I, Claude II, ...) and earns an epithet based on what it worked on ("the Builder", "the Debugger"). When context pressure builds — too many entries, too many sessions, or too much stale context — succession fires automatically. Day compresses into Dusk, Dawn promotes to Day, and a new Dawn is seeded.

A separate **Vault** holds permanent context (50-line cap) that survives all successions.

### What runs automatically

Three hooks handle everything without user interaction:

**SessionStart** — Loads the Vault and a pre-computed briefing into context. Searches the lineage archive for topics relevant to current work and surfaces hints.

**PostToolUse** — Silently tracks which context entries are referenced based on files and keywords touched. Stays under 100ms.

**Stop** — Applies reference scores. The Session Scribe analyzes `git diff` to auto-generate typed Day entries with `Why:` reasoning. Regenerates the briefing. Evaluates succession pressure.

### Entry types

Every entry is typed as a **decision** or an **observation**.

Decisions carry a `Why:` field explaining rationale. This field is sacred — it is never compressed, summarized, or paraphrased through any tier of demotion. It survives succession, context rotation, and lineage archival verbatim.

Observations are facts about what happened. They compress safely because the code is the source of truth.

```markdown
### [ref:0] [decision] Chose RS256 over HS256 for JWT signing
Why: Auth service needs asymmetric verification across microservices.
What: Implemented in auth.service.ts using jose library

### [ref:0] [observation] Added rate limiter middleware
express-rate-limit applied globally before route matching
```

### Succession

Triggered automatically when:
- Day has more than 30 entries
- 5+ sessions since last succession
- 60%+ of entries have reference score 0 (stale)

Or manually via `/empire succession`.

During succession, entries are categorized (not summarized) through compression tiers. Decisions keep their `Why:` verbatim. Observations compress based on reference score. Zero-score entries demote to a searchable lineage archive. Entries referenced across 3+ successions auto-promote to the Vault.

### Ancestor Oracle

Past rulers' decisions are searchable. The oracle activates proactively at session start (keyword matching against lineage) and on demand for deep consultation. Every finding is attributed to the specific ruler who made it.

## Install

```bash
claude plugin marketplace add jansimner/empire
claude plugin install empire
```

## Usage

```bash
/empire init          # Found a dynasty for the current project
```

Then work normally. Everything else is automatic.

```bash
/empire               # Status dashboard
/empire succession    # Manual succession (--review for interactive)
/empire vault         # Manage permanent context (add, remove, swap)
/empire dawn          # View/add items staged for next ruler
/empire deviant       # Flag/resolve contradictions between vault and state
/empire lineage       # Search retired context archive
```

## Project layout

```
plugins/empire/
├── core/               Python library
│   ├── paths.py          Path resolution
│   ├── state.py          Dynasty state management
│   ├── entries.py        Entry parsing and serialization
│   ├── dashboard.py      Status dashboard rendering (emoji-width-aware)
│   ├── briefing.py       Day briefing generation
│   ├── ref_tracker.py    Reference score tracking
│   ├── scribe.py         Git diff to typed entries
│   ├── oracle.py         Lineage search and attribution
│   └── constants.py      Thresholds and defaults
├── hooks/              SessionStart, PostToolUse, Stop
├── commands/           Skill definitions for /empire commands
├── agents/             Succession, Scribe, Oracle subagents
├── tests/              120 tests
└── skills/             Detailed protocol references
```

**Committed state** (`.empire/` in project root):
- `vault.md` — permanent context, 50-line cap
- `protocol.md` — dynasty rules

**Working state** (`~/.claude/projects/<key>/empire/`, per-user):
- `dynasty/<branch>/` — day.md, dawn.md, dusk.md, dynasty.json per branch
- `lineage.md` — searchable archive of retired rulers
- `deviants.md` — tracked contradictions

## License

MIT
