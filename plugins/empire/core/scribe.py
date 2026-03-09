"""Session Scribe: auto-generate Day entries from git diff.

Heuristic-based classifier that turns git diff output into typed Day entries.
Runs in the Stop hook to silently record what happened during a session.
"""

import os
import re
import subprocess


# File extensions considered config/infra
_CONFIG_EXTENSIONS = {
    ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg",
    ".env", ".dockerfile", ".dockerignore",
}
_CONFIG_NAMES = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "makefile", "procfile", "renovate.json", ".eslintrc",
    ".prettierrc", ".editorconfig", "tsconfig.json",
    "package.json", "pyproject.toml", "setup.cfg",
}
_CI_PATTERNS = {".github/workflows/", ".gitlab-ci", "jenkinsfile", ".circleci/"}


def get_session_diff(session_start_sha: str = "") -> str:
    """Get git diff for the current session.

    If *session_start_sha* is provided, diffs from that commit to the current
    working tree (captures both committed and uncommitted changes made during
    the session).  Falls back to ``git diff HEAD`` + ``git diff --cached`` when
    no start SHA is available.

    Returns combined output, truncated to 3000 chars to stay lean.
    """
    parts = []

    if session_start_sha:
        # Diff from session start to working tree — captures everything
        commands = [
            ["git", "diff", session_start_sha],
        ]
    else:
        # Fallback: only sees uncommitted changes
        commands = [
            ["git", "diff", "HEAD"],
            ["git", "diff", "--cached"],
        ]

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                parts.append(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue

    combined = "\n".join(parts)
    return combined[:3000]


def extract_changed_files(diff_output: str) -> list[str]:
    """Extract file paths from diff output.

    Looks for 'diff --git a/X b/X' patterns and deduplicates.
    """
    files = []
    seen = set()
    for match in re.finditer(r"diff --git a/(.+?) b/(.+)", diff_output):
        path = match.group(2)
        if path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _is_new_file(diff_output: str, filepath: str) -> bool:
    """Check if a file appears as 'new file mode' in the diff."""
    # Look for the diff header for this file followed by 'new file mode'
    escaped = re.escape(filepath)
    pattern = rf"diff --git a/{escaped} b/{escaped}\nnew file mode"
    return bool(re.search(pattern, diff_output))


def _is_deleted_file(diff_output: str, filepath: str) -> bool:
    """Check if a file appears as 'deleted file mode' in the diff."""
    escaped = re.escape(filepath)
    pattern = rf"diff --git a/{escaped} b/{escaped}\ndeleted file mode"
    return bool(re.search(pattern, diff_output))


def _is_test_file(filepath: str) -> bool:
    """Check if a file is a test file."""
    basename = os.path.basename(filepath).lower()
    dirparts = filepath.lower().split("/")
    return (
        basename.startswith("test_")
        or basename.startswith("test.")
        or basename.endswith("_test.py")
        or basename.endswith(".test.ts")
        or basename.endswith(".test.js")
        or basename.endswith(".test.tsx")
        or basename.endswith(".test.jsx")
        or basename.endswith(".spec.ts")
        or basename.endswith(".spec.js")
        or "tests" in dirparts
        or "__tests__" in dirparts
    )


def _is_config_file(filepath: str) -> bool:
    """Check if a file is a config/infra file."""
    basename = os.path.basename(filepath).lower()
    _, ext = os.path.splitext(filepath.lower())
    path_lower = filepath.lower()

    if basename in _CONFIG_NAMES:
        return True
    if ext in _CONFIG_EXTENSIONS:
        return True
    for pattern in _CI_PATTERNS:
        if pattern in path_lower:
            return True
    return False


def _get_line_counts(diff_output: str, filepath: str) -> tuple[int, int]:
    """Get approximate added/removed line counts for a file from diff."""
    escaped = re.escape(filepath)
    # Find the diff section for this file
    pattern = rf"diff --git a/{escaped} b/{escaped}\n(.*?)(?=diff --git |\Z)"
    match = re.search(pattern, diff_output, re.DOTALL)
    if not match:
        return 0, 0

    section = match.group(1)
    added = sum(1 for line in section.split("\n") if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in section.split("\n") if line.startswith("-") and not line.startswith("---"))
    return added, removed


def _component_from_test(filepath: str) -> str:
    """Extract component name from a test file path."""
    basename = os.path.basename(filepath)
    # Remove common test prefixes/suffixes
    name = basename
    for prefix in ("test_", "test."):
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break
    for suffix in ("_test.py", ".test.ts", ".test.js", ".test.tsx", ".test.jsx",
                    ".spec.ts", ".spec.js", ".spec.tsx", ".spec.jsx", ".py",
                    ".ts", ".js", ".tsx", ".jsx"):
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name or basename


def classify_changes(diff_output: str, changed_files: list[str]) -> list[dict]:
    """Classify changes into typed entries. Heuristic-based, NOT LLM-based.

    Rules:
    - New files (seen as 'new file mode') -> [observation] "Added <filename>"
    - Deleted files -> [observation] "Removed <filename>"
    - Config/infra files -> [observation]
    - Test files -> [observation] "Added/updated tests for <component>"
    - Multiple files in same directory -> group into one entry

    Each entry dict has: type, title, body, ref (starts at 0), why
    """
    entries = []
    handled = set()

    # Pass 1: New files
    for fp in changed_files:
        if _is_new_file(diff_output, fp):
            if _is_test_file(fp):
                component = _component_from_test(fp)
                added, _ = _get_line_counts(diff_output, fp)
                entries.append({
                    "type": "observation",
                    "title": f"Added tests for {component}",
                    "body": f"{fp} (+{added} lines)",
                    "ref": 0,
                    "why": "",
                })
            else:
                added, _ = _get_line_counts(diff_output, fp)
                entries.append({
                    "type": "observation",
                    "title": f"Added {fp}",
                    "body": f"New file (+{added} lines)",
                    "ref": 0,
                    "why": "",
                })
            handled.add(fp)

    # Pass 2: Deleted files
    for fp in changed_files:
        if fp in handled:
            continue
        if _is_deleted_file(diff_output, fp):
            _, removed = _get_line_counts(diff_output, fp)
            entries.append({
                "type": "observation",
                "title": f"Removed {fp}",
                "body": f"Deleted file (-{removed} lines)",
                "ref": 0,
                "why": "",
            })
            handled.add(fp)

    # Pass 3: Remaining files — group by directory
    remaining = [fp for fp in changed_files if fp not in handled]

    # Group by parent directory
    dir_groups: dict[str, list[str]] = {}
    for fp in remaining:
        parent = os.path.dirname(fp) or "."
        dir_groups.setdefault(parent, []).append(fp)

    for dirpath, files in dir_groups.items():
        # Check if all are test files
        test_files = [f for f in files if _is_test_file(f)]
        config_files = [f for f in files if _is_config_file(f)]
        other_files = [f for f in files if f not in test_files and f not in config_files]

        # Test file group
        if test_files:
            components = set()
            total_added = 0
            total_removed = 0
            for fp in test_files:
                components.add(_component_from_test(fp))
                a, r = _get_line_counts(diff_output, fp)
                total_added += a
                total_removed += r
            comp_str = ", ".join(sorted(components))
            entries.append({
                "type": "observation",
                "title": f"Updated tests for {comp_str}",
                "body": f"{len(test_files)} test file(s) (+{total_added}/-{total_removed} lines)",
                "ref": 0,
                "why": "",
            })

        # Config file group
        if config_files:
            if len(config_files) == 1:
                fp = config_files[0]
                a, r = _get_line_counts(diff_output, fp)
                entries.append({
                    "type": "observation",
                    "title": f"Updated config {fp}",
                    "body": f"(+{a}/-{r} lines)",
                    "ref": 0,
                    "why": "",
                })
            else:
                file_list = ", ".join(os.path.basename(f) for f in config_files)
                entries.append({
                    "type": "observation",
                    "title": f"Updated config files in {dirpath}",
                    "body": f"Files: {file_list}",
                    "ref": 0,
                    "why": "",
                })

        # Other files — group if multiple in same dir
        if other_files:
            if len(other_files) == 1:
                fp = other_files[0]
                a, r = _get_line_counts(diff_output, fp)
                entries.append({
                    "type": "observation",
                    "title": f"Modified {fp}",
                    "body": f"(+{a}/-{r} lines)",
                    "ref": 0,
                    "why": "",
                })
            else:
                total_added = 0
                total_removed = 0
                for fp in other_files:
                    a, r = _get_line_counts(diff_output, fp)
                    total_added += a
                    total_removed += r
                file_list = ", ".join(os.path.basename(f) for f in other_files)
                entries.append({
                    "type": "observation",
                    "title": f"Modified {len(other_files)} files in {dirpath}/",
                    "body": f"Files: {file_list} (+{total_added}/-{total_removed} lines)",
                    "ref": 0,
                    "why": "",
                })

    return entries


def merge_with_existing(new_entries: list[dict], existing_entries: list[dict]) -> list[dict]:
    """Merge new auto-generated entries with existing Day entries.

    - Don't duplicate: if an existing entry's title mentions the same file, skip the new one
    - Existing entries always take priority (human-written > auto-generated)
    - New entries get ref:0 (they haven't been referenced yet)
    - Returns combined list with existing first, then new entries
    """
    if not new_entries:
        return list(existing_entries)

    # Build a set of file paths mentioned in existing entries
    existing_text = " ".join(
        (e.get("title", "") + " " + e.get("body", "")).lower()
        for e in existing_entries
    )

    result = list(existing_entries)
    for entry in new_entries:
        # Extract file paths from the new entry title and body
        entry_text = (entry.get("title", "") + " " + entry.get("body", "")).lower()

        # Check if any specific file mentioned in the new entry is already covered
        # Look for file-like patterns (word.ext or path/word.ext)
        file_patterns = re.findall(r"[\w./\-]+\.\w+", entry_text)
        is_duplicate = False
        for fp in file_patterns:
            # Check if this file path appears in existing entry text
            if fp in existing_text:
                is_duplicate = True
                break

        if not is_duplicate:
            entry["ref"] = 0  # Ensure new entries start at ref:0
            result.append(entry)

    return result
