"""Render the Empire status dashboard as clean markdown."""

import os
from datetime import datetime, timezone

from core.constants import (
    DAY_ENTRY_LIMIT,
    SESSIONS_BEFORE_SUCCESSION,
    STALE_RATIO_THRESHOLD,
    VAULT_MAX_LINES,
    ruler_name,
)
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

    # Succession triggers
    triggered, reason = check_succession_triggers(day_entries, sessions)
    n_entries = len(day_entries)
    stale = [e for e in day_entries if e.get("ref", 0) == 0]
    stale_pct = int(len(stale) / n_entries * 100) if n_entries else 0
    stale_threshold_pct = int(STALE_RATIO_THRESHOLD * 100)

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

    # Entry summaries for Day ruler
    entry_summaries = []
    for e in day_entries:
        title = e.get("title", "").strip()
        if title:
            entry_summaries.append(title)

    # Stale trigger display
    if sessions < 3:
        stale_line = f"Stale: {stale_pct}% (inactive until session 3)"
    else:
        stale_line = f"Stale: {stale_pct}%/{stale_threshold_pct}%"

    if triggered:
        succession_status = f"**Due** — {reason} (last: {last_str})"
    else:
        succession_status = f"Not due (last: {last_str})"

    # Build output
    lines = [
        f"# \u269C Empire — {branch}",
        "",
        "---",
        "",
    ]

    # Day (current ruler — prominent)
    day_display = fmt_epithet(day_name, day_epithet)
    lines.append(f"\U0001F451 **{day_display}** — {len(day_entries)} entries")
    if entry_summaries:
        for s in entry_summaries:
            lines.append(f"  \u25B8 {s}")

    lines.append("")

    # Dawn & Dusk
    lines.append(f"\U0001F305 Dawn: {dawn_name} ({dawn_staged} staged)")
    if dusk_num >= 1:
        dusk_name = ruler_name(dusk_num)
        dusk_display = fmt_epithet(dusk_name, dusk_epithet)
        lines.append(f"\U0001F307 Dusk: {dusk_display} ({len(dusk_entries)} wisdom)")
    else:
        lines.append("\U0001F307 Dusk: none")

    lines.append("")
    lines.append("---")
    lines.append("")

    # State (compact single-line)
    lines.append(
        f"\U0001F4DC Vault: {vault_used}/{VAULT_MAX_LINES} lines"
        f" \u00B7 \u26A0 Deviants: {unresolved} unresolved"
    )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Succession — explicit triggers
    lines.append(f"\u2696 **Succession** — {succession_status}")
    lines.append(f"  \u25CB Entries: {n_entries}/{DAY_ENTRY_LIMIT}")
    lines.append(f"  \u25CB Sessions: {sessions}/{SESSIONS_BEFORE_SUCCESSION}")
    lines.append(f"  \u25CB {stale_line}")

    return "\n".join(lines)
