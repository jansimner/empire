#!/usr/bin/env python3
"""SessionStart hook: Load Vault + Day briefing into conversation context."""

import json
import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_dynasty_dir, get_current_branch
from core.state import read_file_safe, read_dynasty_json
from core.oracle import search_lineage, extract_topic_keywords, format_ancestor_hint
from core.constants import ruler_name


def build_briefing_output(
    vault_path: str,
    briefing_path: str,
    dynasty_dir: str,
    branch: str,
    lineage_path: str = "",
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


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        branch = get_current_branch()
        vault_path = os.path.join(project_root, ".empire", "vault.md")
        dynasty_dir = get_dynasty_dir(branch)
        briefing_path = os.path.join(dynasty_dir, "day-briefing.md")

        memory_dir = os.path.dirname(dynasty_dir)
        lineage_path = os.path.join(memory_dir, "lineage.md")

        output = build_briefing_output(
            vault_path, briefing_path, dynasty_dir, branch, lineage_path,
        )
        if output:
            print(output)
    except Exception:
        pass  # Fail silently per design


if __name__ == "__main__":
    main()
