#!/usr/bin/env python3
"""PostToolUse hook: Track references to Day entries from tool usage."""

import json
import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_current_branch, resolve_dynasty_dir
from core.state import read_file_safe
from core.entries import parse_day_entries
from core.ref_tracker import score_entries_against_content, load_ref_cache, save_ref_cache


def main():
    try:
        project_root = get_project_root()
        if project_root is None:
            return

        input_data = json.loads(sys.stdin.read())
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

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
        dynasty_dir = resolve_dynasty_dir(branch)
        day_path = os.path.join(dynasty_dir, "day.md")
        day_content = read_file_safe(day_path)
        if not day_content:
            return

        entries = parse_day_entries(day_content)
        if not entries:
            return

        scores = score_entries_against_content(entries, content, project_root)
        matched = {k: v for k, v in scores.items() if v > 0}
        if not matched:
            return

        cache_path = os.path.join(dynasty_dir, "ref_cache.json")
        cache = load_ref_cache(cache_path)
        for idx, score in matched.items():
            key = str(idx)
            cache[key] = cache.get(key, 0) + score
        save_ref_cache(cache_path, cache)

    except Exception:
        pass


if __name__ == "__main__":
    main()
