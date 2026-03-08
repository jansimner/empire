#!/usr/bin/env python3
"""Stop hook: Update ref scores, generate briefing, check succession triggers."""

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
    check_succession_triggers,
)
from core.entries import parse_day_entries, serialize_day_entries
from core.briefing import generate_briefing
from core.ref_tracker import load_ref_cache
from core.scribe import get_session_diff, extract_changed_files, classify_changes, merge_with_existing


def apply_ref_cache(entries: list[dict], cache: dict) -> list[dict]:
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

        entries = parse_day_entries(day_content)

        cache_path = os.path.join(dynasty_dir, "ref_cache.json")
        cache = load_ref_cache(cache_path)
        if cache:
            entries = apply_ref_cache(entries, cache)
            write_file_safe(cache_path, "{}")

        # Auto-generate entries from git diff
        diff_output = get_session_diff()
        if diff_output:
            changed_files = extract_changed_files(diff_output)
            if changed_files:
                new_entries = classify_changes(diff_output, changed_files)
                if new_entries:
                    entries = merge_with_existing(new_entries, entries)

        dynasty = read_dynasty_json(dynasty_dir)
        current = dynasty.get("current", 1)
        epithets = dynasty.get("epithets", {})
        current_epithet = epithets.get(str(current))
        born = dynasty.get("founded", "")

        updated_day = serialize_day_entries(entries, f"Claude {current}", current_epithet, branch, born)
        write_file_safe(day_path, updated_day)

        sessions = dynasty.get("sessions_since_succession", 0)
        should_succeed, reason = check_succession_triggers(entries, sessions)

        briefing = generate_briefing(
            entries=entries,
            name=f"Claude {current}",
            epithet=current_epithet,
            branch=branch,
            succession_suggested=should_succeed,
            succession_reason=reason,
        )
        briefing_path = os.path.join(dynasty_dir, "day-briefing.md")
        write_file_safe(briefing_path, briefing)

        dynasty["sessions_since_succession"] = sessions + 1
        write_dynasty_json(dynasty_dir, dynasty)

        if should_succeed:
            dawn_path = os.path.join(dynasty_dir, "dawn.md")
            dawn = read_file_safe(dawn_path)
            if "succession suggested" not in dawn.lower():
                dawn += f"\n\n## ⚔️ Succession suggested\nReason: {reason}\nRun /empire succession or it will auto-trigger next session.\n"
                write_file_safe(dawn_path, dawn)
            print(f"Empire: succession suggested — {reason}. Run /empire succession.")

    except Exception:
        pass


if __name__ == "__main__":
    main()
