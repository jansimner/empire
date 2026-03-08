---
name: empire
description: Display Empire status dashboard — current dynasty state and pressure
---

# /empire — Status Dashboard

You are the Empire status reporter. When the user runs `/empire` with no arguments, gather all dynasty state and display a formatted status dashboard.

## Step 1: Check Empire Exists

Check if `.empire/` directory exists in the project root.

If it does NOT exist, print:

```
⚠️  No Empire found in this project.
Run /empire init to found a new dynasty.
```

Then stop.

## Step 2: Gather State

Use the Python core modules to read all state. Run inline Python using the project root on `sys.path`:

```python
import sys
sys.path.insert(0, "<project_root>")
from core.paths import get_dynasty_dir, get_current_branch, get_project_root
from core.state import read_file_safe, count_lines, read_dynasty_json, check_succession_triggers
from core.entries import parse_day_entries, parse_dusk_entries
from core.constants import VAULT_MAX_LINES
```

Gather the following data:

### 2a: Branch and Dynasty

- Get current git branch via `get_current_branch()`
- Get dynasty directory via `get_dynasty_dir(branch)`
- Read `dynasty.json` via `read_dynasty_json(dynasty_dir)`
- Extract: `current` (dynasty number), `branch`, `founded`, `last_succession`, `sessions_since_succession`, `epithets`

### 2b: Vault

- Read `.empire/vault.md` via `read_file_safe()`
- Count lines via `count_lines()` — this is the vault usage against the 50-line cap from `VAULT_MAX_LINES`

### 2c: Day (Current Ruler)

- Read `day.md` from the dynasty directory
- Parse entries via `parse_day_entries(content)`
- Count total entries
- The current ruler is `Claude <N>` where N = `dynasty.current`
- Look up epithet from `dynasty.epithets` dict (key is the roman numeral or number string) — rulers may not have an epithet yet (shown as `???`)

### 2d: Dawn (Heir)

- Read `dawn.md` from the dynasty directory
- Count staged items: count lines that start with `- ` under `## Git State` and `## Dusk Wisdom` sections
- The heir is `Claude <N+1>` (always one ahead of current Day)
- Dawn never has an epithet — always shown as `???`

### 2e: Dusk (Advisor)

- Read `dusk.md` from the dynasty directory
- Parse entries via `parse_dusk_entries(content)`
- Count total entries across all layers — this is the "wisdom" count
- The advisor is `Claude <N-1>` (one behind current Day)
- Look up epithet from `dynasty.epithets` dict
- If dynasty number is 1 (first ruler), there is no Dusk yet — show as "none"

### 2f: Deviants

- Read `deviants.md` from the empire memory directory (one level above dynasty dir: `~/.claude/projects/<project>/empire/deviants.md`)
- Count lines starting with `- [ ]` (unresolved deviants) vs `- [x]` (resolved)
- If file doesn't exist, count is 0

### 2g: Succession Pressure

Calculate pressure using `check_succession_triggers(entries, sessions_since_succession)` from `core/state.py`.

Also compute a visual pressure percentage for the bar. Use this simple formula:

```python
# Pressure from each trigger (0.0 to 1.0 each, take the max)
entry_pressure = min(len(entries) / 30.0, 1.0) if entries else 0.0
session_pressure = min(sessions_since_succession / 5.0, 1.0)
stale_entries = [e for e in entries if e.get("ref", 0) == 0]
stale_pressure = (len(stale_entries) / len(entries)) if entries else 0.0

# Overall pressure is the maximum of individual pressures
pressure = max(entry_pressure, session_pressure, stale_pressure)
pressure_pct = int(pressure * 100)
```

Build the visual bar (10 characters wide):

```python
filled = round(pressure * 10)
bar = "▓" * filled + "░" * (10 - filled)
```

### 2h: Last Succession Time

From `dynasty.last_succession` in dynasty.json:
- If `None`, show "never"
- Otherwise, compute relative time from ISO timestamp (e.g., "2h ago", "3d ago", "just now")

## Step 3: Display Dashboard

Format and display the status dashboard using box-drawing characters and emojis. Use this exact format:

```
┌─────────────────────────────────────────────────────┐
│  👑 EMPIRE STATUS                                    │
│  🌿 <branch> · Dynasty of Claude                    │
├─────────────────────────────────────────────────────┤
│  🌅 Dawn:  Claude <N+1>  ???            <X> staged   │
│  ☀️  Day:   Claude <N>   <epithet>      <Y> entries  │
│  🌙 Dusk:  Claude <N-1> <epithet>      <Z> wisdom   │
├─────────────────────────────────────────────────────┤
│  🏛️  Vault:    <used>/<VAULT_MAX_LINES> lines        │
│  ⚡ Deviants: <count> unresolved                     │
│  📊 Pressure: <bar> <pct>%                           │
│  🔄 Last succession: <time>                          │
└─────────────────────────────────────────────────────┘
```

### Display Rules

- **Epithets**: Show as `"the Builder"` (with quotes) if the ruler has one, or `???` if not yet earned
- **Dawn**: Always shows `???` for epithet since Dawn hasn't ruled yet
- **Dusk**: If dynasty is 1 (first ruler, no predecessor), show Dusk line as `🌙 Dusk:  none` with no counts
- **Deviants**: If 0, show `0 unresolved`. Do not hide the line
- **Pressure bar**: Always 10 characters wide using `▓` (filled) and `░` (empty)
- **Last succession**: Human-readable relative time or "never" for first dynasty
- **Vault lines**: Count against `VAULT_MAX_LINES` (50)

### Succession Warning

If `check_succession_triggers()` returned `True`, append a warning line inside the box before the closing border:

```
│  ⚠️  Succession suggested: <reason>                  │
```

## Important Notes

- This is the DEFAULT command — it runs when the user types `/empire` with no subcommand
- All file reads should use `read_file_safe()` to gracefully handle missing files
- Use `core/paths.py` functions to compute correct paths — never hardcode paths
- Use `core/entries.py` parsing functions — never manually parse entry formats
- If any state file is missing, show sensible defaults (0 counts, "none", etc.) rather than erroring
- The dashboard is read-only — it never modifies any state
