from datetime import datetime, timezone


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
    active_titles = [e["title"] for e in high_ref[:3]]

    lines = [
        f"# ☀️ Briefing — {title}",
        f"Last updated: {now}",
        f"Branch: {branch}",
        "",
    ]

    if active_titles:
        lines.append("Active work: " + "; ".join(active_titles))
    else:
        lines.append("No high-reference entries.")

    lines.append(f"{len(entries)} Day entries, {len(high_ref)} high-reference.")

    if succession_suggested and succession_reason:
        lines.append(f"⚔️ Succession suggested: {succession_reason}")
    else:
        lines.append("Succession: not needed.")

    return "\n".join(lines)
