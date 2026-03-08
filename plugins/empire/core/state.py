import json
import os
from datetime import datetime, timezone
from core.constants import DAY_ENTRY_LIMIT, SESSIONS_BEFORE_SUCCESSION, STALE_RATIO_THRESHOLD


def read_file_safe(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, PermissionError):
        return ""


def write_file_safe(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def count_lines(content: str) -> int:
    if not content:
        return 0
    return len(content.strip().split("\n"))


def ensure_dynasty_dir(dynasty_dir: str) -> None:
    os.makedirs(dynasty_dir, exist_ok=True)


def read_dynasty_json(dynasty_dir: str) -> dict:
    path = os.path.join(dynasty_dir, "dynasty.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "current": 0,
            "branch": "main",
            "founded": datetime.now(timezone.utc).isoformat(),
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }


def write_dynasty_json(dynasty_dir: str, data: dict) -> None:
    ensure_dynasty_dir(dynasty_dir)
    path = os.path.join(dynasty_dir, "dynasty.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def check_succession_triggers(
    entries: list[dict],
    sessions_since_last: int,
) -> tuple[bool, str | None]:
    """Simple, transparent succession triggers. No weighted formula.
    Returns (should_succeed, reason) where reason is human-readable."""
    if not entries:
        return False, None

    # Trigger 1: Day has too many entries
    if len(entries) > DAY_ENTRY_LIMIT:
        return True, f"Day has >30 entries ({len(entries)})"

    # Trigger 2: Too many sessions without succession
    if sessions_since_last >= SESSIONS_BEFORE_SUCCESSION:
        return True, f"{sessions_since_last} sessions since last succession"

    # Trigger 3: Too many stale entries
    stale = [e for e in entries if e.get("ref", 0) == 0]
    stale_ratio = len(stale) / len(entries)
    if stale_ratio >= STALE_RATIO_THRESHOLD:
        return True, f"{int(stale_ratio * 100)}% of entries are stale ({len(stale)}/{len(entries)})"

    return False, None
