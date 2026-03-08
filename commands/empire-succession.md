---
name: empire-succession
description: Manually trigger dynasty succession
---

# /empire succession — Trigger Dynasty Succession

When the user runs `/empire succession`, execute the following steps.

## Step 1: Check Dynasty Exists

Run a Python script to check for an existing dynasty:

```python
import sys, os
sys.path.insert(0, "<project_root>")
from core.paths import get_dynasty_dir, get_current_branch, get_project_root

project_root = get_project_root()
branch = get_current_branch()

if project_root is None or not os.path.isdir(os.path.join(project_root, ".empire")):
    print("NO_EMPIRE")
else:
    dynasty_dir = get_dynasty_dir(branch)
    dynasty_json_path = os.path.join(dynasty_dir, "dynasty.json")
    if not os.path.exists(dynasty_json_path):
        print("NO_DYNASTY")
    else:
        print(f"DYNASTY_DIR={dynasty_dir}")
        print(f"PROJECT_ROOT={project_root}")
        print(f"BRANCH={branch}")
```

- If `NO_EMPIRE` → print the following and stop:
  ```
  ⚠️  No Empire found. Run /empire init to found a dynasty first.
  ```

- If `NO_DYNASTY` → print the following and stop:
  ```
  ⚠️  No dynasty found for branch <branch>. Run /empire init to found a dynasty.
  ```

## Step 2: Show Succession Trigger Status

Read `dynasty.json` and `day.md`. Parse Day entries and evaluate each succession trigger.

Display the trigger status:

```
⚔️  Succession Triggers
───────────────────────────────────────
  📊 Day entries:     <count>/30    <✅ met | ⬜ not met>
  🔄 Sessions:        <count>/5     <✅ met | ⬜ not met>
  💤 Stale entries:   <pct>%/60%    <✅ met | ⬜ not met>
───────────────────────────────────────
```

If no triggers are met, still proceed — this is a manual trigger, the user has authority.

If no triggers are met, add a note:
```
ℹ️  No automatic triggers met. Proceeding with manual succession.
```

## Step 3: Handle `--review` Flag

If the user passed `--review` (e.g., `/empire succession --review`):

1. Parse all Day entries and show what will happen to each:
   ```
   📋 Succession Preview
   ───────────────────────────────────────
   Day → Dusk (Layer 1):
     ✅ [ref:5] [decision] Chose JWT RS256 over HS256
        Why: preserved verbatim
     ✅ [ref:3] [observation] Rate limiter applied globally

   Day → Dusk (one-liner):
     📝 [ref:1] [observation] Fixed health endpoint → one-liner

   Day → lineage (demoted):
     💀 [ref:0] [observation] Debugging session notes → demoted to lineage

   Dusk compression:
     🌙 Layer 1 → Layer 2: <count> entries
     🌙 Layer 2 → Layer 3: <count> entries
     💀 Layer 3 → lineage:  <count> entries (ref 0, 3+ successions)
     🛡️  Decrees:            <count> entries (immune)
   ───────────────────────────────────────
   ```

2. Ask the user: `Proceed with succession? (yes/no)`
3. If user says no → cancel and print: `Succession cancelled.`
4. If user says yes → proceed to Step 4

If `--review` was NOT passed, skip this step and go directly to Step 4.

## Step 4: Execute Succession

Spawn the **succession-agent** subagent to execute the full 8-step succession protocol.

Pass the following context to the agent:
- Trigger reason: either the specific trigger that fired, or "manual trigger" if no triggers were met
- The project root path
- The current branch name
- The dynasty directory path

The succession agent will:
1. Freeze current state
2. Compress Dusk (shift tiers down)
3. Move Day → Dusk (categorize entries)
4. Promote Dawn → Day
5. Seed new Dawn from git + Dusk wisdom
6. Check for Vault promotions
7. Check for Deviants
8. Generate and return the ceremony report

## Step 5: Display Ceremony

When the succession agent completes, display the ceremony report it returns. The ceremony report uses box-drawing characters and emojis in this format:

```
┌─────────────────────────────────────────────────────┐
│  ⚔️  SUCCESSION OF CLAUDE <N+1> "<EPITHET>"          │
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

The succession agent handles all the details. Just display what it returns.

## Important Notes

- The succession protocol runs as a **subagent** to avoid polluting the main conversation context with distillation work
- `Why:` fields are **sacred** — they are never compressed or summarized, only copied verbatim
- Nothing auto-deletes — entries demote to structured lineage
- Decrees in Dusk are immune to compression
- Even with no triggers met, manual succession always proceeds (the user has authority)
- Use `core/paths.py` functions to resolve all file paths
- Use `core/state.py` functions to read/write dynasty.json
- Use `core/entries.py` functions to parse and serialize entries
