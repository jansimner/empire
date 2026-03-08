# Empire

**Continuous Context Protocol for Claude Code**

Empire is a Claude Code plugin that manages conversation context through a dynasty succession metaphor inspired by Foundation. Context has a lifecycle -- it is born (Dawn), rules (Day), advises (Dusk), and eventually retires to lineage -- preventing unbounded growth while preserving critical knowledge. Nothing is ever deleted; everything demotes gracefully through tiers.

## The Foundation Metaphor

| Foundation     | Empire                                                    |
|----------------|-----------------------------------------------------------|
| Brother Dawn   | Staged context -- prepared, learning, not yet active      |
| Brother Day    | Active context -- driving current decisions               |
| Brother Dusk   | Archived wisdom -- distilled patterns and learnings       |
| Succession     | Context rotation -- triggered by pressure or manually     |

Each dynasty member earns a regnal name (Claude I, Claude II, ...) and an epithet based on their work ("the Architect", "the Debugger"). Succession happens automatically when context pressure builds, or on demand.

## Installation

```bash
claude plugin add /path/to/empire
```

## Quick Start

```bash
# Found your dynasty
/empire init
```

Then just work normally. Empire runs entirely in the background through three hooks:

- **SessionStart** loads your Vault (permanent truths) and a pre-computed Day briefing into context -- roughly 80 lines total.
- **PostToolUse** silently tracks which context entries you're actively referencing based on the files and keywords you touch.
- **Stop** updates reference scores, generates the next session's briefing, and checks whether succession should be triggered.

When succession fires, Empire rotates context automatically: Day becomes Dusk, Dawn becomes Day, and a new Dawn is seeded from git state and past wisdom. Each git branch maintains its own dynasty -- switching branches switches dynasties automatically.

## Commands Reference

| Command                       | Description                                                           |
|-------------------------------|-----------------------------------------------------------------------|
| `/empire`                     | Status dashboard -- current dynasty, pressure, and entry counts       |
| `/empire init`                | Found a new dynasty for the current project                           |
| `/empire succession`          | Manually trigger succession. Use `--review` for interactive review    |
| `/empire vault`               | View and manage immortal context (add, remove, swap). 50-line cap     |
| `/empire dawn`                | View or add items staged for the next ruler                           |
| `/empire deviant`             | Flag or resolve contradictions between Vault and current state        |
| `/empire lineage`             | Search the structured archive of retired context                      |

## How It Works

Empire uses three hooks that run automatically:

**SessionStart** fires on every conversation start or resume. It detects the current git branch, finds the matching dynasty, and injects the Vault (~50 lines) plus the pre-computed Day briefing (~30 lines) into conversation context. Total overhead is roughly 80 lines per session.

**PostToolUse** fires after Read, Edit, Write, Grep, and Glob tool calls. It extracts file paths and keywords from tool input and matches them against Day entries using tiered scoring: exact file path match (+2), same directory overlap (+1), or 2+ keyword matches (+1). Scores are cached and applied in batch at session end. This hook stays under 100ms.

**Stop** fires when the conversation ends. It applies the batched reference scores, generates a compressed Day briefing for the next session, and evaluates three succession triggers:
- Day has more than 30 entries
- 5+ sessions since the last succession
- 60%+ of Day entries have a reference score of 0 (stale)

If any trigger fires, succession is noted for the next session.

## Entry Types

Every Day entry is typed as either a **decision** or an **observation**. This distinction drives everything about how entries compress and demote through tiers.

**Decisions** carry a `Why:` field that explains rationale. The `Why:` field is sacred -- it is never compressed, summarized, or paraphrased through any tier. This is a mechanical rule, not an AI judgment call.

**Observations** are facts about what happened. They compress safely because the code still exists as the source of truth.

```markdown
### [ref:5] [decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.
What: Implemented in auth.service.ts using jose library

### [ref:2] [observation] Fixed rate limiter gap on health endpoint
express-rate-limit middleware now applied globally before route matching.
```

| Type        | Tier compression                                               | Can be auto-pruned?                                     |
|-------------|----------------------------------------------------------------|---------------------------------------------------------|
| Decision    | `What:` compresses, `Why:` survives verbatim through ALL tiers | Never. Demoted to lineage if ref 0, but `Why:` preserved |
| Observation | Compresses normally through tiers                              | Yes, demoted to lineage by ref score                     |

## Succession

Succession is triggered automatically (when pressure thresholds are met) or manually via `/empire succession`. The succession agent runs in a subagent to avoid polluting the main conversation.

**What happens during succession:**

1. **Freeze** -- Snapshot current Day, Dusk, and Dawn. Record the trigger reason.
2. **Compress Dusk** -- Existing Dusk entries shift one tier down. Decisions keep their `Why:` verbatim; only `What:` compresses. Layer 3 observations with ref 0 across 3 successions demote to lineage.
3. **Day to Dusk** -- The succession agent categorizes each Day entry (not summarizes). Decisions have `Why:` preserved verbatim. Observations compress based on ref score. Score 0 entries demote to structured lineage with full original text.
4. **Dawn to Day** -- Dawn contents become the new Day. Scores reset. Dynasty counter increments.
5. **Seed new Dawn** -- Fresh Dawn seeded from git state (branch, recent commits, uncommitted changes) and keyword-matched Dusk wisdom.
6. **Vault check** -- Dusk entries referenced across 3+ successions auto-promote to Vault if space permits. If the Vault is full, candidates are tagged `[vault-candidate]` quietly.
7. **Deviant check** -- Scan new Dusk entries for file-path conflicts with Vault. Auto-flag conflicts. Nudge old unresolved deviants.
8. **Ceremony** -- Generate the succession report and write lineage.

The key insight: distillation is **categorization, not summarization**. The agent never rewrites or paraphrases `Why:` fields. Observations compress safely because the code is the source of truth. The "telephone game" problem is eliminated for decisions and acceptable for observations.

**Succession ceremony output:**
```
┌─────────────────────────────────────────────────────┐
│  ⚔️  SUCCESSION OF CLAUDE VI "THE GATEKEEPER"       │
│  🌿 Branch: main                                    │
├─────────────────────────────────────────────────────┤
│  💀 Claude IV "the Architect"   Dusk → lineage        │
│  🌙 Claude V  "the Debugger"   Day  → Dusk          │
│  ☀️  Claude VI "the Gatekeeper" Dawn → Day           │
│  🌅 Claude VII                       → born as Dawn  │
├─────────────────────────────────────────────────────┤
│  🏛️  Vault:    [████████████░░░░] 46/50              │
│  ⚡ Deviants: 1 unresolved (session 3/10)            │
├─────────────────────────────────────────────────────┤
│  👑 Long live Claude VII. May they earn their name.  │
└─────────────────────────────────────────────────────┘
```

## Configuration

Empire is zero-config by default. All thresholds ship with sensible defaults that work out of the box.

Power users can hand-edit `.empire/config.md` to adjust thresholds. The file contains commented-out defaults that document every configurable value. A `/empire config` command is planned for v2.

## Project Layout

```
empire/
├── .claude-plugin/
│   └── plugin.json                Plugin metadata and hook registrations
├── commands/
│   ├── empire.md                  /empire → status dashboard
│   ├── empire-init.md             /empire init → found dynasty
│   ├── empire-succession.md       /empire succession → manual trigger
│   ├── empire-vault.md            /empire vault → manage immortals
│   ├── empire-dawn.md             /empire dawn → view/add staged items
│   ├── empire-deviant.md          /empire deviant → flag/resolve
│   └── empire-lineage.md          /empire lineage → search history
├── agents/
│   └── succession-agent.md        Subagent for distillation + ceremony
├── hooks/
│   ├── hooks.json                 Hook registrations
│   ├── session_start.py           Load Vault + briefing
│   ├── post_tool_use.py           Reference tracking
│   └── stop.py                    Ref scores, briefing, pressure check
├── skills/
│   └── succession-protocol/
│       └── SKILL.md               Detailed succession logic
├── core/
│   ├── __init__.py
│   ├── paths.py                   Path resolution for project/working state
│   ├── state.py                   Dynasty state management
│   ├── entries.py                 Entry parsing and manipulation
│   ├── briefing.py                Day briefing generation
│   ├── ref_tracker.py             Reference score tracking
│   └── constants.py               Shared thresholds and defaults
├── tests/                         Test suite
├── docs/plans/                    Design and implementation documents
├── pyproject.toml                 Python project configuration
└── README.md
```

**Project state** (`.empire/`, committed to git, shareable):
```
.empire/
├── vault.md       # Immortal context, <= 50 lines
├── protocol.md    # Dynasty rules
└── config.md      # Thresholds (commented defaults, hand-editable)
```

**Working state** (`~/.claude/projects/<project>/empire/`, private):
```
empire/
├── dynasty/
│   ├── main/
│   │   ├── dawn.md
│   │   ├── day.md
│   │   ├── day-briefing.md
│   │   ├── dusk.md
│   │   └── dynasty.json
│   └── feature-payments/
│       └── ...              # Each branch gets its own dynasty
├── deviants.md
└── lineage.md
```

## License

MIT
