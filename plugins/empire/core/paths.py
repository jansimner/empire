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
        return "main"

    # Fallback for fresh repos with no commits yet:
    # symbolic-ref works before any commits exist.
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "main"


def resolve_dynasty_dir(branch: str) -> str:
    """Return the dynasty dir for *branch*, falling back to common alternatives.

    If no ``dynasty.json`` exists under the directory for *branch*, we check
    "main" and "master" as fallbacks (in that order, skipping whichever is the
    current branch).  This handles the case where a dynasty was created under a
    different default-branch name (e.g. the repo was initialised with "master"
    but the system default later changed to "main", or vice-versa).
    """
    primary = get_dynasty_dir(branch)
    if os.path.isfile(os.path.join(primary, "dynasty.json")):
        return primary

    sanitized = sanitize_branch_name(branch)
    for alt in ("main", "master"):
        if sanitize_branch_name(alt) == sanitized:
            continue
        candidate = get_dynasty_dir(alt)
        if os.path.isfile(os.path.join(candidate, "dynasty.json")):
            return candidate

    # Nothing found anywhere – return the primary path so the caller can
    # create it.
    return primary
