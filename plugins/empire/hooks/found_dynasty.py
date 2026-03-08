#!/usr/bin/env python3
"""Create dynasty working state (dynasty.json, day.md, dawn.md, dusk.md, day-briefing.md).

Called by /empire init after .empire/ directory is created.
Idempotent — safe to call multiple times.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_dynasty_dir, get_current_branch
from core.state import ensure_dynasty_dir, write_dynasty_json, read_dynasty_json


def get_recent_commits(n=10):
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{n}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return ""


def get_uncommitted_summary():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            lines = [l for l in lines if l.strip()]
            if lines:
                return f"yes ({len(lines)} files)"
            return "no"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


def get_stash_count():
    try:
        result = subprocess.run(
            ["git", "stash", "list"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
            return str(len(lines)) if lines else "none"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "none"


def main():
    branch = get_current_branch()
    dynasty_dir = get_dynasty_dir(branch)
    ensure_dynasty_dir(dynasty_dir)

    now = datetime.now(timezone.utc).isoformat()

    # dynasty.json
    dynasty_path = os.path.join(dynasty_dir, "dynasty.json")
    if not os.path.exists(dynasty_path):
        data = {
            "current": 1,
            "branch": branch,
            "founded": now,
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }
        write_dynasty_json(dynasty_dir, data)

    # day.md
    day_path = os.path.join(dynasty_dir, "day.md")
    if not os.path.exists(day_path):
        with open(day_path, "w") as f:
            f.write(f"# ☀️ Day — Claude I\n")
            f.write(f"<!-- Branch: {branch} | Born: {now} -->\n\n")
            f.write("## Entries\n\n")

    # dawn.md
    dawn_path = os.path.join(dynasty_dir, "dawn.md")
    if not os.path.exists(dawn_path):
        commits = get_recent_commits()
        uncommitted = get_uncommitted_summary()
        stashes = get_stash_count()

        with open(dawn_path, "w") as f:
            f.write("# 🌅 Dawn — Claude II\n")
            f.write("<!-- Staged for next succession -->\n\n")
            f.write("## Git State\n")
            f.write(f"- Branch: {branch}\n")
            f.write("- Recent commits:\n")
            if commits:
                for line in commits.split("\n"):
                    f.write(f"  - {line}\n")
            else:
                f.write("  - (none)\n")
            f.write(f"- Uncommitted changes: {uncommitted}\n")
            f.write(f"- Stashes: {stashes}\n\n")
            f.write("## Dusk Wisdom\n")
            f.write("<!-- Populated during succession from keyword-matched Dusk entries -->\n")

    # dusk.md
    dusk_path = os.path.join(dynasty_dir, "dusk.md")
    if not os.path.exists(dusk_path):
        with open(dusk_path, "w") as f:
            f.write("# 🌙 Dusk\n")
            f.write("<!-- No wisdom yet — first succession will populate -->\n")

    # day-briefing.md
    briefing_path = os.path.join(dynasty_dir, "day-briefing.md")
    if not os.path.exists(briefing_path):
        with open(briefing_path, "w") as f:
            f.write("# Day Briefing — Claude I\n")
            f.write("<!-- Auto-generated at end of session. No entries yet. -->\n")

    print(f"Dynasty state created at: {dynasty_dir}")
    print(f"Branch: {branch}")
    print(f"Files: dynasty.json, day.md, dawn.md, dusk.md, day-briefing.md")


if __name__ == "__main__":
    main()
