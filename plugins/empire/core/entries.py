import re
from core.constants import EPITHET_KEYWORDS, ENTRY_TYPE_DECISION, ENTRY_TYPE_OBSERVATION


def parse_day_entries(content: str) -> list[dict]:
    entries = []
    pattern = r"### \[ref:(\d+)\] (?:\[(\w+)\] )?(.+?)(?:\n([\s\S]*?))?(?=\n### |\n## |\Z)"
    for match in re.finditer(pattern, content):
        entry_type = match.group(2) or ENTRY_TYPE_OBSERVATION
        raw_body = match.group(4).strip() if match.group(4) else ""

        # Extract Why: and What: fields from body (for decisions)
        why = ""
        body = raw_body
        if entry_type == ENTRY_TYPE_DECISION:
            why_match = re.search(r"^Why:\s*(.+?)(?=^What:|\Z)", raw_body, re.MULTILINE | re.DOTALL)
            what_match = re.search(r"^What:\s*(.+?)$", raw_body, re.MULTILINE | re.DOTALL)
            if why_match:
                why = why_match.group(1).strip()
                body = ""  # Decision with Why: but no What: — body stays empty
            if what_match:
                body = what_match.group(1).strip()
            elif not why_match:
                body = raw_body  # No Why/What structure, keep as body

        entries.append({
            "ref": int(match.group(1)),
            "type": entry_type,
            "title": match.group(3).strip(),
            "why": why,
            "body": body,
        })
    return entries


def serialize_day_entries(
    entries: list[dict],
    name: str,
    epithet: str | None,
    branch: str,
    born: str,
) -> str:
    title_part = f"{name}"
    if epithet:
        title_part += f' "{epithet}"'
    lines = [
        f"# ☀️ Day — {title_part}",
        f"<!-- Branch: {branch} | Born: {born} -->",
        "",
        "## Entries",
        "",
    ]
    for entry in entries:
        entry_type = entry.get("type", ENTRY_TYPE_OBSERVATION)
        lines.append(f"### [ref:{entry['ref']}] [{entry_type}] {entry['title']}")
        if entry_type == ENTRY_TYPE_DECISION and entry.get("why"):
            lines.append(f"Why: {entry['why']}")
            if entry.get("body"):
                lines.append(f"What: {entry['body']}")
        elif entry.get("body"):
            lines.append(entry["body"])
        lines.append("")
    return "\n".join(lines)


def parse_dusk_entries(content: str) -> list[dict]:
    entries = []
    current_layer = 0
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Layer 1" in line:
            current_layer = 1
        elif "Layer 2" in line:
            current_layer = 2
        elif "Layer 3" in line:
            current_layer = 3
        elif current_layer > 0:
            # Layer 1: ### [ref:N] [type] title + Why/What body
            h3_match = re.match(r"### \[ref:(\d+)\] (?:\[(\w+)\] )?(.+)", line)
            if h3_match:
                entry_type = h3_match.group(2) or ENTRY_TYPE_OBSERVATION
                body_lines = []
                why = ""
                i += 1
                while i < len(lines) and not lines[i].startswith("#") and not lines[i].startswith("- [ref:"):
                    stripped = lines[i].strip()
                    if stripped.startswith("Why:"):
                        why = stripped[4:].strip()
                    elif stripped:
                        body_lines.append(stripped)
                    i += 1
                entries.append({
                    "layer": current_layer,
                    "ref": int(h3_match.group(1)),
                    "type": entry_type,
                    "title": h3_match.group(3).strip(),
                    "why": why,
                    "body": " ".join(body_lines),
                })
                continue
            # Layer 2/3: - [ref:N] [type] text (decisions preserve Why inline)
            li_match = re.match(r"- \[ref:(\d+)\] (?:\[(\w+)\] )?(.+)", line)
            if li_match:
                entry_type = li_match.group(2) or ENTRY_TYPE_OBSERVATION
                text = li_match.group(3).strip()
                why = ""
                # Decisions in layer 2/3 have inline Why: "title — Why: reason"
                why_inline = re.search(r"— Why: (.+)", text)
                if why_inline:
                    why = why_inline.group(1).strip()
                    text = text[:why_inline.start()].strip()
                entries.append({
                    "layer": current_layer,
                    "ref": int(li_match.group(1)),
                    "type": entry_type,
                    "title": text,
                    "why": why,
                    "body": "",
                })
        i += 1
    return entries


def serialize_dusk_entries(entries: list[dict], name: str, epithet: str | None) -> str:
    title_part = f"{name}"
    if epithet:
        title_part += f' "{epithet}"'
    lines = [f"# 🌙 Dusk — {title_part}", ""]

    for layer_num, label in [(1, "Layer 1 (detailed)"), (2, "Layer 2 (compressed)"), (3, "Layer 3 (one-liners)")]:
        layer_entries = [e for e in entries if e["layer"] == layer_num]
        if layer_entries:
            lines.append(f"## {label}")
            for entry in layer_entries:
                entry_type = entry.get("type", ENTRY_TYPE_OBSERVATION)
                if layer_num == 1:
                    lines.append(f"### [ref:{entry['ref']}] [{entry_type}] {entry['title']}")
                    if entry.get("why"):
                        lines.append(f"Why: {entry['why']}")
                    if entry.get("body"):
                        lines.append(entry["body"])
                    lines.append("")
                else:
                    # Decisions in layer 2/3 preserve Why inline
                    if entry_type == ENTRY_TYPE_DECISION and entry.get("why"):
                        lines.append(f"- [ref:{entry['ref']}] [{entry_type}] {entry['title']} — Why: {entry['why']}")
                    else:
                        lines.append(f"- [ref:{entry['ref']}] [{entry_type}] {entry['title']}")
            lines.append("")
    return "\n".join(lines)


def generate_epithet(entries: list[dict]) -> str:
    if not entries:
        return "the Brief"

    scores: dict[str, int] = {}
    for epithet, keywords in EPITHET_KEYWORDS.items():
        score = 0
        for entry in entries:
            text = (entry.get("title", "") + " " + entry.get("body", "")).lower()
            for kw in keywords:
                if kw in text:
                    score += 1
        if score > 0:
            scores[epithet] = score

    if not scores:
        return "the Journeyman"

    max_score = max(scores.values())
    winners = [k for k, v in scores.items() if v == max_score]
    if len(winners) > 2:
        return "the Journeyman"
    return winners[0]
