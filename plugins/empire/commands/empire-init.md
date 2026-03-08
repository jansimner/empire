---
name: empire-init
description: Found a new dynasty for the current project
---

# /empire init — Found a New Dynasty

You are the founding ceremony master. When the user runs `/empire init`, execute the following steps exactly.

## Step 1: Check for Existing Empire

Check if a `.empire/` directory already exists in the project root.

If it does, print:

```
⚠️  Empire already founded in this project.
Run /empire to see current status.
```

Then stop. Do not proceed further.

## Step 2: Detect Current Git Branch

Run `git rev-parse --abbrev-ref HEAD` to get the current branch name. If git is not available or fails, default to `"main"`.

## Step 3: Create `.empire/` Directory Structure

Create the `.empire/` directory in the project root.

### 3a: Create `.empire/vault.md`

Auto-detect project information by scanning for project manifest files. Check for these files in the project root and extract info:

- **package.json** → extract `name`, and notable dependencies (frameworks like next, nest, express, react, vue, angular, fastify, etc.)
- **Cargo.toml** → extract `[package] name` and key dependencies
- **pyproject.toml** → extract `[project] name` or `[tool.poetry] name` and key dependencies
- **go.mod** → extract module name

Format the vault as concise bullet points. Keep it lean — this counts against the 50-line hard cap.

```markdown
# 🏛️ Vault

## Project
- Name: <detected-name>
- Stack: <detected frameworks/languages>
- Key deps: <notable dependencies, comma-separated>

## Architecture
<!-- Add immortal context here as you learn the codebase -->
```

If no manifest files are found, create a minimal vault:

```markdown
# 🏛️ Vault

## Project
- Name: <directory name>
- Stack: unknown — update as you explore

## Architecture
<!-- Add immortal context here as you learn the codebase -->
```

### 3b: Create `.empire/protocol.md`

Write the dynasty rules summary:

```markdown
# 📜 Protocol

## Entry Types
- **[decision]** — has a sacred `Why:` field that NEVER gets compressed or summarized through any tier
- **[observation]** — factual record of what happened, compresses safely through tiers

## Lifecycle
- Nothing auto-deletes. Entries demote: Day → Dusk tiers → lineage
- Lineage is structured and searchable — context is never truly lost

## Vault
- Immortal context, 50-line hard cap
- Dusk entries referenced across 3+ sessions auto-promote (if space)

## Succession Triggers
- Day has >30 entries
- 5+ sessions since last succession
- 60%+ of Day entries have ref score 0 (stale)

## Decrees
- Permanent Dusk entries immune to compression and demotion
- Decisions referenced in 2+ sessions auto-promoted to Decree
```

### 3c: Create `.empire/config.md`

Write commented-out defaults showing all thresholds:

```markdown
# ⚙️ Config

<!-- All values below are defaults. Uncomment and change to override. -->
<!-- /empire config command coming in v2. For now, hand-edit this file. -->

<!-- ## Vault -->
<!-- vault_max_lines: 50 -->
<!-- vault_promotion_sessions: 3 -->

<!-- ## Succession Triggers -->
<!-- day_entry_limit: 30 -->
<!-- sessions_before_succession: 5 -->
<!-- stale_ratio_threshold: 0.6 -->

<!-- ## Dusk Layer Limits -->
<!-- dusk_layer1_max: 100 -->
<!-- dusk_layer2_max: 50 -->
<!-- dusk_layer3_max: 30 -->

<!-- ## Deviants -->
<!-- deviant_nudge_sessions: 5 -->
<!-- deviant_resolve_sessions: 10 -->

<!-- ## Reference Scoring -->
<!-- ref_tier1_score: 2 -->
<!-- ref_tier2_score: 1 -->
<!-- ref_tier3_score: 1 -->
<!-- ref_tier3_min_keywords: 2 -->
```

## Step 4: Create Dynasty Working State

Run the founding script to create private dynasty files. This is a single command — do not skip it:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/found_dynasty.py
```

This creates `dynasty.json`, `day.md`, `dawn.md`, `dusk.md`, and `day-briefing.md` in the private dynasty directory (`~/.claude/projects/<project>/empire/dynasty/<branch>/`). The script auto-detects the branch and git state. It is idempotent — safe to run multiple times.

**You MUST run this command before proceeding to Step 5.** Verify it prints "Dynasty state created at:" before continuing.

## Step 5: Print Founding Ceremony

Display the founding ceremony using box-drawing characters and emojis exactly in this format:

```
┌─────────────────────────────────────────────────┐
│  👑 DYNASTY FOUNDED                              │
│  🌿 Branch: <branch>                            │
├─────────────────────────────────────────────────┤
│  ☀️  Claude I                → born as Day        │
│  🌅 Claude II               → born as Dawn       │
├─────────────────────────────────────────────────┤
│  🏛️  Vault: auto-detected from project files     │
│  📜 Protocol: written to .empire/protocol.md     │
├─────────────────────────────────────────────────┤
│  👑 Long live Claude I. May they earn their name.│
└─────────────────────────────────────────────────┘
```

Replace `<branch>` with the actual branch name. If vault was auto-detected from a manifest file, keep "auto-detected from project files". If no manifest was found, say "initialized with project defaults".

## Step 6: Stage and Commit

Stage the `.empire/` directory and commit it to git:

```bash
git add .empire/
git commit -m "feat: found Empire dynasty

Initialize .empire/ with vault, protocol, and config.
Dynasty founded on branch <branch> with Claude I as Day."
```

If git add or commit fails (e.g., not a git repo), print a warning but don't fail the init — the empire state is still valid.

## Important Notes

- The `.empire/` directory (vault.md, protocol.md, config.md) is committed to git — it's shared project context
- The dynasty directory (`~/.claude/projects/<project>/empire/dynasty/<branch>/`) is private working state — never committed
- Use `core/paths.py` functions (`get_dynasty_dir`, `get_current_branch`, `sanitize_branch_name`) to compute the correct dynasty directory path
- Use `core/state.py` functions (`ensure_dynasty_dir`, `write_dynasty_json`) to write state safely
