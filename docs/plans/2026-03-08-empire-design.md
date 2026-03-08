# Empire: Continuous Context Protocol

## Design Document

**Date:** 2026-03-08
**Status:** Draft — reviewed, pending implementation validation
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
| Dusk dies | Oldest wisdom demoted to lineage (never truly deleted) |
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

### 4. Entry Types — Decisions vs Observations

Every Day entry is typed. This is the most critical design decision in Empire — it determines what can be safely compressed and what must be preserved verbatim.

**Decisions** have a `Why:` field that explains rationale. The `Why:` field is **sacred** — it NEVER gets compressed or summarized through any tier. This is a mechanical rule, not an AI judgment call.

**Observations** are facts about what happened. They compress safely because the code still exists as source of truth.

```markdown
### [ref:5] [decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.
What: Implemented in auth.service.ts using jose library

### [ref:2] [observation] Fixed rate limiter gap on health endpoint
express-rate-limit middleware now applied globally before route matching.
```

Distillation behavior by type:

| Type | Tier compression | Can be auto-pruned? |
|---|---|---|
| Decision | `What:` compresses, `Why:` survives verbatim through ALL tiers | Never. Demoted to lineage if ref 0, but `Why:` preserved |
| Observation | Compresses normally through tiers | Yes, demoted to lineage by ref score |

### 5. Distillation is Categorization, Not Summarization

The succession agent's job is NOT to summarize entries. Summarization is a lossy telephone game — each pass degrades fidelity. Instead, the agent **categorizes**:

1. Is this a decision with a "why"? → **Preserve the `Why:` verbatim.** Compress or drop the `What:`
2. Is this a factual observation? → **Compress to one-liner.** Safe to lose detail
3. Is this ephemeral work context? ("currently debugging X") → **Demote to lineage**

Reference scores still drive promotion priority:
- Score >= 3 → Dusk Layer 1 (verbatim for decisions, detailed for observations)
- Score 1-2 → Dusk Layer 1 (decisions: `Why:` verbatim + compressed `What:`. Observations: one-liner)
- Score 0 → Demoted to structured lineage (never auto-deleted)

### 6. Nothing Auto-Deletes — Only Auto-Demotes

**Context amnesia is impossible.** Nothing ever silently disappears from Empire.

```
Day entry, ref 0         → demoted to Dusk Layer 3 (not deleted)
Dusk Layer 3, ref 0 x3   → demoted to Lineage (structured, searchable)
Lineage                  → permanent, never auto-deleted
```

Lineage is not a flat log — it's a **structured searchable archive**. The AI can pull from lineage on-demand if it realizes it's missing context. Worst case is "I need to look it up", never "it's gone."

### 7. Decrees — Permanent Dusk Entries

Decisions that don't make the Vault cut but are too important to ever compress get marked as **Decrees**. Decrees are Dusk entries that:
- Never compress through tiers
- Never demote to lineage
- Count against Dusk's size budget
- Are immune to all automatic rotation

Promotion path: Decision in Dusk → referenced in 2+ sessions → auto-promoted to Decree. Decrees can be further promoted to Vault manually.

### 8. Vault Promotion (Hybrid with Cap, Quiet Overflow)

- Dusk entries referenced across 3+ sessions → auto-promoted to Vault
- Vault hard cap: 50 lines
- When full: candidate stays in Dusk Layer 1 with `[vault-candidate]` tag (quiet overflow — no interruption)
- `/empire vault` shows waiting candidates; user promotes at their own pace
- Swap prompts only appear in `/empire succession --review` mode (the explicit "I want friction" path)

### 9. Deviants (Manual + File-Path Conflicts, Advisory with Nudge)

- **v1 auto-detection limited to concrete conflicts only:** Vault references file X with pattern A, but file X was modified to use pattern B. Detectable via file path overlap without semantic understanding
- **Manual flagging** for everything else — user knows when something contradicts
- **Full semantic contradiction detection deferred to v2** (done by succession agent which can reason as an LLM)
- Advisory only — never block succession
- Nudge at 5 sessions unresolved, explicit resolution prompt at 10
- Resolution options: fix, update, accept as known tech debt, dismiss

### 10. Dawn Seeding (Git + Dusk Wisdom)

New Dawn seeded from:
- Git state: branch, recent commits, uncommitted changes, stash, TODOs/FIXMEs
- Dusk wisdom: keyword-matched entries relevant to current branch/files

### 11. Agent Teams (Citizens, Not Brothers)

Agents read Vault + Day briefing but don't participate in the dynasty. They report back to the main conversation, which decides what to record in Day. Simple, no merge logic.

### 12. Configuration (Zero Config v1)

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

1. Apply batched reference scores from PostToolUse cache → update `day.md`
2. Generate compressed `day-briefing.md` from current Day
3. Evaluate succession triggers (simple, transparent, no weighted formula):
   - Day has > 30 entries → suggest succession
   - 5+ sessions since last succession → suggest succession
   - 60%+ of Day entries have ref score 0 (stale) → suggest succession
4. If any trigger fires → note in Dawn with reason: "Succession suggested: Day has 35 entries"
5. Update dynasty.json session count

**Why no weighted formula:** Weighted pressure scores give false precision. Simple threshold triggers are transparent, debuggable, and their reasons are human-readable. Topic drift was cut from v1 — it's genuinely hard to compute cheaply and honestly.

### PostToolUse Hook

Fires after Read, Edit, Write, Grep, Glob tool calls (lightweight):

1. Extract file paths and content keywords from tool input
2. Match against Day entries using tiered scoring:
   - **Tier 1 (high confidence):** Exact file path match between tool input and paths mentioned in Day entry body → +2
   - **Tier 2 (medium confidence):** Same directory overlap → +1
   - **Tier 3 (low confidence):** 2+ keyword matches between tool context and entry title+body → +1 (single keyword overlap is ignored — too noisy)
3. If any tier matches → increment entry's reference score in cache (batched, applied at Stop)

**Why file paths are primary:** Day entries that mention specific files (e.g., "rate-limit.ts") can be reliably matched when those files are touched. Keyword matching ("auth") alone is too broad — requiring 2+ keyword matches reduces false positives while still catching relevant references.

**Safety net:** If scoring is wrong, the consequence is suboptimal Dusk placement, never data loss. Nothing is ever deleted — low-scoring entries are demoted to structured lineage and can be recovered via `/empire lineage --search`. Decisions are additionally protected: their `Why:` field survives all tiers regardless of ref score.

### Hook Principles

- Never block the user
- Never prompt for input
- Fail silently if state files are missing
- PostToolUse stays under 100ms

---

## Succession Protocol

Triggered by: succession threshold met (auto-suggested, user confirms or auto-fires next session) or `/empire succession` (manual)

**Step 1: Freeze** — Snapshot current Day, Dusk, Dawn. Record trigger reason.

**Step 2: Compress Dusk** — Existing Dusk entries shift one tier down. Decrees and `[decision]` entries with `Why:` fields are exempt from compression — only the `What:` portion compresses:
- Layer 1 (detailed) → Layer 2 (decisions: `Why:` preserved verbatim, `What:` compressed. Observations: one-liner)
- Layer 2 → Layer 3 (decisions: `Why:` still verbatim. Observations: one-liner)
- Layer 3 observations, ref 0 across 3 successions → demoted to structured lineage (never deleted)
- Decrees: immune, stay in place

**Step 3: Day → Dusk** — Succession agent spawned. Agent **categorizes** (not summarizes):
- For each Day entry, determine type: `[decision]` or `[observation]`
- Decisions: `Why:` field preserved verbatim into Dusk. `What:` compressed based on ref score
- Observations: compressed based on ref score (>= 3 detailed, 1-2 one-liner, 0 demoted to lineage)
- Score 0 entries → demoted to structured lineage with full original text
- Agent generates epithet from Day contents

**Step 4: Dawn → Day** — Dawn contents become new Day. Scores reset. Dynasty counter increments.

**Step 5: Seed new Dawn** — Git scan + Dusk wisdom keyword match.

**Step 6: Vault check** — Dusk entries with 3+ succession references → Vault promotion candidate. Auto-promote if space. If full, tag entry as `[vault-candidate]` in Dusk (quiet overflow, no interruption).

**Step 7: Deviant check** — Scan new Dusk entries for file-path conflicts with Vault (concrete only, no semantic matching in v1). Auto-flag conflicts. Nudge old deviants.

**Step 8: Ceremony** — Generate report, write lineage, generate new day-briefing.

Runs in a subagent to avoid polluting main conversation context.

---

## Context Budget

| Layer | Max Size | Loaded When |
|---|---|---|
| Vault | 50 lines (hard cap) | Always (SessionStart) |
| Day briefing | ~30 lines | Always (SessionStart) |
| Day (full) | Uncapped, trigger-monitored | On-demand |
| Dusk | ~180 lines across 3 tiers + decrees | On-demand |
| Decrees | Part of Dusk budget, immune to compression | On-demand (with Dusk) |
| Dawn | Lean, ~20-30 lines | During succession only |
| Lineage | Structured archive, append-only, unbounded | On-demand (`/empire lineage --search`) |
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
- Succession agent with categorization-based distillation (not summarization)
- Typed entries: `[decision]` (with sacred `Why:` field) vs `[observation]`
- Decrees: permanent Dusk entries immune to compression
- Demotion-only lifecycle: nothing auto-deletes, structured searchable lineage
- Branch-linked dynasties
- Reference tracking (file-path primary, keyword secondary with 2+ match threshold)
- Simple succession triggers (entry count, session count, staleness ratio)
- Epithet generation
- Emoji ceremony reports

**Deferred to v2:**
- `/empire config` command
- GitHub integration for Dawn seeding
- Agent tributary system
- `/empire archaeology` (semantic search across pruned lineage)
- Cross-project global Vault
- Dry-run succession mode
- Semantic deviant auto-detection (LLM-powered contradiction analysis)
- Topic drift detection
- Weighted pressure formula (if simple triggers prove insufficient)
- Optional portable state in `.empire/state/` for multi-machine sync
- Export/import dynasty state

**Not building (YAGNI):**
- Vector databases
- External storage backends
- Multi-user dynasty sharing
- Real-time sync
- Web dashboard

---

## Known Limitations & Risks

### Reference Scoring (mitigated risk)
PostToolUse keyword matching to infer whether a Day entry was "actively used" is imprecise. File path matching is reliable; keyword matching is noisy. Multiple safety nets ensure scoring errors are non-destructive:
- **Nothing auto-deletes.** Low-scoring entries are demoted to structured lineage, never deleted
- **Decisions are doubly protected.** The `Why:` field survives all tiers regardless of ref score
- **Lineage is searchable.** If the AI realizes it's missing context, it can look it up
- **Decrees escape scoring entirely.** Important decisions can be marked immune to all rotation

Worst case with bad scoring: an entry ends up in lineage when it should have stayed in Dusk. The AI needs a lookup step to find it. This is "context with a lookup" not "context amnesia."

### Distillation Quality (mitigated by categorization)
Distillation is categorization (decision vs observation), not summarization. The agent never rewrites or paraphrases `Why:` fields — they're copied verbatim through all tiers. Observations compress safely because the code still exists. The "telephone game" problem is eliminated for decisions and acceptable for observations.

### Multi-Machine State
Working state lives in `~/.claude/projects/` which doesn't sync across machines. If you work from multiple machines, each maintains an independent dynasty. v2 will offer optional committed state for portability.

### Deviant Detection
v1 auto-detection is limited to concrete file-path conflicts. Semantic contradictions ("Vault says REST-only but you just wrote a GraphQL resolver") require LLM reasoning, deferred to v2. Manual flagging covers the gap.
