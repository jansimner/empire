"""Ancestor Oracle: Search lineage for relevant past decisions and wisdom."""

import re

# Common English stopwords to filter from keyword extraction
STOPWORDS = {
    "about", "above", "after", "again", "against", "also", "been", "before",
    "being", "below", "between", "both", "could", "does", "doing", "down",
    "during", "each", "from", "further", "have", "having", "here", "into",
    "itself", "just", "more", "most", "myself", "once", "only", "other",
    "over", "same", "should", "some", "such", "than", "that", "their",
    "them", "then", "there", "these", "they", "this", "those", "through",
    "under", "until", "very", "want", "were", "what", "when", "where",
    "which", "while", "will", "with", "would", "your", "working", "using",
    "need", "needs", "make", "made", "like", "used", "currently", "branch",
    "main", "none",
}


def parse_lineage_entries(content: str) -> list[dict]:
    """Parse lineage.md into structured entries.

    Format:
    ## Claude III "the Architect" (main)
    Ruled: 2026-03-05 to 2026-03-07 | Sessions: 8

    ### Retired Entries
    - [decision] Chose JWT RS256 — Why: asymmetric verification needed
    - [observation] Rate limiter applied globally

    Returns list of dicts with: ruler, epithet, branch, type, title, why
    """
    if not content.strip():
        return []

    entries = []
    current_ruler = ""
    current_epithet = ""
    current_branch = ""

    ruler_pattern = re.compile(
        r'^## (Claude \w+)\s+"([^"]+)"\s+\(([^)]+)\)',
    )
    entry_pattern = re.compile(
        r'^- \[(\w+)\]\s+(.+)',
    )

    for line in content.split("\n"):
        ruler_match = ruler_pattern.match(line)
        if ruler_match:
            current_ruler = ruler_match.group(1)
            current_epithet = ruler_match.group(2)
            current_branch = ruler_match.group(3)
            continue

        entry_match = entry_pattern.match(line)
        if entry_match and current_ruler:
            entry_type = entry_match.group(1)
            text = entry_match.group(2).strip()

            title = text
            why = ""

            # Extract inline Why: for decisions
            why_inline = re.search(r"\s*—\s*Why:\s*(.+)", text)
            if why_inline:
                why = why_inline.group(1).strip()
                title = text[: why_inline.start()].strip()

            entries.append({
                "ruler": current_ruler,
                "epithet": current_epithet,
                "branch": current_branch,
                "type": entry_type,
                "title": title,
                "why": why,
            })

    return entries


def search_lineage(lineage_content: str, keywords: list[str]) -> list[dict]:
    """Search lineage entries for keyword matches.

    Returns list of matching entries with attribution.
    Searches case-insensitively across titles, Why: fields, and body text.
    Requires 2+ keyword matches to avoid noise (same threshold as ref tracking).
    """
    if not lineage_content.strip() or not keywords:
        return []

    entries = parse_lineage_entries(lineage_content)
    matches = []

    keywords_lower = [k.lower() for k in keywords]

    for entry in entries:
        searchable = " ".join([
            entry.get("title", ""),
            entry.get("why", ""),
        ]).lower()

        matched_keywords = [k for k in keywords_lower if k in searchable]

        if len(matched_keywords) >= 2:
            result = dict(entry)
            result["keywords_matched"] = matched_keywords
            matches.append(result)

    return matches


def extract_topic_keywords(briefing: str, dawn: str, vault: str) -> list[str]:
    """Extract meaningful keywords from current context to match against lineage.

    Combines keywords from:
    - Day briefing (active work topics)
    - Dawn (staged context, git state)
    - Vault (project fundamentals)

    Filters to meaningful keywords (4+ chars, not stopwords).
    Returns top 10 most distinctive keywords.
    """
    combined = " ".join([briefing, dawn, vault])
    if not combined.strip():
        return []

    # Extract words, lowercase
    words = re.findall(r"[a-zA-Z]+", combined)
    words_lower = [w.lower() for w in words]

    # Filter: 4+ chars, not stopwords
    filtered = [
        w for w in words_lower
        if len(w) >= 4 and w not in STOPWORDS
    ]

    if not filtered:
        return []

    # Count frequency for ranking, then deduplicate preserving order by frequency
    freq: dict[str, int] = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    # Sort by frequency descending, then alphabetically for stability
    ranked = sorted(freq.keys(), key=lambda w: (-freq[w], w))

    return ranked[:10]


def format_ancestor_hint(matches: list[dict]) -> str:
    """Format lineage matches into a hint for SessionStart injection.

    If matches found, returns a short hint (2-3 lines) with topic keywords.
    If no matches, returns empty string.
    """
    if not matches:
        return ""

    # Collect unique matched keywords across all matches
    all_keywords: list[str] = []
    seen: set[str] = set()
    for m in matches:
        for kw in m.get("keywords_matched", []):
            if kw not in seen:
                all_keywords.append(kw)
                seen.add(kw)

    keyword_str = ", ".join(all_keywords)

    return (
        f"Ancestors may have wisdom on: {keyword_str}\n"
        f"   Use /empire lineage --search or ask me to consult the ancestors."
    )


def format_consultation_response(matches: list[dict], query: str) -> str:
    """Format a full consultation response when Claude actively queries lineage.

    Includes ruler attribution, Why: fields, and ceremonial formatting.
    """
    if not matches:
        return (
            f"Consulting the Ancestors on \"{query}\"...\n"
            f"\n"
            f"The lineage holds no wisdom on this topic."
        )

    lines = [
        f"Consulting the Ancestors on \"{query}\"...",
        "",
        f"Found {len(matches)} relevant entries from past rulers:",
        "",
    ]

    for m in matches:
        ruler = m.get("ruler", "Unknown")
        epithet = m.get("epithet", "")
        branch = m.get("branch", "")

        header = f"{ruler}"
        if epithet:
            header += f' "{epithet}"'
        if branch:
            header += f" ({branch})"

        entry_type = m.get("type", "observation")
        title = m.get("title", "")
        why = m.get("why", "")

        lines.append(f"### {header}")
        lines.append(f"[{entry_type}] {title}")
        if why:
            lines.append(f"Why: {why}")
        lines.append("")

    return "\n".join(lines)
