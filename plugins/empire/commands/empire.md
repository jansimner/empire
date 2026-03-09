---
name: empire
description: Display Empire status dashboard — current dynasty state and pressure
---

# /empire — Status Dashboard

When the user runs `/empire` with no arguments, render the status dashboard.

## Steps

1. Run this command using Bash:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/show_dashboard.py
```

2. Display the printed output **exactly as-is** to the user. The output is pre-formatted markdown — do not modify it in any way.

## Rules

- **DO NOT** reformat, rearrange, or wrap the output in boxes, tables, or code blocks
- **DO NOT** add `???`, placeholders, or substitute any text
- **DO NOT** add emojis, icons, or decorations that aren't in the output
- **DO NOT** manually construct the dashboard — always call the script
- Copy the script output verbatim. If a field is missing from the output, it means it doesn't exist yet — do not invent placeholder values
- This is the DEFAULT command — it runs when the user types `/empire` with no subcommand
