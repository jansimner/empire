---
name: succession-protocol
description: Detailed reference for Empire's 8-step succession protocol
---

# Succession Protocol — Reference

This skill documents the complete succession algorithm for the Empire dynasty system. The succession protocol rotates context: Day wisdom becomes Dusk, Dawn is promoted to Day, and a new Dawn is seeded from git state and Dusk wisdom.

## Overview

Succession is triggered either automatically (by threshold triggers evaluated in the Stop hook) or manually (via `/empire succession`). It always runs in a subagent to avoid polluting main conversation context.

The protocol has 8 steps executed in strict order:

1. **Freeze** — snapshot current state
2. **Compress Dusk** — shift existing Dusk entries down one tier
3. **Day to Dusk** — categorize Day entries into Dusk Layer 1
4. **Dawn to Day** — promote Dawn to active Day
5. **Seed new Dawn** — create fresh Dawn from git + Dusk wisdom
6. **Vault check** — promote worthy entries to Vault
7. **Deviant check** — scan for conflicts with Vault
8. **Ceremony** — generate report, write all files

---

## The Sacred Rule

The `Why:` field on `[decision]` entries is **NEVER** compressed, summarized, or paraphrased. It is copied verbatim through every tier transition, every time. This is a mechanical rule, not an AI judgment call.

This is the single most important invariant in the entire system.

---

## Entry Types

### `[decision]`
Decisions have two fields:
- **`Why:`** — the rationale. Sacred. Preserved verbatim through all tiers and into lineage.
- **`What:`** — the implementation detail. Compresses safely because the code still exists.

```markdown
### [ref:5] [decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.
What: Implemented in auth.service.ts using jose library
```

### `[observation]`
Observations are factual records of what happened. They compress safely through all tiers.

```markdown
### [ref:2] [observation] Fixed rate limiter gap on health endpoint
express-rate-limit middleware now applied globally before route matching.
```

### `[decree]`
Decrees are Dusk entries marked as permanent. They are:
- Immune to tier compression (never shift down)
- Immune to demotion to lineage
- Count against Dusk's size budget
- Created by auto-promotion: decisions referenced in 2+ sessions become Decrees

---

## Step-by-Step Protocol

### Step 1: Freeze

Read all state files:

| File | Location | Purpose |
|------|----------|---------|
| `day.md` | `<dynasty_dir>/` | Current active entries |
| `dusk.md` | `<dynasty_dir>/` | Tiered wisdom archive |
| `dawn.md` | `<dynasty_dir>/` | Staged context for next Day |
| `dynasty.json` | `<dynasty_dir>/` | Dynasty metadata |
| `day-briefing.md` | `<dynasty_dir>/` | Current briefing |
| `vault.md` | `<project_root>/.empire/` | Immortal context |
| `deviants.md` | `<memory_dir>/` | Conflict flags |
| `lineage.md` | `<memory_dir>/` | Structured archive |

Record the trigger reason (e.g., "Day has >30 entries (35)", "manual trigger").

Path resolution uses `core/paths.py`:
- `get_project_root()` — finds `.empire/` directory
- `get_current_branch()` — runs `git rev-parse --abbrev-ref HEAD`
- `get_dynasty_dir(branch)` — computes `~/.claude/projects/<project-key>/empire/dynasty/<branch>/`
- `get_memory_dir()` — computes `~/.claude/projects/<project-key>/empire/`

### Step 2: Compress Dusk

Shift existing Dusk entries down one tier. **Decrees are skipped entirely.**

#### Layer 1 → Layer 2

| Entry Type | Compression |
|------------|-------------|
| `[decision]` | `Why:` preserved verbatim. `What:` compressed to one-liner. |
| `[observation]` | Compressed to one-liner. |

Format change: Layer 1 uses `### [ref:N]` multi-line format. Layer 2 uses `- [ref:N]` single-line format.

**Layer 2 decision format:** `- [ref:N] [decision] <compressed-what> — Why: <verbatim-why>`
**Layer 2 observation format:** `- [ref:N] [observation] <one-liner>`

#### Layer 2 → Layer 3

Same compression rules. Decisions keep `Why:` inline. Format stays as `- [ref:N]` list items.

#### Layer 3 — Demote or Keep

| Condition | Action |
|-----------|--------|
| `[observation]`, ref 0, in Layer 3 for 3+ successions | Demote to lineage |
| `[decision]`, ref 0, in Layer 3 for 3+ successions | Demote to lineage (Why: preserved) |
| All others | Keep in Layer 3 |

The "3+ successions" count is tracked by comparing the entry's dynasty number against the current dynasty counter in `dynasty.json`.

#### Dusk file format

```markdown
# 🌙 Dusk — Claude <N> "<epithet>"

## Layer 1 (detailed)
### [ref:5] [decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.
What: Implemented in auth.service.ts using jose library

### [ref:3] [observation] Rate limiter applied globally
express-rate-limit middleware applied before route matching. Health endpoint
no longer bypasses rate limiting.

## Layer 2 (compressed)
- [ref:2] [decision] Used Prisma over TypeORM — Why: Type-safe queries with zero runtime overhead
- [ref:1] [observation] Redis caching added for session store

## Layer 3 (one-liners)
- [ref:0] [decision] REST over GraphQL for v1 — Why: Team expertise and simpler debugging
- [ref:0] [observation] Configured ESLint flat config
```

#### Dusk size limits (from `core/constants.py`)

| Layer | Max Lines |
|-------|-----------|
| Layer 1 | 100 |
| Layer 2 | 50 |
| Layer 3 | 30 |

If a layer exceeds its limit after compression, the lowest-ref entries are demoted to the next layer (or to lineage from Layer 3).

### Step 3: Day to Dusk — Categorization

**This is categorization, NOT summarization.** The agent determines entry type and placement tier. It does not rewrite content through a telephone game.

#### Placement by ref score

| Type | Ref >= 3 | Ref 1-2 | Ref 0 |
|------|----------|---------|-------|
| `[decision]` | Layer 1: `Why:` verbatim, `What:` detailed | Layer 1: `Why:` verbatim, `What:` one-liner | Demote to lineage (`Why:` preserved) |
| `[observation]` | Layer 1: detailed description | Layer 1: one-liner | Demote to lineage |

#### Epithet generation

Score outgoing Day entries against keyword lists to determine the epithet for the outgoing ruler.

**Keyword map** (from `core/constants.py` `EPITHET_KEYWORDS`):

| Epithet | Keywords |
|---------|----------|
| "the Builder" | feature, add, create, new, implement, build |
| "the Gatekeeper" | auth, security, permission, token, jwt, csrf, cors |
| "the Debugger" | fix, bug, debug, error, issue, patch, resolve |
| "the Reformer" | refactor, rename, restructure, clean, simplify, extract |
| "the Painter" | ui, css, style, layout, component, design, theme |
| "the Chronicler" | database, migration, schema, prisma, sql, model |
| "the Sentinel" | test, spec, assert, coverage, vitest, jest, playwright |
| "the Engineer" | ci, cd, deploy, docker, pipeline, infra, config |
| "the Ambassador" | api, endpoint, route, controller, rest, graphql |
| "the Scribe" | doc, readme, comment, jsdoc, typedoc |
| "the Swift" | performance, optimize, cache, speed, lazy, bundle |

**Algorithm:**
1. For each epithet, count keyword occurrences across all Day entry titles and bodies (case-insensitive substring match)
2. No keywords match any entries → **"the Journeyman"**
3. Three or more epithets tie for highest score → **"the Journeyman"**
4. Zero entries in Day → **"the Brief"**
5. Otherwise → **highest-scoring epithet wins** (first in tie if only 2 tie)

Can be computed via `core/entries.py`:
```python
from core.entries import generate_epithet, parse_day_entries
epithet = generate_epithet(parse_day_entries(day_content))
```

### Step 4: Dawn to Day

1. Read `dawn.md` contents
2. Create new `day.md` with Dawn content reformatted as Day entries
3. All ref scores reset to 0
4. New Day header: `# ☀️ Day — Claude <N+1>`
5. Metadata comment: `<!-- Branch: <branch> | Born: <ISO timestamp> -->`

Update `dynasty.json`:
- `current` → incremented by 1
- `last_succession` → current ISO timestamp
- `sessions_since_succession` → 0
- `epithets["Claude <N>"]` → the outgoing Day's earned epithet

### Step 5: Seed New Dawn

#### Git state gathering

Run these commands:
```bash
git log --oneline -5        # Recent commits
git status --short           # Uncommitted changes
git branch --show-current    # Current branch
```

#### Dusk wisdom matching

Keyword-match the current branch name and any modified files (from `git status --short`) against Dusk entries. Include matching entries in Dawn's "Dusk Wisdom" section.

#### Dawn format

```markdown
# 🌅 Dawn — Claude <N+2>
<!-- Staged for next succession -->

## Git State
- Branch: <branch>
- Recent commits:
  - <hash> <message>
  - <hash> <message>
  - ...
- Uncommitted changes: <yes/no with summary>

## Dusk Wisdom
<!-- Keyword-matched entries from Dusk relevant to current work -->
- <matched entry 1>
- <matched entry 2>
```

### Step 6: Vault Check

Scan Dusk entries referenced across 3+ successions for Vault promotion.

| Condition | Action |
|-----------|--------|
| Entry qualifies AND vault < 50 lines | Auto-promote: append to `vault.md` as concise bullet |
| Entry qualifies AND vault >= 50 lines | Tag entry as `[vault-candidate]` in Dusk (quiet overflow) |

**Constants:**
- `VAULT_MAX_LINES = 50` (hard cap)
- `VAULT_PROMOTION_SESSIONS = 3` (minimum successions referenced)

Never remove existing vault entries. Never prompt the user about vault overflow — it's quiet by design. The `/empire vault` command shows candidates for manual promotion.

### Step 7: Deviant Check

#### Auto-detection (v1: file-path conflicts only)

For each new Dusk entry that mentions file paths:
1. Extract file paths from the Dusk entry body/title
2. Extract file paths from `vault.md`
3. If the same file is referenced in both Vault and new Dusk with different patterns/behaviors → flag as deviant

**No semantic analysis in v1.** Only concrete file-path overlap triggers auto-detection. Semantic contradiction detection (e.g., "Vault says REST-only but Dusk mentions GraphQL resolver") is deferred to v2.

#### Deviant entry format in `deviants.md`

```markdown
### [deviant] <description>
Filed: <ISO date>
Session: 1
Vault ref: <which vault entry conflicts>
Dusk ref: <which dusk entry conflicts>
Status: unresolved
```

#### Nudging old deviants

| Session Count | Action |
|---------------|--------|
| >= 5 | Add nudge: `⚠️ Deviant unresolved for 5+ sessions` |
| >= 10 | Add resolution prompt: `🚨 Deviant unresolved for 10+ sessions — consider resolving` |

**Constants:**
- `DEVIANT_NUDGE_SESSIONS = 5`
- `DEVIANT_RESOLVE_SESSIONS = 10`

Resolution options (handled by `/empire deviant` command, not during succession):
- Fix the code to match Vault
- Update Vault to match new reality
- Accept as known tech debt
- Dismiss the deviant

### Step 8: Ceremony

#### Files written

| File | Action |
|------|--------|
| `dusk.md` | Rewritten with compressed old entries + new entries from Day |
| `day.md` | Rewritten with promoted Dawn content |
| `dawn.md` | Rewritten with new git-seeded Dawn |
| `dynasty.json` | Updated metadata (counter, epithet, timestamp) |
| `lineage.md` | Appended with demoted entries (never overwritten) |
| `day-briefing.md` | Regenerated for new Day |
| `deviants.md` | Updated if new deviants or nudges |
| `vault.md` | Updated if vault promotions |

#### Ceremony report format

```
┌─────────────────────────────────────────────────────┐
│  ⚔️  SUCCESSION OF CLAUDE <N+1> "<OUTGOING EPITHET>" │
│  🌿 Branch: <branch>                                │
├─────────────────────────────────────────────────────┤
│  💀 Claude <N-2> "<epithet>"   Dusk → lineage        │
│  🌙 Claude <N>  "<epithet>"   Day  → Dusk           │
│  ☀️  Claude <N+1>              Dawn → Day             │
│  🌅 Claude <N+2>                   → born as Dawn    │
├─────────────────────────────────────────────────────┤
│  🏛️  Vault:    [████████████░░░░] <used>/50          │
│  ⚡ Deviants: <count> unresolved (session <max>/10)  │
├─────────────────────────────────────────────────────┤
│  👑 Long live Claude <N+1>. May they earn their name.│
└─────────────────────────────────────────────────────┘
```

**Title line:** "SUCCESSION OF" names the new Day ruler (promoted from Dawn). The epithet in the title is the **outgoing Day's** earned epithet (they earned it; the new Day hasn't yet).

**Vault progress bar:** 16 characters total. `█` for filled, `░` for empty. Example: 46/50 = `[██████████████░░]`.

Calculation: `filled = round(vault_lines / 50 * 16)`, `empty = 16 - filled`.

**Dead line (💀):** Only shown if entries were actually demoted from Dusk Layer 3 to lineage during this succession. Omit if no demotions occurred (e.g., first succession).

**Deviants line:** If 0 deviants, show `⚡ Deviants: none`. Otherwise show count and the highest session number: `⚡ Deviants: 2 unresolved (session 7/10)`.

---

## Constants Reference

All constants are defined in `core/constants.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `VAULT_MAX_LINES` | 50 | Hard cap on vault size |
| `VAULT_PROMOTION_SESSIONS` | 3 | Minimum successions for vault candidacy |
| `DEVIANT_NUDGE_SESSIONS` | 5 | Sessions before nudge |
| `DEVIANT_RESOLVE_SESSIONS` | 10 | Sessions before explicit resolution prompt |
| `DUSK_LAYER1_MAX` | 100 | Max lines for Layer 1 |
| `DUSK_LAYER2_MAX` | 50 | Max lines for Layer 2 |
| `DUSK_LAYER3_MAX` | 30 | Max lines for Layer 3 |
| `DAY_ENTRY_LIMIT` | 30 | Succession trigger: Day entry count |
| `SESSIONS_BEFORE_SUCCESSION` | 5 | Succession trigger: session count |
| `STALE_RATIO_THRESHOLD` | 0.6 | Succession trigger: stale entry percentage |
| `REF_TIER1_SCORE` | 2 | Exact file path match score |
| `REF_TIER2_SCORE` | 1 | Directory overlap score |
| `REF_TIER3_SCORE` | 1 | 2+ keyword match score |
| `REF_TIER3_MIN_KEYWORDS` | 2 | Minimum keyword overlap for tier 3 |

---

## Succession Triggers

Evaluated in the Stop hook (`hooks/stop.py`). Simple, transparent, no weighted formula.

| Trigger | Condition | Reason String |
|---------|-----------|---------------|
| Entry count | `len(entries) > 30` | "Day has >30 entries (N)" |
| Session count | `sessions_since_succession >= 5` | "N sessions since last succession" |
| Staleness | `stale_entries / total_entries >= 0.6` | "N% of entries are stale (stale/total)" |

If any trigger fires, the Stop hook notes it in Dawn: `Succession suggested: <reason>`. The next session's SessionStart hook will surface this suggestion. The user confirms or it auto-fires the following session.

Manual trigger via `/empire succession` always proceeds regardless of trigger status.

---

## Lineage Format

Lineage is a structured, append-only archive. Entries are never deleted from lineage.

```markdown
# 📜 Lineage

## Dynasty of Claude — <branch>

### [dynasty:3] [decision] Chose JWT RS256 over HS256
Demoted: 2026-03-08T14:30:00Z
Original ref: 0
Why: Auth service needs asymmetric verification across microservices.
     HS256 requires shared secret which breaks zero-trust boundary.

### [dynasty:3] [observation] Configured ESLint flat config
Demoted: 2026-03-08T14:30:00Z
Original ref: 0
Migrated from .eslintrc to eslint.config.js for ESLint v9 compatibility.
```

Key properties:
- **`[dynasty:N]`** tags which dynasty the entry belonged to
- **Decisions preserve `Why:`** even in lineage
- **Full original body** is preserved (not compressed)
- **Searchable** via `/empire lineage --search <term>`
- **Never auto-deleted** — lineage is permanent

---

## Decree Rules

Decrees are Dusk entries immune to all automatic operations:

1. **Never compressed** — a decree in Layer 1 stays in Layer 1 exactly as-is
2. **Never demoted** — a decree never moves to lineage regardless of ref score
3. **Count against Dusk size budget** — they consume space in the layer they occupy
4. **Auto-created** — decisions referenced in 2+ sessions are auto-promoted to decree status
5. **Can be vault-promoted** — user can manually promote a decree to Vault via `/empire vault`

Decree entries are marked with `[decree]` in their header:
```markdown
### [ref:8] [decree] [decision] Authentication uses JWT RS256
Why: Auth service needs asymmetric verification across microservices.
```

During Step 2 (Compress Dusk), any entry with `[decree]` in its header is **skipped entirely**.
