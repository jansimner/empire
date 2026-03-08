import pytest
from core.briefing import generate_briefing
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
