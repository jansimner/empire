"""Render the Empire status dashboard with proper emoji-aware alignment."""

import os
import unicodedata
from datetime import datetime, timezone

from core.constants import VAULT_MAX_LINES, ruler_name
from core.entries import parse_day_entries, parse_dusk_entries
from core.paths import get_current_branch, get_dynasty_dir, get_project_root
from core.state import (
    check_succession_triggers,
    count_lines,
    read_dynasty_json,
    read_file_safe,
)

# Box inner width (between the two │ characters)
BOX_WIDTH = 55


def display_width(s: str) -> int:
    """Calculate terminal display width of a string, handling emoji correctly."""
    w = 0
    for c in s:
        cp = ord(c)
        # Skip variation selectors (U+FE0E text, U+FE0F emoji) and ZWJ
        if cp in (0xFE0E, 0xFE0F, 0x200D):
            continue
        eaw = unicodedata.east_asian_width(c)
        cat = unicodedata.category(c)
        if eaw in ("W", "F"):
            w += 2
        elif cp > 0x1F000:  # Supplementary emoji (flags, symbols, etc.)
            w += 2
        elif 0x2600 <= cp <= 0x27BF:  # Miscellaneous symbols & dingbats
            w += 2
        elif cat == "Mn":  # Combining marks — zero width
            pass
        else:
            w += 1
    return w


def pad_right(s: str, width: int) -> str:
    """Pad string with spaces to reach target display width."""
    current = display_width(s)
    if current >= width:
        return s
    return s + " " * (width - current)


def box_line(content: str) -> str:
    """Wrap content in box borders, padded to BOX_WIDTH."""
    return "│" + pad_right(content, BOX_WIDTH) + "│"


def box_top() -> str:
    return "┌" + "─" * BOX_WIDTH + "┐"


def box_mid() -> str:
    return "├" + "─" * BOX_WIDTH + "┤"


def box_bottom() -> str:
    return "└" + "─" * BOX_WIDTH + "┘"


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
            "⚠️  No Empire found in this project.\n"
            "Run /empire init to found a new dynasty."
        )

    branch = get_current_branch()
    dynasty_dir = get_dynasty_dir(branch)
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
    day_epithet = epithets.get(str(current), "???")
    if day_epithet != "???":
        day_epithet = f'"{day_epithet}"'
    dusk_num = current - 1
    dusk_epithet = epithets.get(str(dusk_num), "???") if dusk_num >= 1 else "N/A"
    if dusk_epithet not in ("???", "N/A"):
        dusk_epithet = f'"{dusk_epithet}"'

    # Last succession
    last = dynasty.get("last_succession")
    last_str = "never" if last is None else relative_time(last)

    # Ruler names
    day_name = ruler_name(current)
    dawn_name = ruler_name(current + 1)
    dusk_name = ruler_name(dusk_num) if dusk_num >= 1 else "none"

    # Build lines
    lines = [box_top()]

    # Header
    lines.append(box_line(f"  👑 EMPIRE STATUS"))
    lines.append(box_line(f"  🌿 {branch} · Dynasty of Claude"))
    lines.append(box_mid())

    # Rulers — column-aligned
    dawn_left = f"🌅 Dawn:  {dawn_name}"
    dawn_mid = "???"
    dawn_right = f"{dawn_staged} staged"
    day_left = f"☀️  Day:   {day_name}"
    day_mid = day_epithet
    day_right = f"{len(day_entries)} entries"

    # Calculate column positions for alignment
    col1_w = max(display_width(dawn_left), display_width(day_left))
    col2_w = max(display_width(dawn_mid), display_width(day_mid))

    dawn_line = f"  {pad_right(dawn_left, col1_w)}  {pad_right(dawn_mid, col2_w)}  {dawn_right}"
    day_line = f"  {pad_right(day_left, col1_w)}  {pad_right(day_mid, col2_w)}  {day_right}"

    lines.append(box_line(dawn_line))
    lines.append(box_line(day_line))

    if dusk_num >= 1:
        dusk_left = f"🌙 Dusk:  {dusk_name}"
        dusk_right = f"{len(dusk_entries)} wisdom"
        dusk_line = f"  {pad_right(dusk_left, col1_w)}  {pad_right(dusk_epithet, col2_w)}  {dusk_right}"
        lines.append(box_line(dusk_line))
    else:
        lines.append(box_line("  🌙 Dusk:  none"))

    lines.append(box_mid())

    # Stats
    lines.append(box_line(f"  🏛️  Vault:    {vault_used}/{VAULT_MAX_LINES} lines"))
    lines.append(box_line(f"  ⚡ Deviants: {unresolved} unresolved"))
    lines.append(box_line(f"  📊 Pressure: {bar} {pressure_pct}%"))
    lines.append(box_line(f"  🔄 Last succession: {last_str}"))

    # Succession warning
    if triggered and reason:
        # Truncate reason if it would overflow
        prefix = "  ⚠️  Succession suggested: "
        max_reason = BOX_WIDTH - display_width(prefix)
        if display_width(reason) > max_reason:
            reason = reason[: max_reason - 3] + "..."
        lines.append(box_line(f"{prefix}{reason}"))

    lines.append(box_bottom())

    return "\n".join(lines)
