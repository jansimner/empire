#!/usr/bin/env python3
"""SessionStart hook: Load Vault + Day briefing into conversation context."""

import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_current_branch, resolve_dynasty_dir
from core.state import (
    read_file_safe,
    write_file_safe,
    read_dynasty_json,
    write_dynasty_json,
    check_succession_triggers,
)
from core.entries import parse_day_entries, serialize_day_entries
from core.briefing import generate_briefing
from core.ref_tracker import apply_ref_cache, load_ref_cache
from core.oracle import search_lineage, extract_topic_keywords, format_ancestor_hint
from core.constants import ruler_name


def build_briefing_output(
    vault: str,
    briefing: str,
    dynasty: dict,
    branch: str,
    lineage_path: str = "",
) -> str:
    """Build the output string shown to Claude at session start."""
    if not vault and not briefing:
        return ""

    current = dynasty.get("current", 1)
    epithets = dynasty.get("epithets", {})
    current_epithet = epithets.get(str(current))

    parts = []
    parts.append(f"Empire active on branch: {branch} | {ruler_name(current)}")
    if current_epithet:
        parts[-1] += f' "{current_epithet}"'

    if vault:
        parts.append("")
        parts.append(vault)

    if briefing:
        parts.append("")
        parts.append(briefing)

    # Ancestor Oracle: search lineage for topics matching current context
    if lineage_path:
        lineage_content = read_file_safe(lineage_path)
        if lineage_content:
            keywords = extract_topic_keywords(briefing, "", vault)
            if keywords:
                matches = search_lineage(lineage_content, keywords)
                if matches:
                    hint = format_ancestor_hint(matches)
                    if hint:
                        parts.append("")
                        parts.append(hint)

    return "\n".join(parts)


def recover_from_crash(dynasty_dir: str, dynasty: dict, branch: str) -> str | None:
    """Apply pending ref cache and regenerate briefing if needed.

    If the previous session's stop hook never ran (crash/kill/restart),
    the ref cache still has accumulated scores. Apply them now so they
    aren't lost, then regenerate the briefing.

    Returns the regenerated briefing string, or None if no recovery was needed.
    """
    cache_path = os.path.join(dynasty_dir, "ref_cache.json")
    cache = load_ref_cache(cache_path)
    if not cache:
        return None

    day_path = os.path.join(dynasty_dir, "day.md")
    day_content = read_file_safe(day_path)
    if not day_content:
        return None

    entries = parse_day_entries(day_content)
    entries = apply_ref_cache(entries, cache)
    write_file_safe(cache_path, "{}")

    # Write updated entries back to day.md
    current = dynasty.get("current", 1)
    epithets = dynasty.get("epithets", {})
    current_epithet = epithets.get(str(current))
    born = dynasty.get("founded", "")
    updated_day = serialize_day_entries(
        entries, ruler_name(current), current_epithet, branch, born,
    )
    write_file_safe(day_path, updated_day)

    # Regenerate briefing from recovered state
    sessions = dynasty.get("sessions_since_succession", 0)
    should_succeed, reason = check_succession_triggers(entries, sessions)

    briefing = generate_briefing(
        entries=entries,
        name=ruler_name(current),
        epithet=current_epithet,
        branch=branch,
        succession_suggested=should_succeed,
        succession_reason=reason,
    )
    briefing_path = os.path.join(dynasty_dir, "day-briefing.md")
    write_file_safe(briefing_path, briefing)
    return briefing


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        branch = get_current_branch()
        vault_path = os.path.join(project_root, ".empire", "vault.md")
        dynasty_dir = resolve_dynasty_dir(branch)
        dynasty = read_dynasty_json(dynasty_dir)

        # Recover from any previous crash before reading briefing
        recovered_briefing = recover_from_crash(dynasty_dir, dynasty, branch)

        vault = read_file_safe(vault_path)
        briefing_path = os.path.join(dynasty_dir, "day-briefing.md")
        briefing = recovered_briefing or read_file_safe(briefing_path)

        memory_dir = os.path.dirname(dynasty_dir)
        lineage_path = os.path.join(memory_dir, "lineage.md")

        output = build_briefing_output(vault, briefing, dynasty, branch, lineage_path)
        if output:
            print(output)

        # Increment session counter at start so it counts even if session crashes
        sessions = dynasty.get("sessions_since_succession", 0)
        dynasty["sessions_since_succession"] = sessions + 1
        write_dynasty_json(dynasty_dir, dynasty)
    except Exception as exc:
        # Log to stderr so failures are visible in debug output
        print(f"Empire session_start: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
