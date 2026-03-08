"""Render the Empire status dashboard as clean markdown."""

import os
from datetime import datetime, timezone

from core.constants import VAULT_MAX_LINES, ruler_name
from core.entries import parse_day_entries, parse_dusk_entries
from core.paths import get_current_branch, get_project_root, resolve_dynasty_dir
from core.state import (
    check_succession_triggers,
    count_lines,
    read_dynasty_json,
    read_file_safe,
)


def relative_time(iso_str: str) -> str:
    """Convert ISO timestamp to human-readable relative time."""
    try:
        then = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        delta = now - then
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        return f"{days}d ago"
    except (ValueError, TypeError):
        return "unknown"


def render_dashboard() -> str:
    """Render the full Empire status dashboard."""
    project_root = get_project_root()
    if not project_root or not os.path.isdir(os.path.join(project_root, ".empire")):
        return (
            "No Empire found in this project.\n"
            "Run /empire init to found a new dynasty."
        )

    branch = get_current_branch()
    dynasty_dir = resolve_dynasty_dir(branch)
    dynasty = read_dynasty_json(dynasty_dir)

    current = dynasty.get("current", 1)
    sessions = dynasty.get("sessions_since_succession", 0)
    epithets = dynasty.get("epithets", {})

    # Vault
    vault_content = read_file_safe(os.path.join(project_root, ".empire", "vault.md"))
    vault_used = count_lines(vault_content)

    # Day entries
    day_content = read_file_safe(os.path.join(dynasty_dir, "day.md"))
    day_entries = parse_day_entries(day_content)

    # Dawn staged items
    dawn_content = read_file_safe(os.path.join(dynasty_dir, "dawn.md"))
    dawn_staged = len([l for l in dawn_content.split("\n") if l.strip().startswith("- ")])

    # Dusk wisdom
    dusk_content = read_file_safe(os.path.join(dynasty_dir, "dusk.md"))
    dusk_entries = parse_dusk_entries(dusk_content)

    # Deviants
    empire_mem = os.path.dirname(dynasty_dir)
    dev_content = read_file_safe(os.path.join(empire_mem, "deviants.md"))
    unresolved = len([l for l in dev_content.split("\n") if l.strip().startswith("- [ ]")])

    # Pressure
    triggered, reason = check_succession_triggers(day_entries, sessions)
    entry_pressure = min(len(day_entries) / 30.0, 1.0) if day_entries else 0.0
    session_pressure = min(sessions / 5.0, 1.0)
    stale = [e for e in day_entries if e.get("ref", 0) == 0]
    stale_pressure = (len(stale) / len(day_entries)) if day_entries else 0.0
    pressure = max(entry_pressure, session_pressure, stale_pressure)
    pressure_pct = int(pressure * 100)
    filled = round(pressure * 10)
    bar = "▓" * filled + "░" * (10 - filled)

    # Epithets
    day_epithet = epithets.get(str(current))
    dusk_num = current - 1
    dusk_epithet = epithets.get(str(dusk_num)) if dusk_num >= 1 else None

    # Last succession
    last = dynasty.get("last_succession")
    last_str = "never" if last is None else relative_time(last)

    # Ruler names
    day_name = ruler_name(current)
    dawn_name = ruler_name(current + 1)

    # Format epithet display
    def fmt_epithet(name: str, epithet: str | None) -> str:
        if epithet:
            return f'{name} "{epithet}"'
        return name

    # Build output
    lines = [
        f"# Empire — {branch}",
        "",
        "## Dynasty",
        "",
    ]

    # Dawn
    lines.append(f"- **Dawn:** {dawn_name} — {dawn_staged} staged")

    # Day
    day_display = fmt_epithet(day_name, day_epithet)
    lines.append(f"- **Day:** {day_display} — {len(day_entries)} entries")

    # Dusk
    if dusk_num >= 1:
        dusk_name = ruler_name(dusk_num)
        dusk_display = fmt_epithet(dusk_name, dusk_epithet)
        lines.append(f"- **Dusk:** {dusk_display} — {len(dusk_entries)} wisdom")
    else:
        lines.append("- **Dusk:** none")

    lines.append("")
    lines.append("## State")
    lines.append("")
    lines.append(f"- **Vault:** {vault_used}/{VAULT_MAX_LINES} lines")
    lines.append(f"- **Deviants:** {unresolved} unresolved")
    lines.append(f"- **Pressure:** {bar} {pressure_pct}%")
    lines.append(f"- **Last succession:** {last_str}")

    if triggered and reason:
        lines.append("")
        lines.append(f"**Succession suggested:** {reason}")

    return "\n".join(lines)
