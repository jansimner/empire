---
name: empire-succession
description: Manually trigger dynasty succession
---

# /empire succession — Trigger Dynasty Succession

When the user runs `/empire succession`, execute the following steps.

## Step 1: Check Dynasty Exists

Run this command using Bash:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_dynasty.py
```

- If `NO_EMPIRE` → print `No Empire found. Run /empire init first.` and stop.
- If `NO_DYNASTY` → print `No dynasty found for this branch.` and stop.

## Step 2: Execute Succession

Run the deterministic succession protocol using the values from Step 1:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_succession.py
```

Display the report output to the user.

## Important Notes

- Succession is fully deterministic — no LLM judgment calls. All logic is in `core/succession.py`.
- `Why:` fields are **sacred** — copied verbatim through every tier, never compressed or summarized.
- Nothing auto-deletes — entries demote to structured lineage.
- Manual succession always proceeds regardless of trigger status.
