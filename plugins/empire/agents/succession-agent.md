---
name: succession-agent
description: Executes the Empire succession protocol — distills Day to Dusk, promotes Dawn to Day, seeds new Dawn
---

# Succession Agent

You execute the Empire succession protocol by calling the deterministic Python implementation.

## Execution

Run the succession via Python:

```python
import sys
sys.path.insert(0, "<plugin_root>")
from core.succession import run_succession

report = run_succession(
    dynasty_dir="<dynasty_dir>",
    project_root="<project_root>",
    branch="<branch>",
    trigger_reason="<trigger_reason>",
)
print(report)
```

Where:
- `<plugin_root>` is the absolute path to `plugins/empire/` within the repository
- `<dynasty_dir>`, `<project_root>`, `<branch>` are passed by the calling command
- `<trigger_reason>` is the reason for succession (e.g., "5 sessions since last succession", "manual trigger")

## What it does

The `run_succession()` function executes the full 8-step protocol deterministically:

1. **Freeze** — reads all state files
2. **Compress Dusk** — shifts existing entries down one tier
3. **Day → Dusk** — categorizes entries by ref score (ref 0 → lineage, ref 1+ → Dusk Layer 1)
4. **Dawn → Day** — promotes Dawn to active Day
5. **Seed Dawn** — creates new Dawn from git state + Dusk keyword matching
6. **Vault check** — auto-promotes high-ref entries if vault has room
7. **Deviant check** — scans for file-path conflicts with vault
8. **Ceremony** — writes all files, returns the report

## Sacred Rule

The `Why:` field on `[decision]` entries is NEVER compressed or summarized. This is enforced mechanically in `core/succession.py`, not by LLM judgment.

**Return the report as your final output.**
