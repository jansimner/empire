---
name: empire
description: Display Empire status dashboard — current dynasty state and pressure
---

# /empire — Status Dashboard

You are the Empire status reporter. When the user runs `/empire` with no arguments, render the status dashboard.

## How to render

Run this command using Bash:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show_dashboard.py
```

Display the printed output exactly as-is to the user — it is pre-formatted markdown.

## Important Notes

- This is the DEFAULT command — it runs when the user types `/empire` with no subcommand
- The dashboard is read-only — it never modifies any state
- All formatting logic lives in `core/dashboard.py` (tested, emoji-width-aware)
- Do NOT manually construct the box — always call `render_dashboard()`
