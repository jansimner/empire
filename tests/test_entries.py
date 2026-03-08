import pytest
from core.entries import (
    parse_day_entries,
    serialize_day_entries,
    parse_dusk_entries,
    serialize_dusk_entries,
    generate_epithet,
)


SAMPLE_DAY = """# ☀️ Day — Claude III "the Builder"
<!-- Branch: main | Born: 2026-03-08T14:30:00Z -->

## Entries

### [ref:5] [decision] Chose JWT RS256 over HS256
Why: Auth service needs asymmetric verification across microservices.
What: Implemented in auth.service.ts using jose library

### [ref:2] [observation] Fixed rate limiter gap on health endpoint
express-rate-limit middleware now applied globally before route matching.

### [ref:0] [observation] Considered Redis
Decided against it.
"""

SAMPLE_DUSK = """# 🌙 Dusk — Claude II "the Debugger"

## Layer 1 (detailed)
### [ref:4] [decision] Payment mutex strategy
Why: Concurrent checkout requests cause race conditions on inventory.
What: Mutex lock in payment.service.ts:142

## Layer 2 (compressed)
- [ref:2] [observation] Empty cart checkout returns 400
- [ref:2] [decision] Payment mutex — Why: concurrent checkout race conditions

## Layer 3 (one-liners)
- [ref:1] [observation] Prisma needs $disconnect on error
"""


def test_parse_day_entries_extracts_all():
    entries = parse_day_entries(SAMPLE_DAY)
    assert len(entries) == 3


def test_parse_day_entries_extracts_ref_scores():
    entries = parse_day_entries(SAMPLE_DAY)
    assert entries[0]["ref"] == 5
    assert entries[1]["ref"] == 2
    assert entries[2]["ref"] == 0


def test_parse_day_entries_extracts_type():
    entries = parse_day_entries(SAMPLE_DAY)
    assert entries[0]["type"] == "decision"
    assert entries[1]["type"] == "observation"


def test_parse_day_entries_extracts_title():
    entries = parse_day_entries(SAMPLE_DAY)
    assert entries[0]["title"] == "Chose JWT RS256 over HS256"


def test_parse_day_entries_extracts_why_field():
    entries = parse_day_entries(SAMPLE_DAY)
    assert "asymmetric verification" in entries[0]["why"]


def test_parse_day_entries_extracts_body():
    entries = parse_day_entries(SAMPLE_DAY)
    assert "auth.service.ts" in entries[0]["body"]


def test_serialize_day_entries_roundtrips():
    entries = parse_day_entries(SAMPLE_DAY)
    output = serialize_day_entries(entries, "Claude III", "the Builder", "main", "2026-03-08T14:30:00Z")
    re_parsed = parse_day_entries(output)
    assert len(re_parsed) == len(entries)
    assert re_parsed[0]["ref"] == entries[0]["ref"]
    assert re_parsed[0]["type"] == entries[0]["type"]
    assert re_parsed[0]["why"] == entries[0]["why"]


def test_parse_dusk_entries_extracts_layers():
    entries = parse_dusk_entries(SAMPLE_DUSK)
    layer1 = [e for e in entries if e["layer"] == 1]
    layer2 = [e for e in entries if e["layer"] == 2]
    layer3 = [e for e in entries if e["layer"] == 3]
    assert len(layer1) == 1
    assert len(layer2) == 2
    assert len(layer3) == 1


def test_parse_dusk_decision_preserves_why():
    entries = parse_dusk_entries(SAMPLE_DUSK)
    decisions = [e for e in entries if e.get("type") == "decision"]
    assert len(decisions) >= 1
    assert all("why" in d and d["why"] for d in decisions)


def test_generate_epithet_security_work():
    entries = [
        {"title": "Added JWT auth", "body": "token validation with csrf protection"},
        {"title": "Fixed auth bug", "body": "permission check was missing"},
    ]
    epithet = generate_epithet(entries)
    assert epithet == "the Gatekeeper"


def test_generate_epithet_mixed_work():
    entries = [
        {"title": "Added button", "body": "ui component"},
        {"title": "Fixed database", "body": "migration issue"},
        {"title": "Wrote docs", "body": "readme update"},
    ]
    epithet = generate_epithet(entries)
    assert epithet == "the Journeyman"


def test_generate_epithet_empty():
    epithet = generate_epithet([])
    assert epithet == "the Brief"
