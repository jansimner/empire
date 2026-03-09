#!/usr/bin/env python3
"""Entry point for /empire succession — runs the succession protocol."""

import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_project_root, get_current_branch, resolve_dynasty_dir
from core.succession import run_succession

if __name__ == "__main__":
    project_root = get_project_root()
    if project_root is None:
        print("NO_EMPIRE", file=sys.stderr)
        sys.exit(1)

    branch = get_current_branch()
    dynasty_dir = resolve_dynasty_dir(branch)

    report = run_succession(
        dynasty_dir=dynasty_dir,
        project_root=project_root,
        branch=branch,
        trigger_reason="manual trigger",
    )
    print(report)
