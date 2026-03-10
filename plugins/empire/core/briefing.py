from datetime import datetime, timezone

MAX_RECENT_ENTRIES = 10


def generate_briefing(
    entries: list[dict],
    name: str,
    epithet: str | None,
    branch: str,
    succession_suggested: bool = False,
    succession_reason: str | None = None,
) -> str:
    now = datetime.now(timezone.utc).isoformat()
    title = name
    if epithet:
        title += f' "{epithet}"'

    high_ref = [e for e in entries if e.get("ref", 0) >= 3]

    lines = [
        f"# ☀️ Briefing — {title}",
        f"Last updated: {now}",
        f"Branch: {branch}",
        "",
    ]

    # Always show recent entries so the next session knows what happened
    if entries:
        recent = entries[-MAX_RECENT_ENTRIES:]
        lines.append("## Recent work")
        for entry in recent:
            tag = entry.get("type", "observation")
            lines.append(f"- [{tag}] {entry['title']}")
        if len(entries) > MAX_RECENT_ENTRIES:
            lines.append(f"  ...and {len(entries) - MAX_RECENT_ENTRIES} earlier entries")
        lines.append("")

    if high_ref:
        lines.append("Hot topics: " + "; ".join(e["title"] for e in high_ref[:3]))

    lines.append(f"{len(entries)} Day entries, {len(high_ref)} high-reference.")

    if succession_suggested and succession_reason:
        lines.append(f"⚔️ Succession suggested: {succession_reason}")
    else:
        lines.append("Succession: not needed.")

    return "\n".join(lines)
