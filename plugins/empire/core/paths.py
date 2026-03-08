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
