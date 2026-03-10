import pytest
from core.briefing import generate_briefing, MAX_RECENT_ENTRIES
from core.entries import parse_day_entries


SAMPLE_DAY = """# ☀️ Day — Claude VI "the Gatekeeper"
<!-- Branch: main | Born: 2026-03-08T14:30:00Z -->

## Entries

### [ref:5] [decision] Added rate limiting to auth endpoints
Why: Prevent brute force attacks on login endpoint.
What: Implemented express-rate-limit, 100 req/15min per IP.

### [ref:3] [observation] Webhook signature validation
All Stripe webhooks verified with HMAC-SHA256.

### [ref:0] [observation] Considered Redis for session store
Decided against it for now.
"""


def test_generate_briefing_includes_summary():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
    )
    assert "Briefing" in briefing
    assert "Claude VI" in briefing
    assert "rate limiting" in briefing or "auth" in briefing


def test_generate_briefing_includes_succession_status():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
        succession_suggested=True,
        succession_reason="Day has >30 entries (35)",
    )
    assert ">30 entries" in briefing


def test_generate_briefing_includes_entry_count():
    entries = parse_day_entries(SAMPLE_DAY)
    briefing = generate_briefing(
        entries=entries,
        name="Claude VI",
        epithet="the Gatekeeper",
        branch="main",
    )
    assert "3" in briefing


def test_generate_briefing_empty_entries():
    briefing = generate_briefing(
        entries=[],
        name="Claude I",
        epithet=None,
        branch="main",
    )
    assert "Briefing" in briefing
    assert "0" in briefing
    assert "Recent work" not in briefing


def test_generate_briefing_always_shows_recent_entries():
    """All entries appear in briefing regardless of ref score."""
    entries = [
        {"ref": 0, "type": "observation", "title": "Fixed login bug"},
        {"ref": 0, "type": "observation", "title": "Updated README"},
    ]
    briefing = generate_briefing(
        entries=entries,
        name="Claude I",
        epithet=None,
        branch="main",
    )
    assert "Recent work" in briefing
    assert "Fixed login bug" in briefing
    assert "Updated README" in briefing


def test_generate_briefing_shows_hot_topics_for_high_ref():
    """High-ref entries get highlighted separately as hot topics."""
    entries = [
        {"ref": 5, "type": "decision", "title": "Chose PostgreSQL"},
        {"ref": 0, "type": "observation", "title": "Ran migrations"},
    ]
    briefing = generate_briefing(
        entries=entries,
        name="Claude II",
        epithet="the Architect",
        branch="main",
    )
    assert "Hot topics" in briefing
    assert "Chose PostgreSQL" in briefing
    assert "Ran migrations" in briefing


def test_generate_briefing_no_hot_topics_when_all_low_ref():
    """No hot topics section when nothing has high ref score."""
    entries = [
        {"ref": 0, "type": "observation", "title": "Minor fix"},
    ]
    briefing = generate_briefing(
        entries=entries,
        name="Claude I",
        epithet=None,
        branch="main",
    )
    assert "Hot topics" not in briefing
    assert "Minor fix" in briefing


def test_generate_briefing_caps_at_max_recent():
    """Only the most recent MAX_RECENT_ENTRIES entries are shown."""
    entries = [
        {"ref": 0, "type": "observation", "title": f"Entry {i}"}
        for i in range(15)
    ]
    briefing = generate_briefing(
        entries=entries,
        name="Claude V",
        epithet=None,
        branch="main",
    )
    # Should show the last MAX_RECENT_ENTRIES entries
    assert f"Entry {15 - MAX_RECENT_ENTRIES}" in briefing
    assert "Entry 14" in briefing
    # First entries should be truncated
    assert "Entry 0" not in briefing
    assert "5 earlier entries" in briefing


def test_generate_briefing_entry_type_tags():
    """Entry type tags (observation/decision) appear in the listing."""
    entries = [
        {"ref": 0, "type": "decision", "title": "Use TypeScript"},
        {"ref": 0, "type": "observation", "title": "Added tests"},
    ]
    briefing = generate_briefing(
        entries=entries,
        name="Claude I",
        epithet=None,
        branch="main",
    )
    assert "[decision] Use TypeScript" in briefing
    assert "[observation] Added tests" in briefing
