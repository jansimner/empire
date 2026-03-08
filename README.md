# Empire

**Your AI takes immaculate notes on your genius, automatically.**

Empire is a Claude Code plugin that gives your AI generational intelligence. Every session builds on the last. Decisions are preserved with their reasoning intact, forever. Context rotates gracefully through a dynasty succession model inspired by Foundation -- nothing is ever deleted, everything demotes through tiers until it rests in a searchable lineage archive.

You don't type `[decision]` or `Why:` fields. The **Session Scribe** watches your git diff and auto-generates Day entries. The **Ancestor Oracle** proactively searches past rulers' wisdom when you start a session. You just work. When you run `/empire status`, the AI has already correctly deduced _why_ you made the choices you did.

## What Happens Automatically

A typical session lifecycle, without you doing anything:

**1. Session starts** -- Vault + briefing loaded (~80 lines). The Ancestor Oracle scans lineage for topics relevant to your current work and surfaces hints: _"Ancestors may have wisdom on: authentication, middleware."_

**2. You work normally** -- PostToolUse silently tracks which context entries are actively referenced based on the files and keywords you touch. No interruptions.

**3. Session ends** -- The Session Scribe analyzes `git diff`, auto-generates typed Day entries, and enhances them with LLM-powered `Why:` reasoning. The briefing for your next session is pre-computed.

**4. After several sessions** -- Succession triggers automatically. Context rotates: Day becomes Dusk, Dawn becomes Day, a new Dawn is seeded. The outgoing ruler earns an epithet. A ceremony is displayed:

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

## The Dynasty Model

| Foundation     | Empire                                                    |
|----------------|-----------------------------------------------------------|
| Brother Dawn   | Staged context -- prepared, learning, not yet active      |
| Brother Day    | Active context -- driving current decisions               |
| Brother Dusk   | Archived wisdom -- distilled patterns and learnings       |
| Succession     | Context rotation -- triggered by pressure or manually     |

Each dynasty member earns a regnal name (Claude I, Claude II, ...) and an epithet based on their work ("the Architect", "the Debugger", "the Gatekeeper"). Succession happens automatically when context pressure builds, or on demand.

## Session Scribe -- Autonomous Archaeology

The Session Scribe runs in the Stop hook. When your session ends, it:

1. Runs `git diff` to see exactly what changed
2. Classifies changes heuristically -- new files, deleted files, test updates, config changes, grouped by directory
3. Merges auto-generated entries with any existing Day entries (human-written entries always take priority)
4. Optionally spawns the `session-scribe` agent to enhance entries with LLM-powered reasoning

The Scribe turns raw diffs into typed entries:

```markdown
### [ref:0] [decision] Chose RS256 over HS256 for JWT signing
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.
What: Implemented in auth.service.ts using jose library

### [ref:0] [observation] Added rate limiter middleware
express-rate-limit applied globally before route matching (+45 lines)
```

The `Why:` field is **sacred** -- once written, it is never compressed, summarized, or paraphrased through any tier. This is a mechanical rule, not an AI judgment call. Sacred decisions survive dynasty succession, context rotation, and the heat death of your project. They are the generational intelligence that makes each new Claude session smarter than the last.

## Ancestor Oracle -- Consulting the Lineage

The Ancestor Oracle activates in two ways:

**Proactive hints at session start.** The SessionStart hook extracts topic keywords from your current briefing, Dawn, and Vault, then searches the lineage archive. If past rulers made relevant decisions, you see a hint:

```
Ancestors may have wisdom on: authentication, middleware
   Use /empire lineage --search or ask me to consult the ancestors.
```

**Deep consultation on demand.** Claude can spawn the `ancestor-oracle` agent for a full ceremonial consultation. Every finding is attributed to the specific ruler who made it:

```
Consulting the Ancestors on "JWT authentication"...

Found 2 relevant entries from past rulers:

### Claude III "the Architect" (main)
[decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.

### Claude II "the Builder" (main)
[observation] Rate limiter applied globally before route matching
```

According to Claude III "the Architect," your auth service needs asymmetric verification. The Ancestor Oracle ensures that wisdom is never lost to context rotation -- it is always one question away.

## Installation

```bash
claude plugin marketplace add jansimner/empire
claude plugin install empire
```

## Quick Start

```bash
# Found your dynasty
/empire init
```

Then just work normally. Empire runs entirely in the background through three hooks:

- **SessionStart** loads your Vault (permanent truths) and a pre-computed Day briefing into context. The Ancestor Oracle searches lineage and surfaces relevant hints. Total overhead: ~80 lines.
- **PostToolUse** silently tracks which context entries you're actively referencing based on the files and keywords you touch.
- **Stop** updates reference scores, the Session Scribe auto-generates Day entries from git diff, the briefing is regenerated, and succession pressure is evaluated.

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

## Entry Types

Every Day entry is typed as either a **decision** or an **observation**. This distinction drives everything about how entries compress and demote through tiers.

**Decisions** carry a `Why:` field that explains rationale. The `Why:` field is sacred -- it is never compressed, summarized, or paraphrased through any tier.

**Observations** are facts about what happened. They compress safely because the code still exists as the source of truth.

| Type        | Tier compression                                               | Can be auto-pruned?                                     |
|-------------|----------------------------------------------------------------|---------------------------------------------------------|
| Decision    | `What:` compresses, `Why:` survives verbatim through ALL tiers | Never. Demoted to lineage if ref 0, but `Why:` preserved |
| Observation | Compresses normally through tiers                              | Yes, demoted to lineage by ref score                     |

## Succession Protocol

Succession is triggered automatically (entry count > 30, 5+ sessions, or 60%+ stale entries) or manually via `/empire succession`. It runs in a subagent to avoid polluting the main conversation.

**What happens during succession:**

1. **Freeze** -- Snapshot current Day, Dusk, and Dawn. Record the trigger reason.
2. **Compress Dusk** -- Existing Dusk entries shift one tier down. Decisions keep their `Why:` verbatim; only `What:` compresses. Layer 3 observations with ref 0 across 3 successions demote to lineage.
3. **Day to Dusk** -- The succession agent categorizes each Day entry (not summarizes). Decisions have `Why:` preserved verbatim. Observations compress based on ref score. Score 0 entries demote to structured lineage with full original text.
4. **Dawn to Day** -- Dawn contents become the new Day. Scores reset. Dynasty counter increments.
5. **Seed new Dawn** -- Fresh Dawn seeded from git state (branch, recent commits, uncommitted changes) and keyword-matched Dusk wisdom.
6. **Vault check** -- Dusk entries referenced across 3+ successions auto-promote to Vault if space permits. If full, candidates are tagged `[vault-candidate]` quietly.
7. **Deviant check** -- Scan new Dusk entries for file-path conflicts with Vault. Auto-flag conflicts. Nudge old unresolved deviants.
8. **Ceremony** -- Generate the succession report, write lineage, assign the outgoing ruler's epithet.

The key insight: distillation is **categorization, not summarization**. The agent never rewrites or paraphrases `Why:` fields. The "telephone game" problem is eliminated for decisions and acceptable for observations.

## Hook System

**SessionStart** fires on every conversation start or resume. It detects the current git branch, finds the matching dynasty, and injects the Vault (~50 lines) plus the pre-computed Day briefing (~30 lines) into conversation context. The Ancestor Oracle then searches lineage for keyword matches and appends hints about relevant past wisdom.

**PostToolUse** fires after Read, Edit, Write, Grep, and Glob tool calls. It extracts file paths and keywords from tool input and matches them against Day entries using tiered scoring: exact file path match (+2), same directory overlap (+1), or 2+ keyword matches (+1). Scores are cached and applied in batch at session end. This hook stays under 100ms.

**Stop** fires when the conversation ends. It applies the batched reference scores, then the Session Scribe analyzes `git diff` to auto-generate new Day entries from the session's changes. It generates a compressed Day briefing for the next session, and evaluates three succession triggers:
- Day has more than 30 entries
- 5+ sessions since the last succession
- 60%+ of Day entries have a reference score of 0 (stale)

If any trigger fires, succession is noted for the next session.

**Hook principles:** Never block the user. Never prompt for input. Fail silently if state files are missing. PostToolUse stays under 100ms.

## Configuration

Empire is zero-config by default. All thresholds ship with sensible defaults that work out of the box.

Power users can hand-edit `.empire/config.md` to adjust thresholds. The file contains commented-out defaults that document every configurable value.

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
│   ├── succession-agent.md        Subagent for distillation + ceremony
│   ├── session-scribe.md          Subagent for LLM-enhanced Day entry generation
│   └── ancestor-oracle.md         Subagent for ceremonial lineage consultation
├── hooks/
│   ├── hooks.json                 Hook registrations
│   ├── session_start.py           Load Vault + briefing + ancestor hints
│   ├── post_tool_use.py           Reference tracking
│   └── stop.py                    Ref scores, scribe, briefing, pressure check
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
│   ├── scribe.py                  Session Scribe — git diff to typed entries
│   ├── oracle.py                  Ancestor Oracle — lineage search + attribution
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
