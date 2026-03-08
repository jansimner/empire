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
sys.path.insert(0, "<plugin_root>")
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

- If `NO_EMPIRE` → print `No Empire found. Run /empire init first.` and stop.
- If `NO_DYNASTY` → print `No dynasty found for this branch.` and stop.

## Step 2: Execute Succession

Run the deterministic succession protocol via Python:

```python
import sys
sys.path.insert(0, "<plugin_root>")
from core.succession import run_succession

report = run_succession(
    dynasty_dir="<dynasty_dir>",
    project_root="<project_root>",
    branch="<branch>",
    trigger_reason="manual trigger",
)
print(report)
```

Display the report output to the user.

## Important Notes

- Succession is fully deterministic — no LLM judgment calls. All logic is in `core/succession.py`.
- `Why:` fields are **sacred** — copied verbatim through every tier, never compressed or summarized.
- Nothing auto-deletes — entries demote to structured lineage.
- Manual succession always proceeds regardless of trigger status.
