"""Deterministic succession protocol — no LLM required.

Implements the 8-step succession protocol as pure Python:
1. Freeze current state
2. Compress Dusk (shift tiers down)
3. Day → Dusk (categorize by ref score)
4. Dawn → Day (promote)
5. Seed new Dawn (git state + Dusk wisdom)
6. Vault check (auto-promote worthy entries)
7. Deviant check (file-path conflicts)
8. Ceremony (write all files, return report)
"""

import os
import re
import subprocess
from datetime import datetime, timezone

from core.constants import (
    DEVIANT_NUDGE_SESSIONS,
    DEVIANT_RESOLVE_SESSIONS,
    DUSK_LAYER1_MAX,
    DUSK_LAYER2_MAX,
    DUSK_LAYER3_MAX,
    ENTRY_TYPE_DECISION,
    ENTRY_TYPE_OBSERVATION,
    VAULT_MAX_LINES,
    VAULT_PROMOTION_SESSIONS,
    ruler_name,
)
from core.entries import (
    generate_epithet,
    parse_day_entries,
    parse_dusk_entries,
    serialize_day_entries,
    serialize_dusk_entries,
)
from core.briefing import generate_briefing
from core.state import (
    count_lines,
    read_dynasty_json,
    read_file_safe,
    write_dynasty_json,
    write_file_safe,
)


def _extract_file_paths(text: str) -> set[str]:
    """Extract file-path-like strings from text."""
    return set(re.findall(r"[\w./\-]+\.\w{1,10}", text))


def _run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


# ─── Step 2: Compress Dusk ─────────────────────────────────────────────

def compress_dusk(dusk_entries: list[dict], dynasty_num: int) -> tuple[list[dict], list[dict]]:
    """Shift existing Dusk entries down one tier. Returns (kept, demoted_to_lineage)."""
    kept = []
    demoted = []

    for entry in dusk_entries:
        layer = entry.get("layer", 1)
        entry_type = entry.get("type", ENTRY_TYPE_OBSERVATION)

        # Decrees are immune
        if entry.get("decree"):
            kept.append(dict(entry))
            continue

        if layer == 1:
            # Layer 1 → Layer 2
            new = dict(entry)
            new["layer"] = 2
            if entry_type == ENTRY_TYPE_DECISION:
                new["body"] = ""  # What: compressed away, title stays
            else:
                new["body"] = ""
            kept.append(new)

        elif layer == 2:
            # Layer 2 → Layer 3
            new = dict(entry)
            new["layer"] = 3
            kept.append(new)

        elif layer == 3:
            # Layer 3: demote if ref 0
            ref = entry.get("ref", 0)
            if ref == 0:
                demoted.append(dict(entry))
            else:
                kept.append(dict(entry))

    return kept, demoted


# ─── Step 3: Day → Dusk ────────────────────────────────────────────────

def day_to_dusk(day_entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """Categorize Day entries into Dusk Layer 1 or lineage. Returns (dusk_entries, demoted)."""
    dusk = []
    demoted = []

    for entry in day_entries:
        ref = entry.get("ref", 0)
        entry_type = entry.get("type", ENTRY_TYPE_OBSERVATION)

        if ref == 0 and entry_type != ENTRY_TYPE_DECISION:
            # Demote observations with ref=0 to lineage.
            # Decisions always survive — their Why: field is sacred.
            demoted.append(dict(entry))
            continue

        new = dict(entry)
        new["layer"] = 1

        if entry_type == ENTRY_TYPE_DECISION:
            # Why: always preserved. What: compressed for low ref.
            if ref <= 2:
                new["body"] = ""  # Compress What: away
        else:
            # Observations: one-liner for low ref
            if ref <= 2:
                new["body"] = ""

        dusk.append(new)

    return dusk, demoted


# ─── Step 5: Seed Dawn ─────────────────────────────────────────────────

def seed_dawn(
    branch: str,
    next_num: int,
    dusk_entries: list[dict],
) -> str:
    """Generate new Dawn content from git state and keyword-matched Dusk wisdom."""
    commits = _run_git("log", "--oneline", "-5")
    status = _run_git("status", "--short")

    lines = [
        f"# 🌅 Dawn — {ruler_name(next_num)}",
        "<!-- Staged for next succession -->",
        "",
        "## Git State",
        f"- Branch: {branch}",
        "- Recent commits:",
    ]

    if commits:
        for line in commits.split("\n")[:5]:
            lines.append(f"  - {line}")
    else:
        lines.append("  - (none)")

    if status:
        file_count = len([l for l in status.split("\n") if l.strip()])
        lines.append(f"- Uncommitted changes: yes ({file_count} files)")
    else:
        lines.append("- Uncommitted changes: no")

    lines.extend(["", "## Dusk Wisdom", "<!-- Keyword-matched entries from Dusk -->"])

    # Match Dusk entries by branch keywords and modified file paths
    match_terms = set(branch.replace("-", " ").replace("_", " ").split())
    if status:
        for line in status.split("\n"):
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                match_terms.update(parts[1].replace("/", " ").split())

    matched = []
    for entry in dusk_entries:
        text = (entry.get("title", "") + " " + entry.get("body", "")).lower()
        if any(term.lower() in text for term in match_terms if len(term) > 2):
            matched.append(entry)

    if matched:
        for entry in matched[:5]:
            etype = entry.get("type", ENTRY_TYPE_OBSERVATION)
            title = entry.get("title", "")
            lines.append(f"- [{etype}] {title}")
    else:
        lines.append("- (no matching wisdom)")

    return "\n".join(lines) + "\n"


# ─── Step 6: Vault Check ───────────────────────────────────────────────

def vault_check(
    dusk_entries: list[dict],
    vault_content: str,
    dynasty_num: int,
) -> tuple[str, list[dict]]:
    """Check for vault-worthy entries. Returns (updated_vault, updated_dusk)."""
    vault_lines = count_lines(vault_content)
    updated_dusk = list(dusk_entries)

    # Entries in layer 2+ with high ref scores are vault candidates
    for i, entry in enumerate(updated_dusk):
        if entry.get("ref", 0) >= VAULT_PROMOTION_SESSIONS and entry.get("layer", 1) >= 2:
            if vault_lines < VAULT_MAX_LINES:
                title = entry.get("title", "")
                vault_content += f"- {title}\n"
                vault_lines += 1
            else:
                updated_dusk[i] = dict(entry)
                updated_dusk[i]["title"] = f"[vault-candidate] {entry.get('title', '')}"

    return vault_content, updated_dusk


# ─── Step 7: Deviant Check ─────────────────────────────────────────────

def deviant_check(
    new_dusk_entries: list[dict],
    vault_content: str,
    existing_deviants: str,
) -> str:
    """Check for file-path conflicts between new Dusk entries and Vault."""
    vault_paths = _extract_file_paths(vault_content)
    if not vault_paths:
        return existing_deviants

    now = datetime.now(timezone.utc).isoformat()
    new_deviants = []

    for entry in new_dusk_entries:
        entry_text = entry.get("title", "") + " " + entry.get("body", "")
        entry_paths = _extract_file_paths(entry_text)
        conflicts = entry_paths & vault_paths
        if conflicts:
            for path in conflicts:
                desc = f"File {path} referenced in both Vault and Dusk entry '{entry.get('title', '')}'"
                new_deviants.append(
                    f"\n### [deviant] {desc}\n"
                    f"Filed: {now}\n"
                    f"Session: 1\n"
                    f"Status: unresolved\n"
                )

    # Nudge old deviants
    updated = existing_deviants
    if "Session:" in updated:
        lines = updated.split("\n")
        for i, line in enumerate(lines):
            match = re.match(r"Session: (\d+)", line)
            if match:
                count = int(match.group(1)) + 1
                lines[i] = f"Session: {count}"
                if count >= DEVIANT_RESOLVE_SESSIONS:
                    lines.insert(i + 1, f"🚨 Deviant unresolved for {DEVIANT_RESOLVE_SESSIONS}+ sessions — consider resolving")
                elif count >= DEVIANT_NUDGE_SESSIONS:
                    lines.insert(i + 1, f"⚠️ Deviant unresolved for {DEVIANT_NUDGE_SESSIONS}+ sessions")
        updated = "\n".join(lines)

    if new_deviants:
        updated += "\n".join(new_deviants)

    return updated


# ─── Step 8: Lineage Format ────────────────────────────────────────────

def format_lineage_entries(
    entries: list[dict],
    dynasty_num: int,
    branch: str,
    epithet: str | None = None,
    sessions: int = 0,
    start_date: str = "",
) -> str:
    """Format demoted entries for append to lineage.md.

    Output matches the format that parse_lineage_entries() expects:
      ## Claude N "epithet" (branch)
      Ruled: <start> to <end> | Sessions: N
      - [type] title — Why: reason
    """
    if not entries:
        return ""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start = start_date[:10] if start_date else now
    name = ruler_name(dynasty_num)
    epithet_str = f' "{epithet}"' if epithet else ""

    lines = [
        f"\n## {name}{epithet_str} ({branch})",
        f"Ruled: {start} to {now} | Sessions: {sessions}",
        "",
        "### Retired Entries",
    ]

    for entry in entries:
        etype = entry.get("type", ENTRY_TYPE_OBSERVATION)
        title = entry.get("title", "")
        why = entry.get("why", "")

        if why:
            lines.append(f"- [{etype}] {title} — Why: {why}")
        else:
            lines.append(f"- [{etype}] {title}")

    lines.append("")
    return "\n".join(lines)


# ─── Main Protocol ─────────────────────────────────────────────────────

def run_succession(
    dynasty_dir: str,
    project_root: str,
    branch: str,
    trigger_reason: str = "manual trigger",
) -> str:
    """Execute the full 8-step succession protocol. Returns the ceremony report."""

    # ── Step 1: Freeze ──────────────────────────────────────────────
    dynasty = read_dynasty_json(dynasty_dir)
    current = dynasty.get("current", 1)
    epithets = dynasty.get("epithets", {})

    day_content = read_file_safe(os.path.join(dynasty_dir, "day.md"))
    dusk_content = read_file_safe(os.path.join(dynasty_dir, "dusk.md"))
    dawn_content = read_file_safe(os.path.join(dynasty_dir, "dawn.md"))

    vault_path = os.path.join(project_root, ".empire", "vault.md")
    vault_content = read_file_safe(vault_path)

    memory_dir = os.path.dirname(dynasty_dir)
    lineage_path = os.path.join(memory_dir, "lineage.md")
    lineage_content = read_file_safe(lineage_path)
    deviants_path = os.path.join(memory_dir, "deviants.md")
    deviants_content = read_file_safe(deviants_path)

    day_entries = parse_day_entries(day_content)
    dusk_entries = parse_dusk_entries(dusk_content)

    # ── Step 2: Compress Dusk ───────────────────────────────────────
    compressed_dusk, dusk_demoted = compress_dusk(dusk_entries, current)

    # ── Step 3: Day → Dusk ──────────────────────────────────────────
    new_dusk, day_demoted = day_to_dusk(day_entries)
    all_demoted = dusk_demoted + day_demoted

    # Generate epithet for outgoing ruler
    epithet = generate_epithet(day_entries)

    # Merge: new Day entries go to Layer 1, compressed old stays in their layers
    final_dusk = new_dusk + compressed_dusk

    # ── Step 4: Dawn → Day ──────────────────────────────────────────
    new_current = current + 1
    now = datetime.now(timezone.utc).isoformat()

    # Parse Dawn for any useful entries, or create minimal Day
    dawn_lines = dawn_content.split("\n") if dawn_content else []
    dawn_items = [l.strip() for l in dawn_lines if l.strip().startswith("- ") and not l.strip().startswith("- Branch:") and not l.strip().startswith("- Recent") and not l.strip().startswith("- Uncommitted") and not l.strip().startswith("- Stashes") and "<!--" not in l]

    new_day_entries = []
    for item in dawn_items:
        text = item.lstrip("- ").strip()
        if text and text != "(none)" and text != "(no matching wisdom)":
            new_day_entries.append({
                "ref": 0,
                "type": ENTRY_TYPE_OBSERVATION,
                "title": text,
                "why": "",
                "body": "",
            })

    new_day_content = serialize_day_entries(
        new_day_entries,
        ruler_name(new_current),
        None,  # No epithet yet
        branch,
        now,
    )

    # ── Step 5: Seed new Dawn ───────────────────────────────────────
    new_dawn_content = seed_dawn(branch, new_current + 1, final_dusk)

    # ── Step 6: Vault check ─────────────────────────────────────────
    vault_content, final_dusk = vault_check(final_dusk, vault_content, new_current)

    # ── Step 7: Deviant check ───────────────────────────────────────
    deviants_content = deviant_check(new_dusk, vault_content, deviants_content)

    # ── Step 8: Ceremony — write files ──────────────────────────────

    # Serialize Dusk
    outgoing_name = ruler_name(current)
    new_dusk_content = serialize_dusk_entries(final_dusk, outgoing_name, epithet)

    # Write all files
    write_file_safe(os.path.join(dynasty_dir, "dusk.md"), new_dusk_content)
    write_file_safe(os.path.join(dynasty_dir, "day.md"), new_day_content)
    write_file_safe(os.path.join(dynasty_dir, "dawn.md"), new_dawn_content)

    # Append lineage
    lineage_addition = format_lineage_entries(
        all_demoted,
        dynasty_num=current,
        branch=branch,
        epithet=epithet,
        sessions=dynasty.get("sessions_since_succession", 0),
        start_date=dynasty.get("founded", ""),
    )
    if lineage_addition:
        if not lineage_content:
            lineage_content = f"# 📜 Lineage\n\n## Dynasty of Claude — {branch}\n"
        lineage_content += lineage_addition
        write_file_safe(lineage_path, lineage_content)

    # Write vault if changed
    write_file_safe(vault_path, vault_content)

    # Write deviants if changed
    if deviants_content:
        write_file_safe(deviants_path, deviants_content)

    # Update dynasty.json
    dynasty["current"] = new_current
    dynasty["last_succession"] = now
    dynasty["sessions_since_succession"] = 0
    epithets[str(current)] = epithet
    dynasty["epithets"] = epithets
    write_dynasty_json(dynasty_dir, dynasty)

    # Generate briefing for new Day
    briefing = generate_briefing(
        entries=new_day_entries,
        name=ruler_name(new_current),
        epithet=None,
        branch=branch,
    )
    write_file_safe(os.path.join(dynasty_dir, "day-briefing.md"), briefing)

    # ── Generate ceremony report ────────────────────────────────────
    vault_used = count_lines(vault_content)
    dev_unresolved = len([l for l in deviants_content.split("\n") if l.strip().startswith("- [ ]")]) if deviants_content else 0

    report_lines = [
        f"# Succession of {ruler_name(new_current)}",
        f"Branch: {branch} | Trigger: {trigger_reason}",
        "",
        "## Transitions",
        "",
    ]

    if all_demoted:
        report_lines.append(f"- {len(all_demoted)} entries demoted to lineage")
    report_lines.append(f"- {outgoing_name} \"{epithet}\" — Day to Dusk ({len(new_dusk)} entries kept, {len(day_demoted)} demoted)")
    report_lines.append(f"- {ruler_name(new_current)} — Dawn to Day ({len(new_day_entries)} entries)")
    report_lines.append(f"- {ruler_name(new_current + 1)} — born as Dawn")

    report_lines.extend([
        "",
        "## State",
        "",
        f"- Vault: {vault_used}/{VAULT_MAX_LINES} lines",
        f"- Deviants: {dev_unresolved} unresolved",
        f"- Dusk compressed: {len(compressed_dusk)} old entries shifted down",
        "",
        f"Long live {ruler_name(new_current)}. May they earn their name.",
    ])

    return "\n".join(report_lines)
