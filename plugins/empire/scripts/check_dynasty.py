#!/usr/bin/env python3
"""Entry point for /empire succession — checks if dynasty exists and prints state."""

import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.paths import get_current_branch, get_project_root, resolve_dynasty_dir

if __name__ == "__main__":
    project_root = get_project_root()
    branch = get_current_branch()

    if project_root is None or not os.path.isdir(os.path.join(project_root, ".empire")):
        print("NO_EMPIRE")
    else:
        dynasty_dir = resolve_dynasty_dir(branch)
        dynasty_json_path = os.path.join(dynasty_dir, "dynasty.json")
        if not os.path.exists(dynasty_json_path):
            print("NO_DYNASTY")
        else:
            print(f"DYNASTY_DIR={dynasty_dir}")
            print(f"PROJECT_ROOT={project_root}")
            print(f"BRANCH={branch}")
