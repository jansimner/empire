# Empire: Continuous Context Protocol

## Design Document

**Date:** 2026-03-08
**Status:** Approved
**Inspiration:** The genetic dynasty succession model from Foundation (Brother Dawn/Day/Dusk)

---

## Overview

Empire is a Claude Code plugin that manages conversation context through a dynasty succession metaphor. Context has a lifecycle — it's born (Dawn), rules (Day), advises (Dusk), and eventually dies — preventing unbounded growth while preserving critical knowledge.

Each dynasty member gets a regnal name (Claude I, Claude II, ...) and earns an epithet based on their work ("the Architect", "the Debugger"). Context rotation happens automatically, driven by pressure metrics, with manual override available.

## Core Metaphor

| Foundation | Empire |
|---|---|
| Brother Dawn | Staged context — prepared, learning, not yet active |
| Brother Day | Active context — driving current decisions |
| Brother Dusk | Archived wisdom — distilled patterns and learnings |
| Succession | Context rotation — triggered by pressure or events |
| Dusk dies | Oldest wisdom pruned |
| New Dawn born | Fresh context seeded from git state + past wisdom |

## Design Decisions

### 1. State Storage (Hybrid)

- **Project directory (`.empire/`)** — Vault, protocol, config. Committed to git, shareable
- **Claude memory directory (`~/.claude/projects/<project>/empire/`)** — Dawn, Day, Dusk, deviants, lineage. Private working state

### 2. Multi-Stream Handling (Branch-Linked Dynasties)

Each git branch gets its own dynasty with separate Dawn/Day/Dusk. Switching branches switches dynasties automatically.

### 3. Session Bootstrap (Smart Briefing)

- SessionStart loads Vault (~50 lines) + pre-computed Day briefing (~30 lines)
- Total context overhead: ~80 lines per session
- Full Day/Dusk loaded on-demand only when needed
- Day briefing is pre-computed at end of previous session (Stop hook) for accuracy

### 4. Distillation (Tiered Automatic)

Reference scores track how often Day entries are used during work:
- Score >= 3 → Dusk verbatim
- Score 1-2 → Dusk compressed
- Score 0 → pruned (archived in lineage)
- Manual review available via `--review` flag

### 5. Vault Promotion (Hybrid with Cap)

- Dusk entries referenced across 3+ sessions → auto-promoted to Vault
- Vault hard cap: 50 lines
- When full: swap proposal (promote X, demote Y?) requiring user confirmation

### 6. Deviants (Both, Advisory with Nudge)

- Auto-detected (contradictions between work and Vault/Dusk) + manually flagged
- Advisory only — never block succession
- Nudge at 5 sessions unresolved, explicit resolution prompt at 10
- Resolution options: fix, update, accept as known tech debt, dismiss

### 7. Dawn Seeding (Git + Dusk Wisdom)

New Dawn seeded from:
- Git state: branch, recent commits, uncommitted changes, stash, TODOs/FIXMEs
- Dusk wisdom: keyword-matched entries relevant to current branch/files

### 8. Agent Teams (Citizens, Not Brothers)

Agents read Vault + Day briefing but don't participate in the dynasty. They report back to the main conversation, which decides what to record in Day. Simple, no merge logic.

### 9. Configuration (Zero Config v1)

All thresholds hardcoded with sensible defaults. Config file exists with commented-out defaults for power users to hand-edit. `/empire config` command deferred to v2.

---

## Architecture

### Plugin Structure

```
empire/
├── .claude-plugin/
│   └── plugin.json
├── README.md
├── commands/
│   ├── empire.md              # /empire → status dashboard
│   ├── empire-init.md         # /empire init → found dynasty
│   ├── empire-succession.md   # /empire succession → manual trigger
│   ├── empire-vault.md        # /empire vault → manage immortals
│   ├── empire-deviant.md      # /empire deviant → flag/resolve
│   ├── empire-lineage.md      # /empire lineage → view history
│   └── empire-dawn.md         # /empire dawn → view/add staged items
├── agents/
│   └── succession-agent.md    # Subagent for distillation + ceremony
├── hooks/
│   ├── hooks.json             # Hook registrations
│   ├── session_start.py       # Load Vault + briefing
│   ├── stop.py                # Ref scores, briefing, pressure, auto-succession
│   └── post_tool_use.py       # Reference tracking
└── skills/
    └── succession-protocol/
        └── SKILL.md           # Detailed succession logic
```

### Project State (`.empire/`, committed to git)

```
.empire/
├── vault.md       # Immortal context, <= 50 lines
├── protocol.md    # Dynasty rules
└── config.md      # Thresholds (commented defaults, hand-editable)
```

### Working State (`~/.claude/projects/<project>/empire/`)

```
empire/
└── dynasty/
    ├── main/
    │   ├── dawn.md
    │   ├── day.md
    │   ├── day-briefing.md
    │   ├── dusk.md
    │   └── dynasty.json
    └── feature-payments/
        ├── dawn.md
        ├── day.md
        ├── ...
        └── dynasty.json
├── deviants.md
└── lineage.md
```

---

## Hook System

### SessionStart Hook

Fires on every conversation start/resume:

1. Detect current git branch
2. Find or create dynasty directory for that branch
3. Load `.empire/vault.md`
4. Load `day-briefing.md` (compressed Day summary)
5. Inject both into conversation context
6. If branch changed since last session, log it

### Stop Hook

Fires when conversation ends:

1. Scan conversation for references to Day entries → update reference scores
2. Generate compressed `day-briefing.md` from current Day
3. Calculate succession pressure score:
   - `(day_size / max_day_size) * 0.3`
   - `(stale_entry_ratio) * 0.25`
   - `(topic_drift_estimate) * 0.2`
   - `(decision_count / threshold) * 0.15`
   - `(git_boundary_event) * 0.1`
4. If pressure > 0.7 → auto-trigger succession
5. If pressure > 0.5 → note in Dawn: "succession recommended"
6. Update dynasty.json session count

### PostToolUse Hook

Fires after Read, Edit, Write, Grep, Glob tool calls (lightweight):

1. Check if file/content relates to any Day entry
2. If match → increment reference score (batched, written at Stop)
3. Fast keyword match only — no heavy computation

### Hook Principles

- Never block the user
- Never prompt for input
- Fail silently if state files are missing
- PostToolUse stays under 100ms

---

## Succession Protocol

Triggered by: pressure > 0.7 (auto) or `/empire succession` (manual)

**Step 1: Freeze** — Snapshot current Day, Dusk, Dawn. Record trigger reason.

**Step 2: Prune Dusk** — Check reference scores across last 3 successions. Score 0 across all → pruned. Remaining entries compress one tier:
- Layer 1 (detailed, ~100 lines max) → Layer 2 (key decisions, ~50 lines max)
- Layer 2 → Layer 3 (one-liners, ~30 lines max)
- Layer 3 score 0 → pruned

**Step 3: Day → Dusk** — Succession agent spawned:
- Score >= 3 → Dusk Layer 1 verbatim
- Score 1-2 → Dusk Layer 1 compressed
- Score 0 → pruned (archived in lineage)
- Agent generates epithet from Day contents

**Step 4: Dawn → Day** — Dawn contents become new Day. Scores reset. Dynasty counter increments.

**Step 5: Seed new Dawn** — Git scan + Dusk wisdom keyword match.

**Step 6: Vault check** — Dusk entries with 3+ succession references → Vault promotion candidate. Auto-promote if space, swap proposal if full.

**Step 7: Deviant check** — Scan new Dusk against Vault for contradictions. Auto-flag. Nudge old deviants.

**Step 8: Ceremony** — Generate report, write lineage, generate new day-briefing.

Runs in a subagent to avoid polluting main conversation context.

---

## Context Budget

| Layer | Max Size | Loaded When |
|---|---|---|
| Vault | 50 lines (hard cap) | Always (SessionStart) |
| Day briefing | ~30 lines | Always (SessionStart) |
| Day (full) | Uncapped, pressure-monitored | On-demand |
| Dusk | ~180 lines across 3 tiers | On-demand |
| Dawn | Lean, ~20-30 lines | During succession only |
| Lineage | Append-only, unbounded | On-demand (`/empire lineage`) |
| Deviants | Count in briefing | On-demand (`/empire deviant`) |

**Permanent session overhead: ~80 lines.** Everything else loads only when needed.

---

## Display Format

Emoji-styled with box-drawing characters for all ceremony output.

**Status:**
```
┌─────────────────────────────────────────────────────┐
│  👑 EMPIRE STATUS                                    │
│  🌿 main · Dynasty of Claude                        │
├─────────────────────────────────────────────────────┤
│  🌅 Dawn:  Claude VII  ???         4 staged items    │
│  ☀️  Day:   Claude VI  "the Gatekeeper"  12 entries  │
│  🌙 Dusk:  Claude V   "the Debugger"    6 wisdom    │
├─────────────────────────────────────────────────────┤
│  🏛️  Vault:    46/50 lines                           │
│  ⚡ Deviants: 1 unresolved                           │
│  📊 Pressure: ▓▓▓▓▓▓░░░░ 42%                        │
│  🔄 Last succession: 2h ago                          │
└─────────────────────────────────────────────────────┘
```

**Succession ceremony:**
```
┌─────────────────────────────────────────────────────┐
│  ⚔️  SUCCESSION OF CLAUDE VI "THE GATEKEEPER"       │
│  🌿 Branch: main                                    │
├─────────────────────────────────────────────────────┤
│  💀 Claude IV "the Architect"   Dusk → pruned        │
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

**Epithet vocabulary:**

| Work Pattern | Epithet |
|---|---|
| New features | "the Builder" |
| Auth/security | "the Gatekeeper" |
| Bug fixes | "the Debugger" |
| Refactoring | "the Reformer" |
| UI/styling | "the Painter" |
| Database/migrations | "the Chronicler" |
| Tests | "the Sentinel" |
| CI/CD/infra | "the Engineer" |
| API work | "the Ambassador" |
| Documentation | "the Scribe" |
| Performance | "the Swift" |
| Mixed/general | "the Journeyman" |
| Huge output | "the Tireless" |
| Very short reign | "the Brief" |

---

## v1 Scope

**Building:**
- All 7 commands (empire, init, succession, vault, deviant, lineage, dawn)
- 3 hooks (SessionStart, Stop, PostToolUse)
- Succession agent
- Branch-linked dynasties
- Reference tracking + pressure monitoring
- Auto-succession
- Epithet generation
- Emoji ceremony reports

**Deferred to v2:**
- `/empire config` command
- GitHub integration for Dawn seeding
- Agent tributary system
- `/empire archaeology` (semantic search across pruned lineage)
- Cross-project global Vault
- Dry-run succession mode
- Pressure visualization over time
- Export/import dynasty state

**Not building (YAGNI):**
- Vector databases
- External storage backends
- Multi-user dynasty sharing
- Real-time sync
- Web dashboard
