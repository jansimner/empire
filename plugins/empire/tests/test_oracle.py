import pytest
from core.oracle import (
    parse_lineage_entries,
    search_lineage,
    extract_topic_keywords,
    format_ancestor_hint,
    format_consultation_response,
)


SAMPLE_LINEAGE = """## Claude III "the Architect" (main)
Ruled: 2026-03-05 to 2026-03-07 | Sessions: 8

### Retired Entries
- [decision] Chose JWT RS256 over HS256 — Why: asymmetric verification needed
- [observation] Rate limiter applied globally

## Claude II "the Builder" (main)
Ruled: 2026-03-02 to 2026-03-05 | Sessions: 12

### Retired Entries
- [decision] Chose PostgreSQL over MongoDB — Why: relational data model with complex joins
- [observation] Set up CI pipeline with GitHub Actions
"""


def test_parse_lineage_entries():
    """Parse lineage format into structured entries."""
    entries = parse_lineage_entries(SAMPLE_LINEAGE)
    assert len(entries) == 4


def test_parse_lineage_extracts_ruler_and_epithet():
    """Each entry attributed to correct ruler."""
    entries = parse_lineage_entries(SAMPLE_LINEAGE)
    architects = [e for e in entries if e["ruler"] == "Claude III"]
    assert len(architects) == 2
    assert all(e["epithet"] == "the Architect" for e in architects)

    builders = [e for e in entries if e["ruler"] == "Claude II"]
    assert len(builders) == 2
    assert all(e["epithet"] == "the Builder" for e in builders)


def test_parse_lineage_preserves_why():
    """Decision entries have Why: field extracted."""
    entries = parse_lineage_entries(SAMPLE_LINEAGE)
    jwt_entry = [e for e in entries if "JWT" in e["title"]][0]
    assert jwt_entry["why"] == "asymmetric verification needed"
    assert jwt_entry["type"] == "decision"

    pg_entry = [e for e in entries if "PostgreSQL" in e["title"]][0]
    assert pg_entry["why"] == "relational data model with complex joins"


def test_parse_lineage_extracts_branch():
    """Branch info extracted from ruler header."""
    entries = parse_lineage_entries(SAMPLE_LINEAGE)
    assert all(e["branch"] == "main" for e in entries)


def test_parse_lineage_observation_has_no_why():
    """Observation entries have empty why field."""
    entries = parse_lineage_entries(SAMPLE_LINEAGE)
    obs = [e for e in entries if e["type"] == "observation"]
    assert len(obs) == 2
    assert all(e["why"] == "" for e in obs)


def test_search_lineage_finds_keyword_matches():
    """Search for 'jwt auth' related keywords finds Claude III's RS256 decision."""
    matches = search_lineage(SAMPLE_LINEAGE, ["jwt", "asymmetric", "verification"])
    assert len(matches) >= 1
    jwt_match = [m for m in matches if "JWT" in m["title"]]
    assert len(jwt_match) == 1
    assert jwt_match[0]["ruler"] == "Claude III"
    assert "jwt" in jwt_match[0]["keywords_matched"] or "asymmetric" in jwt_match[0]["keywords_matched"]


def test_search_lineage_requires_two_keywords():
    """Single keyword match alone doesn't return results (noise threshold)."""
    # 'limiter' only appears in one entry's title — only 1 keyword match
    matches = search_lineage(SAMPLE_LINEAGE, ["limiter"])
    assert len(matches) == 0


def test_search_lineage_no_matches():
    """Unrelated keywords return empty list."""
    matches = search_lineage(SAMPLE_LINEAGE, ["kubernetes", "terraform", "ansible"])
    assert len(matches) == 0


def test_search_lineage_case_insensitive():
    """Search is case-insensitive."""
    matches = search_lineage(SAMPLE_LINEAGE, ["JWT", "ASYMMETRIC"])
    assert len(matches) >= 1


def test_extract_topic_keywords():
    """Extracts meaningful 4+ char keywords from context."""
    briefing = "Working on authentication module and JWT token handling"
    dawn = ""
    vault = "TypeScript + NestJS backend"
    keywords = extract_topic_keywords(briefing, dawn, vault)
    assert isinstance(keywords, list)
    assert len(keywords) <= 10
    # All keywords should be 4+ chars
    assert all(len(k) >= 4 for k in keywords)
    # Should include meaningful words
    assert "authentication" in keywords or "module" in keywords or "token" in keywords


def test_extract_topic_keywords_filters_stopwords():
    """Stopwords and short words are filtered out."""
    briefing = "Working on the new auth feature for this project"
    keywords = extract_topic_keywords(briefing, "", "")
    # 'the', 'for', 'this', 'on' should be filtered (< 4 chars or stopwords)
    assert "the" not in keywords
    assert "for" not in keywords
    assert "this" not in keywords


def test_extract_topic_keywords_empty_input():
    """Empty inputs return empty keyword list."""
    keywords = extract_topic_keywords("", "", "")
    assert keywords == []


def test_extract_topic_keywords_limits_to_ten():
    """Returns at most 10 keywords."""
    long_text = " ".join(f"keyword{i}thing" for i in range(50))
    keywords = extract_topic_keywords(long_text, "", "")
    assert len(keywords) <= 10


def test_format_ancestor_hint_with_matches():
    """Hint includes topic keywords and ruler attribution."""
    matches = [
        {
            "ruler": "Claude III",
            "epithet": "the Architect",
            "branch": "main",
            "type": "decision",
            "title": "Chose JWT RS256 over HS256",
            "why": "asymmetric verification needed",
            "keywords_matched": ["jwt", "auth"],
        },
    ]
    hint = format_ancestor_hint(matches)
    assert hint  # Non-empty
    assert "Ancestor" in hint or "ancestor" in hint or "wisdom" in hint
    assert "JWT" in hint or "jwt" in hint.lower()


def test_format_ancestor_hint_empty_on_no_matches():
    """No matches returns empty string."""
    hint = format_ancestor_hint([])
    assert hint == ""


def test_format_consultation_response():
    """Full consultation includes ruler attribution and Why: fields."""
    matches = [
        {
            "ruler": "Claude III",
            "epithet": "the Architect",
            "branch": "main",
            "type": "decision",
            "title": "Chose JWT RS256 over HS256",
            "why": "asymmetric verification needed",
            "keywords_matched": ["jwt", "auth"],
        },
        {
            "ruler": "Claude II",
            "epithet": "the Builder",
            "branch": "main",
            "type": "observation",
            "title": "Rate limiter applied globally",
            "why": "",
            "keywords_matched": ["rate", "limiter"],
        },
    ]
    response = format_consultation_response(matches, "authentication")
    assert "Claude III" in response
    assert "the Architect" in response
    assert "asymmetric verification needed" in response
    assert "Claude II" in response
    assert "the Builder" in response
    assert "authentication" in response


def test_format_consultation_response_empty():
    """Empty matches produce a 'no results' response."""
    response = format_consultation_response([], "obscure topic")
    assert response  # Should still return something
    assert "no" in response.lower() or "nothing" in response.lower() or "empty" in response.lower()


def test_parse_lineage_empty_content():
    """Empty lineage content returns empty list."""
    entries = parse_lineage_entries("")
    assert entries == []


def test_search_lineage_empty_content():
    """Empty lineage content returns no matches."""
    matches = search_lineage("", ["jwt", "auth"])
    assert matches == []
