# Empire Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Empire Claude Code plugin — a continuous context protocol that manages conversation context through dynasty succession (Dawn/Day/Dusk).

**Architecture:** Claude Code plugin with Python hooks for automation (SessionStart, Stop, PostToolUse), markdown commands for user interaction (7 slash commands), a succession subagent, and a shared Python utility library for state management. State is split: `.empire/` in project root (git-committed) and `~/.claude/projects/<project>/empire/` for private working state.

**Tech Stack:** Python 3 (hooks + utilities), Markdown (commands/agents/skills), JSON (dynasty state, hook config)

**Design doc:** `docs/plans/2026-03-08-empire-design.md`

---

### Task 1: Plugin Scaffold

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `README.md`

**Step 1: Create plugin.json**

```json
{
  "name": "empire",
  "description": "Continuous Context Protocol — manage conversation context through dynasty succession (Dawn/Day/Dusk)",
  "version": "0.1.0",
  "author": {
    "name": "jansimner"
  },
  "license": "MIT",
  "keywords": ["context", "memory", "succession", "dynasty", "foundation"]
}
```

**Step 2: Create README.md**

Write a README covering:
- What Empire is (1 paragraph)
- The Foundation metaphor (Dawn/Day/Dusk table)
- Installation: `claude plugin add /path/to/empire`
- Quick start: `/empire init` then work normally
- Commands list (one line each)
- How it works (hooks run automatically, succession is seamless)

**Step 3: Create directory structure**

```bash
mkdir -p commands agents hooks skills/succession-protocol core tests
```

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json README.md
git commit -m "feat: scaffold Empire plugin structure"
```

---

### Task 2: Core Python Utility Library

This is the shared foundation all hooks use. Build and test it first.

**Files:**
- Create: `core/__init__.py`
- Create: `core/paths.py`
- Create: `core/state.py`
- Create: `core/entries.py`
- Create: `core/constants.py`
- Create: `tests/test_paths.py`
- Create: `tests/test_state.py`
- Create: `tests/test_entries.py`

**Step 1: Write constants**

Create `core/constants.py`:

```python
VAULT_MAX_LINES = 50
PRESSURE_THRESHOLD_AUTO = 0.7
PRESSURE_THRESHOLD_WARN = 0.5
VAULT_PROMOTION_SESSIONS = 3
DEVIANT_NUDGE_SESSIONS = 5
DEVIANT_RESOLVE_SESSIONS = 10
DUSK_LAYER1_MAX = 100
DUSK_LAYER2_MAX = 50
DUSK_LAYER3_MAX = 30
DAY_MAX_SIZE_LINES = 200

PRESSURE_WEIGHTS = {
    "day_size": 0.3,
    "staleness": 0.25,
    "topic_drift": 0.2,
    "decision_count": 0.15,
    "git_boundary": 0.1,
}

EPITHET_KEYWORDS = {
    "the Builder": ["feature", "add", "create", "new", "implement", "build"],
    "the Gatekeeper": ["auth", "security", "permission", "token", "jwt", "csrf", "cors"],
    "the Debugger": ["fix", "bug", "debug", "error", "issue", "patch", "resolve"],
    "the Reformer": ["refactor", "rename", "restructure", "clean", "simplify", "extract"],
    "the Painter": ["ui", "css", "style", "layout", "component", "design", "theme"],
    "the Chronicler": ["database", "migration", "schema", "prisma", "sql", "model"],
    "the Sentinel": ["test", "spec", "assert", "coverage", "vitest", "jest", "playwright"],
    "the Engineer": ["ci", "cd", "deploy", "docker", "pipeline", "infra", "config"],
    "the Ambassador": ["api", "endpoint", "route", "controller", "rest", "graphql"],
    "the Scribe": ["doc", "readme", "comment", "jsdoc", "typedoc"],
    "the Swift": ["performance", "optimize", "cache", "speed", "lazy", "bundle"],
}
```

**Step 2: Write failing tests for paths module**

Create `tests/test_paths.py`:

```python
import os
import tempfile
import pytest
from unittest.mock import patch
from core.paths import (
    get_project_root,
    get_memory_dir,
    get_current_branch,
    get_dynasty_dir,
    sanitize_branch_name,
)


def test_sanitize_branch_name_simple():
    assert sanitize_branch_name("main") == "main"


def test_sanitize_branch_name_with_slashes():
    assert sanitize_branch_name("feature/payments") == "feature-payments"


def test_sanitize_branch_name_with_special_chars():
    assert sanitize_branch_name("feature/my_branch@2") == "feature-my_branch-2"


def test_get_project_root_finds_empire_dir(tmp_path):
    empire_dir = tmp_path / ".empire"
    empire_dir.mkdir()
    with patch("os.getcwd", return_value=str(tmp_path)):
        assert get_project_root() == str(tmp_path)


def test_get_project_root_returns_none_when_missing(tmp_path):
    with patch("os.getcwd", return_value=str(tmp_path)):
        assert get_project_root() is None


def test_get_memory_dir_constructs_path(tmp_path):
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        with patch("core.paths.get_project_root", return_value="/home/user/myproject"):
            result = get_memory_dir()
            assert "empire" in result
            assert "-home-user-myproject" in result


def test_get_dynasty_dir_uses_sanitized_branch(tmp_path):
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        result = get_dynasty_dir("feature/payments")
        assert result.endswith("dynasty/feature-payments")


def test_get_current_branch_reads_git(tmp_path):
    # Create a git repo
    os.system(f"git init {tmp_path} --quiet")
    os.system(f"git -C {tmp_path} commit --allow-empty -m 'init' --quiet")
    with patch("os.getcwd", return_value=str(tmp_path)):
        branch = get_current_branch()
        assert branch in ("main", "master")
```

**Step 3: Run tests to verify they fail**

```bash
cd /home/jansimner/projects/empire && python3 -m pytest tests/test_paths.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'core.paths'`

**Step 4: Implement paths module**

Create `core/__init__.py` (empty).

Create `core/paths.py`:

```python
import os
import re
import subprocess


def sanitize_branch_name(branch: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-.]", "-", branch)


def get_project_root() -> str | None:
    cwd = os.getcwd()
    current = cwd
    while True:
        if os.path.isdir(os.path.join(current, ".empire")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def get_memory_dir() -> str:
    home = os.path.expanduser("~")
    project_root = get_project_root()
    if project_root is None:
        project_root = os.getcwd()
    project_key = project_root.replace("/", "-").replace("\\", "-")
    if project_key.startswith("-"):
        project_key = project_key[1:]
    return os.path.join(home, ".claude", "projects", project_key, "empire")


def get_dynasty_dir(branch: str) -> str:
    memory_dir = get_memory_dir()
    return os.path.join(memory_dir, "dynasty", sanitize_branch_name(branch))


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "main"
```

**Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_paths.py -v
```

Expected: All PASS

**Step 6: Write failing tests for entries module**

Create `tests/test_entries.py`:

```python
import pytest
from core.entries import (
    parse_day_entries,
    serialize_day_entries,
    parse_dusk_entries,
    serialize_dusk_entries,
    generate_epithet,
)


SAMPLE_DAY = """# ☀️ Day — Claude III "the Builder"
<!-- Branch: main | Born: 2026-03-08T14:30:00Z -->

## Entries

### [ref:5] Added rate limiting
Implemented express-rate-limit, 100 req/15min per IP.

### [ref:0] Considered Redis
Decided against it.
"""

SAMPLE_DUSK = """# 🌙 Dusk — Claude II "the Debugger"

## Layer 1 (detailed)
### [ref:4] Payment race condition fix
Mutex lock on concurrent checkout.

## Layer 2 (compressed)
- [ref:2] Empty cart checkout returns 400

## Layer 3 (one-liners)
- [ref:1] Prisma needs $disconnect on error
"""


def test_parse_day_entries_extracts_all():
    entries = parse_day_entries(SAMPLE_DAY)
    assert len(entries) == 2


def test_parse_day_entries_extracts_ref_scores():
    entries = parse_day_entries(SAMPLE_DAY)
    assert entries[0]["ref"] == 5
    assert entries[1]["ref"] == 0


def test_parse_day_entries_extracts_title():
    entries = parse_day_entries(SAMPLE_DAY)
    assert entries[0]["title"] == "Added rate limiting"


def test_parse_day_entries_extracts_body():
    entries = parse_day_entries(SAMPLE_DAY)
    assert "express-rate-limit" in entries[0]["body"]


def test_serialize_day_entries_roundtrips():
    entries = parse_day_entries(SAMPLE_DAY)
    output = serialize_day_entries(entries, "Claude III", "the Builder", "main", "2026-03-08T14:30:00Z")
    re_parsed = parse_day_entries(output)
    assert len(re_parsed) == len(entries)
    assert re_parsed[0]["ref"] == entries[0]["ref"]


def test_parse_dusk_entries_extracts_layers():
    entries = parse_dusk_entries(SAMPLE_DUSK)
    layer1 = [e for e in entries if e["layer"] == 1]
    layer2 = [e for e in entries if e["layer"] == 2]
    layer3 = [e for e in entries if e["layer"] == 3]
    assert len(layer1) == 1
    assert len(layer2) == 1
    assert len(layer3) == 1


def test_generate_epithet_security_work():
    entries = [
        {"title": "Added JWT auth", "body": "token validation with csrf protection"},
        {"title": "Fixed auth bug", "body": "permission check was missing"},
    ]
    epithet = generate_epithet(entries)
    assert epithet == "the Gatekeeper"


def test_generate_epithet_mixed_work():
    entries = [
        {"title": "Added button", "body": "ui component"},
        {"title": "Fixed database", "body": "migration issue"},
        {"title": "Wrote docs", "body": "readme update"},
    ]
    epithet = generate_epithet(entries)
    assert epithet == "the Journeyman"


def test_generate_epithet_empty():
    epithet = generate_epithet([])
    assert epithet == "the Brief"
```

**Step 7: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_entries.py -v
```

Expected: FAIL

**Step 8: Implement entries module**

Create `core/entries.py`:

```python
import re
from core.constants import EPITHET_KEYWORDS


def parse_day_entries(content: str) -> list[dict]:
    entries = []
    pattern = r"### \[ref:(\d+)\] (.+?)(?:\n([\s\S]*?))?(?=\n### |\n## |\Z)"
    for match in re.finditer(pattern, content):
        entries.append({
            "ref": int(match.group(1)),
            "title": match.group(2).strip(),
            "body": match.group(3).strip() if match.group(3) else "",
        })
    return entries


def serialize_day_entries(
    entries: list[dict],
    name: str,
    epithet: str | None,
    branch: str,
    born: str,
) -> str:
    title_part = f"{name}"
    if epithet:
        title_part += f' "{epithet}"'
    lines = [
        f"# ☀️ Day — {title_part}",
        f"<!-- Branch: {branch} | Born: {born} -->",
        "",
        "## Entries",
        "",
    ]
    for entry in entries:
        lines.append(f"### [ref:{entry['ref']}] {entry['title']}")
        if entry.get("body"):
            lines.append(entry["body"])
        lines.append("")
    return "\n".join(lines)


def parse_dusk_entries(content: str) -> list[dict]:
    entries = []
    current_layer = 0
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Layer 1" in line:
            current_layer = 1
        elif "Layer 2" in line:
            current_layer = 2
        elif "Layer 3" in line:
            current_layer = 3
        elif current_layer > 0:
            # Layer 1: ### [ref:N] title + body
            h3_match = re.match(r"### \[ref:(\d+)\] (.+)", line)
            if h3_match:
                body_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("#") and not lines[i].startswith("- [ref:"):
                    if lines[i].strip():
                        body_lines.append(lines[i].strip())
                    i += 1
                entries.append({
                    "layer": current_layer,
                    "ref": int(h3_match.group(1)),
                    "title": h3_match.group(2).strip(),
                    "body": " ".join(body_lines),
                })
                continue
            # Layer 2/3: - [ref:N] text
            li_match = re.match(r"- \[ref:(\d+)\] (.+)", line)
            if li_match:
                entries.append({
                    "layer": current_layer,
                    "ref": int(li_match.group(1)),
                    "title": li_match.group(2).strip(),
                    "body": "",
                })
        i += 1
    return entries


def serialize_dusk_entries(entries: list[dict], name: str, epithet: str | None) -> str:
    title_part = f"{name}"
    if epithet:
        title_part += f' "{epithet}"'
    lines = [f"# 🌙 Dusk — {title_part}", ""]

    for layer_num, label in [(1, "Layer 1 (detailed)"), (2, "Layer 2 (compressed)"), (3, "Layer 3 (one-liners)")]:
        layer_entries = [e for e in entries if e["layer"] == layer_num]
        if layer_entries:
            lines.append(f"## {label}")
            for entry in layer_entries:
                if layer_num == 1:
                    lines.append(f"### [ref:{entry['ref']}] {entry['title']}")
                    if entry.get("body"):
                        lines.append(entry["body"])
                    lines.append("")
                else:
                    lines.append(f"- [ref:{entry['ref']}] {entry['title']}")
            lines.append("")
    return "\n".join(lines)


def generate_epithet(entries: list[dict]) -> str:
    if not entries:
        return "the Brief"

    scores: dict[str, int] = {}
    for epithet, keywords in EPITHET_KEYWORDS.items():
        score = 0
        for entry in entries:
            text = (entry.get("title", "") + " " + entry.get("body", "")).lower()
            for kw in keywords:
                if kw in text:
                    score += 1
        if score > 0:
            scores[epithet] = score

    if not scores:
        return "the Journeyman"

    max_score = max(scores.values())
    winners = [k for k, v in scores.items() if v == max_score]
    if len(winners) > 2:
        return "the Journeyman"
    return winners[0]
```

**Step 9: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_entries.py -v
```

Expected: All PASS

**Step 10: Write failing tests for state module**

Create `tests/test_state.py`:

```python
import json
import os
import pytest
from core.state import (
    read_dynasty_json,
    write_dynasty_json,
    ensure_dynasty_dir,
    read_file_safe,
    write_file_safe,
    count_lines,
    calculate_pressure,
)


def test_read_dynasty_json_default(tmp_path):
    result = read_dynasty_json(str(tmp_path / "nonexistent"))
    assert result["current"] == 0
    assert result["branch"] == "main"
    assert result["epithets"] == {}


def test_write_and_read_dynasty_json(tmp_path):
    dynasty_dir = str(tmp_path / "dynasty")
    os.makedirs(dynasty_dir)
    data = {"current": 3, "branch": "main", "founded": "2026-03-08", "epithets": {"1": "the Builder"}}
    write_dynasty_json(dynasty_dir, data)
    result = read_dynasty_json(dynasty_dir)
    assert result["current"] == 3
    assert result["epithets"]["1"] == "the Builder"


def test_ensure_dynasty_dir_creates(tmp_path):
    dynasty_dir = str(tmp_path / "dynasty" / "main")
    ensure_dynasty_dir(dynasty_dir)
    assert os.path.isdir(dynasty_dir)


def test_read_file_safe_returns_empty_on_missing(tmp_path):
    result = read_file_safe(str(tmp_path / "nope.md"))
    assert result == ""


def test_write_and_read_file(tmp_path):
    path = str(tmp_path / "test.md")
    write_file_safe(path, "hello world")
    assert read_file_safe(path) == "hello world"


def test_count_lines():
    assert count_lines("one\ntwo\nthree") == 3
    assert count_lines("") == 0
    assert count_lines("single") == 1


def test_calculate_pressure_empty():
    pressure = calculate_pressure(day_content="", day_max=200, stale_ratio=0.0, decision_count=0, git_boundary=False)
    assert pressure == 0.0


def test_calculate_pressure_full_day():
    big_day = "\n".join([f"line {i}" for i in range(200)])
    pressure = calculate_pressure(day_content=big_day, day_max=200, stale_ratio=0.5, decision_count=10, git_boundary=True)
    assert pressure > 0.7
```

**Step 11: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_state.py -v
```

Expected: FAIL

**Step 12: Implement state module**

Create `core/state.py`:

```python
import json
import os
from datetime import datetime, timezone
from core.constants import PRESSURE_WEIGHTS, DAY_MAX_SIZE_LINES


def read_file_safe(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return ""


def write_file_safe(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def count_lines(content: str) -> int:
    if not content:
        return 0
    return len(content.strip().split("\n"))


def ensure_dynasty_dir(dynasty_dir: str) -> None:
    os.makedirs(dynasty_dir, exist_ok=True)


def read_dynasty_json(dynasty_dir: str) -> dict:
    path = os.path.join(dynasty_dir, "dynasty.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "current": 0,
            "branch": "main",
            "founded": datetime.now(timezone.utc).isoformat(),
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }


def write_dynasty_json(dynasty_dir: str, data: dict) -> None:
    ensure_dynasty_dir(dynasty_dir)
    path = os.path.join(dynasty_dir, "dynasty.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def calculate_pressure(
    day_content: str,
    day_max: int = DAY_MAX_SIZE_LINES,
    stale_ratio: float = 0.0,
    decision_count: int = 0,
    git_boundary: bool = False,
    topic_drift: float = 0.0,
) -> float:
    day_lines = count_lines(day_content)
    day_ratio = min(day_lines / max(day_max, 1), 1.0)
    decision_ratio = min(decision_count / 20, 1.0)

    pressure = (
        day_ratio * PRESSURE_WEIGHTS["day_size"]
        + stale_ratio * PRESSURE_WEIGHTS["staleness"]
        + topic_drift * PRESSURE_WEIGHTS["topic_drift"]
        + decision_ratio * PRESSURE_WEIGHTS["decision_count"]
        + (1.0 if git_boundary else 0.0) * PRESSURE_WEIGHTS["git_boundary"]
    )
    return round(min(pressure, 1.0), 2)
```

**Step 13: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_state.py -v
```

Expected: All PASS

**Step 14: Commit core library**

```bash
git add core/ tests/
git commit -m "feat: add core Python utility library with paths, state, and entries modules"
```

---

### Task 3: Hooks — hooks.json + SessionStart

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/__init__.py`
- Create: `hooks/session_start.py`
- Create: `tests/test_session_start.py`

**Step 1: Create hooks.json**

```json
{
  "description": "Empire hooks — context lifecycle automation",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/stop.py",
            "timeout": 30
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Read|Edit|Write|Grep|Glob",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/post_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Step 2: Write failing test for session_start**

Create `tests/test_session_start.py`:

```python
import json
import os
import pytest
from unittest.mock import patch
from hooks.session_start import build_briefing_output


def test_build_briefing_with_vault_and_briefing(tmp_path):
    vault_path = tmp_path / "vault.md"
    vault_path.write_text("# 🏛️ Vault\n- TypeScript + NestJS\n- Prisma ORM")

    briefing_path = tmp_path / "day-briefing.md"
    briefing_path.write_text("# ☀️ Briefing\nWorking on auth. Pressure: 30%")

    dynasty_dir = tmp_path / "dynasty"
    dynasty_dir.mkdir()
    (dynasty_dir / "dynasty.json").write_text(json.dumps({
        "current": 3, "branch": "main",
        "epithets": {"2": "the Builder", "3": None},
    }))

    output = build_briefing_output(
        vault_path=str(vault_path),
        briefing_path=str(briefing_path),
        dynasty_dir=str(dynasty_dir),
        branch="main",
    )
    assert "Vault" in output
    assert "TypeScript" in output
    assert "Briefing" in output
    assert "auth" in output


def test_build_briefing_no_empire_initialized():
    output = build_briefing_output(
        vault_path="/nonexistent/vault.md",
        briefing_path="/nonexistent/briefing.md",
        dynasty_dir="/nonexistent/dynasty",
        branch="main",
    )
    assert output == ""
```

**Step 3: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_session_start.py -v
```

Expected: FAIL

**Step 4: Implement session_start.py**

Create `hooks/__init__.py` (empty).

Create `hooks/session_start.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook: Load Vault + Day briefing into conversation context."""

import json
import os
import sys

# Add plugin root to path
plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_dynasty_dir, get_current_branch
from core.state import read_file_safe, read_dynasty_json


def build_briefing_output(
    vault_path: str,
    briefing_path: str,
    dynasty_dir: str,
    branch: str,
) -> str:
    vault = read_file_safe(vault_path)
    briefing = read_file_safe(briefing_path)

    if not vault and not briefing:
        return ""

    dynasty = read_dynasty_json(dynasty_dir)
    current = dynasty.get("current", 0)
    epithets = dynasty.get("epithets", {})
    current_epithet = epithets.get(str(current))

    parts = []
    parts.append(f"Empire active on branch: {branch} | Claude {current}")
    if current_epithet:
        parts[-1] += f' "{current_epithet}"'

    if vault:
        parts.append("")
        parts.append(vault)

    if briefing:
        parts.append("")
        parts.append(briefing)

    return "\n".join(parts)


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        branch = get_current_branch()
        vault_path = os.path.join(project_root, ".empire", "vault.md")
        dynasty_dir = get_dynasty_dir(branch)
        briefing_path = os.path.join(dynasty_dir, "day-briefing.md")

        output = build_briefing_output(vault_path, briefing_path, dynasty_dir, branch)
        if output:
            print(output)
    except Exception:
        pass  # Fail silently per design


if __name__ == "__main__":
    main()
```

**Step 5: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_session_start.py -v
```

Expected: All PASS

**Step 6: Commit**

```bash
git add hooks/ tests/test_session_start.py
git commit -m "feat: add hooks.json and SessionStart hook"
```

---

### Task 4: Hooks — PostToolUse (Reference Tracking)

**Files:**
- Create: `hooks/post_tool_use.py`
- Create: `core/ref_tracker.py`
- Create: `tests/test_ref_tracker.py`

**Step 1: Write failing tests for ref_tracker**

Create `tests/test_ref_tracker.py`:

```python
import json
import pytest
from core.ref_tracker import match_entries_to_content, load_ref_cache, save_ref_cache


ENTRIES = [
    {"ref": 2, "title": "Added rate limiting", "body": "express-rate-limit in middleware/rate-limit.ts"},
    {"ref": 0, "title": "Considered Redis", "body": "session store decision"},
]


def test_match_finds_title_keyword():
    matches = match_entries_to_content(ENTRIES, "rate-limit.ts")
    assert 0 in matches  # index of first entry


def test_match_finds_body_keyword():
    matches = match_entries_to_content(ENTRIES, "session store")
    assert 1 in matches


def test_match_returns_empty_on_no_match():
    matches = match_entries_to_content(ENTRIES, "completely unrelated content")
    assert len(matches) == 0


def test_ref_cache_roundtrip(tmp_path):
    cache_path = str(tmp_path / "ref_cache.json")
    data = {"0": 3, "1": 1}
    save_ref_cache(cache_path, data)
    loaded = load_ref_cache(cache_path)
    assert loaded == data


def test_ref_cache_missing_file(tmp_path):
    loaded = load_ref_cache(str(tmp_path / "nope.json"))
    assert loaded == {}
```

**Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_ref_tracker.py -v
```

Expected: FAIL

**Step 3: Implement ref_tracker**

Create `core/ref_tracker.py`:

```python
import json
import os


def match_entries_to_content(entries: list[dict], content: str) -> list[int]:
    content_lower = content.lower()
    matches = []
    for i, entry in enumerate(entries):
        keywords = set()
        for word in entry.get("title", "").split():
            if len(word) > 3:
                keywords.add(word.lower())
        for word in entry.get("body", "").split():
            if len(word) > 3:
                keywords.add(word.lower())
        # Also match on file paths (anything with a dot and slash)
        import re
        paths = re.findall(r"[\w\-./]+\.\w+", entry.get("body", ""))
        for p in paths:
            keywords.add(p.lower())

        for kw in keywords:
            if kw in content_lower:
                matches.append(i)
                break
    return matches


def load_ref_cache(cache_path: str) -> dict:
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_ref_cache(cache_path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(data, f)
```

**Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_ref_tracker.py -v
```

Expected: All PASS

**Step 5: Implement post_tool_use.py**

Create `hooks/post_tool_use.py`:

```python
#!/usr/bin/env python3
"""PostToolUse hook: Track references to Day entries from tool usage."""

import json
import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_dynasty_dir, get_current_branch
from core.state import read_file_safe
from core.entries import parse_day_entries
from core.ref_tracker import match_entries_to_content, load_ref_cache, save_ref_cache


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        # Read tool input from stdin
        input_data = json.loads(sys.stdin.read())
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Extract content to match against
        content_parts = []
        if isinstance(tool_input, dict):
            for key in ("file_path", "path", "pattern", "command", "content"):
                val = tool_input.get(key, "")
                if val:
                    content_parts.append(str(val))
        content = " ".join(content_parts)
        if not content:
            return

        branch = get_current_branch()
        dynasty_dir = get_dynasty_dir(branch)
        day_path = os.path.join(dynasty_dir, "day.md")
        day_content = read_file_safe(day_path)
        if not day_content:
            return

        entries = parse_day_entries(day_content)
        if not entries:
            return

        matches = match_entries_to_content(entries, content)
        if not matches:
            return

        # Update ref cache (batched, applied at Stop)
        cache_path = os.path.join(dynasty_dir, "ref_cache.json")
        cache = load_ref_cache(cache_path)
        for idx in matches:
            key = str(idx)
            cache[key] = cache.get(key, 0) + 1
        save_ref_cache(cache_path, cache)

    except Exception:
        pass  # Fail silently


if __name__ == "__main__":
    main()
```

**Step 6: Commit**

```bash
git add core/ref_tracker.py hooks/post_tool_use.py tests/test_ref_tracker.py
git commit -m "feat: add PostToolUse hook for reference tracking"
```

---

### Task 5: Hooks — Stop (Briefing + Pressure + Ref Scores)

**Files:**
- Create: `hooks/stop.py`
- Create: `core/briefing.py`
- Create: `tests/test_briefing.py`

**Step 1: Write failing tests for briefing module**

Create `tests/test_briefing.py`:

```python
import pytest
from core.briefing import generate_briefing
from core.entries import parse_day_entries


SAMPLE_DAY = """# ☀️ Day — Claude VI "the Gatekeeper"
<!-- Branch: main | Born: 2026-03-08T14:30:00Z -->

## Entries

### [ref:5] Added rate limiting to auth endpoints
Implemented express-rate-limit, 100 req/15min per IP.

### [ref:3] Webhook signature validation
All Stripe webhooks verified with HMAC-SHA256.

### [ref:0] Considered Redis for session store
Decided against it for now.
"""


def test_generate_briefing_includes_summary():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
        pressure=0.42,
    )
    assert "Briefing" in briefing
    assert "Claude VI" in briefing
    assert "rate limiting" in briefing or "auth" in briefing


def test_generate_briefing_includes_pressure():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
        pressure=0.42,
    )
    assert "42%" in briefing


def test_generate_briefing_includes_entry_count():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
        pressure=0.42,
    )
    assert "3" in briefing


def test_generate_briefing_empty_entries():
    briefing = generate_briefing(
        entries=[],
        name="Claude I",
        epithet=None,
        branch="main",
        pressure=0.0,
    )
    assert "Briefing" in briefing
    assert "0" in briefing
```

**Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_briefing.py -v
```

Expected: FAIL

**Step 3: Implement briefing module**

Create `core/briefing.py`:

```python
from datetime import datetime, timezone


def generate_briefing(
    entries: list[dict],
    name: str,
    epithet: str | None,
    branch: str,
    pressure: float,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    title = name
    if epithet:
        title += f' "{epithet}"'

    high_ref = [e for e in entries if e.get("ref", 0) >= 3]
    active_titles = [e["title"] for e in high_ref[:3]]

    lines = [
        f"# ☀️ Briefing — {title}",
        f"Last updated: {now}",
        f"Branch: {branch}",
        "",
    ]

    if active_titles:
        lines.append("Active work: " + "; ".join(active_titles))
    else:
        lines.append("No high-reference entries.")

    lines.append(f"{len(entries)} Day entries, {len(high_ref)} high-reference.")
    lines.append(f"Succession pressure: {int(pressure * 100)}%")

    return "\n".join(lines)
```

**Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_briefing.py -v
```

Expected: All PASS

**Step 5: Implement stop.py**

Create `hooks/stop.py`:

```python
#!/usr/bin/env python3
"""Stop hook: Update ref scores, generate briefing, calculate pressure, trigger succession if needed."""

import json
import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_dynasty_dir, get_current_branch
from core.state import (
    read_file_safe,
    write_file_safe,
    read_dynasty_json,
    write_dynasty_json,
    calculate_pressure,
)
from core.entries import parse_day_entries, serialize_day_entries
from core.briefing import generate_briefing
from core.ref_tracker import load_ref_cache
from core.constants import PRESSURE_THRESHOLD_AUTO, PRESSURE_THRESHOLD_WARN


def apply_ref_cache(entries: list[dict], cache: dict) -> list[dict]:
    """Apply batched reference increments from PostToolUse cache."""
    for key, count in cache.items():
        idx = int(key)
        if 0 <= idx < len(entries):
            entries[idx]["ref"] = entries[idx].get("ref", 0) + count
    return entries


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        branch = get_current_branch()
        dynasty_dir = get_dynasty_dir(branch)
        day_path = os.path.join(dynasty_dir, "day.md")
        day_content = read_file_safe(day_path)

        if not day_content:
            return

        # Parse entries
        entries = parse_day_entries(day_content)

        # Apply ref cache from PostToolUse
        cache_path = os.path.join(dynasty_dir, "ref_cache.json")
        cache = load_ref_cache(cache_path)
        if cache:
            entries = apply_ref_cache(entries, cache)
            # Clear cache
            write_file_safe(cache_path, "{}")

        # Read dynasty state
        dynasty = read_dynasty_json(dynasty_dir)
        current = dynasty.get("current", 1)
        epithets = dynasty.get("epithets", {})
        current_epithet = epithets.get(str(current))
        born = dynasty.get("founded", "")

        # Write updated Day with new ref scores
        updated_day = serialize_day_entries(entries, f"Claude {current}", current_epithet, branch, born)
        write_file_safe(day_path, updated_day)

        # Calculate pressure
        stale_entries = [e for e in entries if e.get("ref", 0) == 0]
        stale_ratio = len(stale_entries) / max(len(entries), 1)

        pressure = calculate_pressure(
            day_content=updated_day,
            stale_ratio=stale_ratio,
            decision_count=len(entries),
        )

        # Generate briefing
        briefing = generate_briefing(
            entries=entries,
            name=f"Claude {current}",
            epithet=current_epithet,
            branch=branch,
            pressure=pressure,
        )
        briefing_path = os.path.join(dynasty_dir, "day-briefing.md")
        write_file_safe(briefing_path, briefing)

        # Update session count
        dynasty["sessions_since_succession"] = dynasty.get("sessions_since_succession", 0) + 1
        write_dynasty_json(dynasty_dir, dynasty)

        # Pressure warnings
        if pressure >= PRESSURE_THRESHOLD_AUTO:
            # Write succession note to Dawn
            dawn_path = os.path.join(dynasty_dir, "dawn.md")
            dawn = read_file_safe(dawn_path)
            if "succession required" not in dawn.lower():
                dawn += "\n\n## ⚔️ Succession required\nPressure exceeded threshold. Run /empire succession or it will auto-trigger next session.\n"
                write_file_safe(dawn_path, dawn)
            print(f"Empire: succession pressure critical ({int(pressure * 100)}%). Auto-succession recommended.")
        elif pressure >= PRESSURE_THRESHOLD_WARN:
            print(f"Empire: succession pressure rising ({int(pressure * 100)}%). Consider /empire succession soon.")

    except Exception:
        pass  # Fail silently


if __name__ == "__main__":
    main()
```

**Step 6: Commit**

```bash
git add core/briefing.py hooks/stop.py tests/test_briefing.py
git commit -m "feat: add Stop hook with briefing generation and pressure monitoring"
```

---

### Task 6: `/empire init` Command

**Files:**
- Create: `commands/empire-init.md`

**Step 1: Write the empire-init command**

This is a markdown skill file that instructs Claude on how to initialize a dynasty. Create `commands/empire-init.md`:

The command should instruct Claude to:
1. Check if `.empire/` already exists (abort if so)
2. Create `.empire/vault.md` with auto-detected project info (scan package.json, Cargo.toml, pyproject.toml, etc.)
3. Create `.empire/protocol.md` with dynasty rules summary
4. Create `.empire/config.md` with commented-out defaults
5. Create dynasty directory in memory with `dynasty.json`, empty `dawn.md` seeded from git state
6. Print the founding ceremony with box-drawing + emojis
7. Commit `.empire/` to git

See design doc for exact ceremony format and vault seeding logic.

**Step 2: Verify command file follows plugin convention**

Check that the file has proper frontmatter (`name`, `description` fields) matching other command files in the ecosystem.

**Step 3: Commit**

```bash
git add commands/empire-init.md
git commit -m "feat: add /empire init command"
```

---

### Task 7: `/empire` Status Command

**Files:**
- Create: `commands/empire.md`

**Step 1: Write the empire status command**

Create `commands/empire.md` — the default command when user runs `/empire` with no args.

Instructs Claude to:
1. Read `.empire/vault.md` and count lines
2. Read `dynasty.json` for current dynasty state
3. Read `day.md` and count entries
4. Read `dusk.md` and count entries per layer
5. Read `dawn.md` and count staged items
6. Count active deviants from `deviants.md`
7. Calculate current pressure
8. Format and display the status dashboard with box-drawing + emojis per design doc format

**Step 2: Commit**

```bash
git add commands/empire.md
git commit -m "feat: add /empire status dashboard command"
```

---

### Task 8: `/empire vault`, `/empire dawn`, `/empire deviant`, `/empire lineage` Commands

**Files:**
- Create: `commands/empire-vault.md`
- Create: `commands/empire-dawn.md`
- Create: `commands/empire-deviant.md`
- Create: `commands/empire-lineage.md`

**Step 1: Write empire-vault command**

Supports: no args (display), `add "text"`, `remove <line>`, `swap <line> "text"`. Enforces 50-line cap.

**Step 2: Write empire-dawn command**

Supports: no args (display), `add "note"`, `remove <line>`.

**Step 3: Write empire-deviant command**

Supports: no args (list all), `"description"` (flag new), `resolve <id>` (interactive resolution: fix/update/accept/dismiss).

**Step 4: Write empire-lineage command**

Supports: no args (show current branch history), `--branch <name>`, `--search "keyword"`.

**Step 5: Commit**

```bash
git add commands/empire-vault.md commands/empire-dawn.md commands/empire-deviant.md commands/empire-lineage.md
git commit -m "feat: add vault, dawn, deviant, and lineage commands"
```

---

### Task 9: Succession Agent + `/empire succession` Command

**Files:**
- Create: `agents/succession-agent.md`
- Create: `commands/empire-succession.md`
- Create: `skills/succession-protocol/SKILL.md`

**Step 1: Write succession-agent.md**

The subagent prompt that handles the full 8-step succession protocol:
1. Freeze — snapshot state
2. Prune Dusk — check scores, compress tiers
3. Day → Dusk — distill entries by ref score, generate epithet
4. Dawn → Day — promote, reset scores, increment counter
5. Seed new Dawn — git scan + Dusk keyword match
6. Vault check — promotion candidates
7. Deviant check — contradiction scan
8. Ceremony — generate report, update lineage

The agent reads all state files, performs the protocol, writes all updated files, and returns the ceremony report.

**Step 2: Write empire-succession command**

Create `commands/empire-succession.md`. Instructs Claude to:
- Spawn the succession agent
- If `--review` flag: show distillation proposal, wait for approval
- Display the ceremony report when agent completes

**Step 3: Write succession protocol skill**

Create `skills/succession-protocol/SKILL.md`. Detailed reference for the succession algorithm — thresholds, tier logic, epithet selection, ceremony format.

**Step 4: Commit**

```bash
git add agents/ commands/empire-succession.md skills/
git commit -m "feat: add succession agent, command, and protocol skill"
```

---

### Task 10: Integration Test — Full Init + Session Cycle

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Test the full lifecycle in a temp directory:
1. Set up a fake git repo with some files
2. Simulate `/empire init` by running the init logic programmatically
3. Verify `.empire/vault.md` was created with content
4. Verify dynasty directory was created with `dynasty.json`
5. Simulate a SessionStart hook — verify it outputs vault + briefing
6. Simulate PostToolUse with some file paths — verify ref cache is updated
7. Simulate Stop hook — verify briefing is generated, ref scores applied, pressure calculated
8. Verify all files are in expected state

**Step 2: Run integration test**

```bash
python3 -m pytest tests/test_integration.py -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for full init + session lifecycle"
```

---

### Task 11: README + Final Polish

**Files:**
- Modify: `README.md`

**Step 1: Finalize README**

Complete the README with:
- Installation instructions
- Quick start guide
- Full command reference
- How the automatic system works (hooks explained simply)
- The Foundation metaphor explained
- Configuration (hand-edit `.empire/config.md`)
- Example ceremony outputs

**Step 2: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: finalize README with full usage guide"
```

---

### Task 12: Manual Smoke Test

**Step 1:** Install the plugin locally:
```bash
claude plugin add /home/jansimner/projects/empire
```

**Step 2:** Navigate to a test project and run `/empire init`

**Step 3:** Verify the founding ceremony displays correctly

**Step 4:** Work for a bit, then run `/empire` to check status

**Step 5:** Run `/empire succession` to test manual succession

**Step 6:** Verify lineage was updated, ceremony displayed, new Dawn seeded

---
