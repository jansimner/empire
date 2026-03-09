"""Integration tests: full init + session lifecycle in a temp directory."""

import json
import os
import pytest

from hooks.session_start import build_briefing_output
from core.ref_tracker import apply_ref_cache
from core.paths import reset_project_root_cache
from core.entries import (
    parse_day_entries,
    serialize_day_entries,
    parse_dusk_entries,
    serialize_dusk_entries,
    generate_epithet,
)
from core.ref_tracker import score_entries_against_content, load_ref_cache, save_ref_cache
from core.briefing import generate_briefing
from core.state import (
    read_dynasty_json,
    write_dynasty_json,
    read_file_safe,
    write_file_safe,
    check_succession_triggers,
    ensure_dynasty_dir,
)
from core.paths import sanitize_branch_name, get_dynasty_dir


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_project_root_cache()
    yield
    reset_project_root_cache()


BRANCH = "main"
FOUNDED = "2026-03-08T10:00:00Z"


@pytest.fixture
def empire_env(tmp_path):
    """Set up a full empire environment in tmp_path."""
    # Fake project root with .empire dir
    empire_dir = tmp_path / ".empire"
    empire_dir.mkdir()

    vault_path = empire_dir / "vault.md"
    vault_path.write_text(
        "# Vault\n- TypeScript + NestJS backend\n- Prisma ORM for database\n- React frontend"
    )

    # Dynasty dir (simulated — we use tmp_path directly instead of ~/.claude)
    dynasty_dir = tmp_path / "dynasty" / "main"
    dynasty_dir.mkdir(parents=True)

    dynasty_data = {
        "current": 1,
        "branch": BRANCH,
        "founded": FOUNDED,
        "last_succession": None,
        "sessions_since_succession": 0,
        "epithets": {},
    }
    write_dynasty_json(str(dynasty_dir), dynasty_data)

    day_path = dynasty_dir / "day.md"
    day_path.write_text(
        "# \u2600\ufe0f Day \u2014 Claude 1\n<!-- Branch: main | Born: 2026-03-08T10:00:00Z -->\n\n## Entries\n"
    )

    dawn_path = dynasty_dir / "dawn.md"
    dawn_path.write_text("## Staged items\n- Consider adding rate limiting\n")

    briefing_path = dynasty_dir / "day-briefing.md"

    return {
        "project_root": str(tmp_path),
        "empire_dir": str(empire_dir),
        "vault_path": str(vault_path),
        "dynasty_dir": str(dynasty_dir),
        "day_path": str(day_path),
        "dawn_path": str(dawn_path),
        "briefing_path": str(briefing_path),
        "cache_path": str(dynasty_dir / "ref_cache.json"),
    }


def test_session_start_outputs_vault_and_briefing(empire_env):
    """SessionStart: build_briefing_output includes vault content."""
    vault = read_file_safe(empire_env["vault_path"])
    dynasty = read_dynasty_json(empire_env["dynasty_dir"])
    output = build_briefing_output(
        vault=vault,
        briefing="",
        dynasty=dynasty,
        branch=BRANCH,
    )
    # Vault exists, briefing file doesn't yet — should still output vault
    assert "Vault" in output
    assert "TypeScript" in output
    assert "Claude I" in output


def test_session_start_with_briefing(empire_env):
    """SessionStart: includes briefing when both vault and briefing exist."""
    vault = read_file_safe(empire_env["vault_path"])
    briefing = "# Briefing\nActive work: auth system\n2 Day entries."
    dynasty = read_dynasty_json(empire_env["dynasty_dir"])
    output = build_briefing_output(
        vault=vault,
        briefing=briefing,
        dynasty=dynasty,
        branch=BRANCH,
    )
    assert "Vault" in output
    assert "auth system" in output
    assert "Briefing" in output


def test_day_entries_serialize_and_parse(empire_env):
    """Write day.md with entries using serialize, then parse back."""
    entries = [
        {
            "ref": 0,
            "type": "decision",
            "title": "Chose PostgreSQL over MySQL",
            "why": "Better JSON support and full-text search for our use case.",
            "body": "Updated prisma/schema.prisma provider to postgresql",
        },
        {
            "ref": 0,
            "type": "observation",
            "title": "Rate limiter added to auth endpoints",
            "why": "",
            "body": "express-rate-limit in middleware/rate-limit.ts, 100 req/15min",
        },
        {
            "ref": 0,
            "type": "observation",
            "title": "Fixed CORS config for staging",
            "why": "",
            "body": "Added staging.example.com to allowed origins in config/cors.ts",
        },
    ]

    day_content = serialize_day_entries(entries, "Claude 1", None, BRANCH, FOUNDED)
    write_file_safe(empire_env["day_path"], day_content)

    parsed = parse_day_entries(read_file_safe(empire_env["day_path"]))
    assert len(parsed) == 3
    assert parsed[0]["type"] == "decision"
    assert parsed[0]["title"] == "Chose PostgreSQL over MySQL"
    assert "JSON support" in parsed[0]["why"]
    assert "schema.prisma" in parsed[0]["body"]
    assert parsed[1]["type"] == "observation"
    assert parsed[2]["title"] == "Fixed CORS config for staging"


def test_ref_tracker_scores_and_cache(empire_env):
    """PostToolUse: score entries against tool output, save to ref cache."""
    entries = [
        {
            "ref": 0,
            "type": "decision",
            "title": "Chose PostgreSQL over MySQL",
            "why": "Better JSON support.",
            "body": "Updated prisma/schema.prisma provider to postgresql",
        },
        {
            "ref": 0,
            "type": "observation",
            "title": "Rate limiter added to auth endpoints",
            "why": "",
            "body": "express-rate-limit in middleware/rate-limit.ts, 100 req/15min",
        },
        {
            "ref": 0,
            "type": "observation",
            "title": "Fixed CORS config for staging",
            "why": "",
            "body": "Added staging.example.com to allowed origins in config/cors.ts",
        },
    ]

    # Simulate tool output that references a file from entry 1
    tool_content = "Edited middleware/rate-limit.ts to increase limit to 200 req/15min"
    scores = score_entries_against_content(entries, tool_content)

    # Entry 1 should score highest (exact file path match = tier 1)
    assert scores[1] >= 2  # REF_TIER1_SCORE
    # Entry 0 should score 0 (no file or keyword overlap)
    assert scores[0] == 0

    # Save non-zero scores to ref cache
    cache = {str(k): v for k, v in scores.items() if v > 0}
    save_ref_cache(empire_env["cache_path"], cache)

    loaded = load_ref_cache(empire_env["cache_path"])
    assert loaded == cache


def test_stop_hook_apply_ref_cache_and_briefing(empire_env):
    """Stop hook: load ref cache, apply to entries, generate briefing."""
    entries = [
        {"ref": 0, "type": "decision", "title": "Chose PostgreSQL over MySQL",
         "why": "Better JSON support.", "body": "Updated prisma/schema.prisma"},
        {"ref": 0, "type": "observation", "title": "Rate limiter added",
         "why": "", "body": "middleware/rate-limit.ts"},
        {"ref": 0, "type": "observation", "title": "Fixed CORS config",
         "why": "", "body": "config/cors.ts"},
    ]

    # Simulate a ref cache from post_tool_use
    cache = {"1": 2, "2": 1}
    save_ref_cache(empire_env["cache_path"], cache)

    # Apply ref cache
    loaded_cache = load_ref_cache(empire_env["cache_path"])
    updated = apply_ref_cache(entries, loaded_cache)

    assert updated[0]["ref"] == 0  # untouched
    assert updated[1]["ref"] == 2  # was 0, cache added 2
    assert updated[2]["ref"] == 1  # was 0, cache added 1

    # Check succession triggers — few entries, 0 sessions, should be False
    should_succeed, reason = check_succession_triggers(updated, sessions_since_last=0)
    assert should_succeed is False
    assert reason is None

    # Generate briefing
    briefing = generate_briefing(
        entries=updated,
        name="Claude 1",
        epithet=None,
        branch=BRANCH,
        succession_suggested=should_succeed,
        succession_reason=reason,
    )
    assert "Briefing" in briefing
    assert "Claude 1" in briefing
    assert "3 Day entries" in briefing
    assert "Succession: not needed" in briefing


def test_stop_hook_succession_triggers(empire_env):
    """Succession triggers fire when conditions are met."""
    # Many sessions without succession
    entries = [{"ref": 1, "type": "observation", "title": "Some work", "body": "", "why": ""}]
    should, reason = check_succession_triggers(entries, sessions_since_last=6)
    assert should is True
    assert "sessions" in reason

    # Too many entries
    many_entries = [{"ref": 1, "type": "observation", "title": f"entry {i}", "body": "", "why": ""} for i in range(35)]
    should, reason = check_succession_triggers(many_entries, sessions_since_last=0)
    assert should is True
    assert ">30" in reason

    # Too many stale entries (all ref 0)
    stale_entries = [{"ref": 0, "type": "observation", "title": f"stale {i}", "body": "", "why": ""} for i in range(10)]
    should, reason = check_succession_triggers(stale_entries, sessions_since_last=0)
    assert should is True
    assert "stale" in reason.lower()


def test_day_roundtrip_modify_and_reparse(empire_env):
    """Roundtrip: parse day.md, modify entries, serialize, re-parse — data integrity."""
    entries = [
        {"ref": 2, "type": "decision", "title": "Use Redis for caching",
         "why": "High read traffic on product catalog needs sub-ms latency.",
         "body": "Configured in services/cache.service.ts"},
        {"ref": 5, "type": "observation", "title": "API response times improved",
         "why": "", "body": "p99 dropped from 230ms to 45ms after caching layer"},
        {"ref": 0, "type": "observation", "title": "Considered CDN for static assets",
         "why": "", "body": "Decided to evaluate next sprint"},
    ]

    # Serialize and write
    content = serialize_day_entries(entries, "Claude 1", None, BRANCH, FOUNDED)
    write_file_safe(empire_env["day_path"], content)

    # Parse back
    parsed = parse_day_entries(read_file_safe(empire_env["day_path"]))
    assert len(parsed) == 3

    # Modify: bump a ref score, change a title
    parsed[2]["ref"] = 3
    parsed[2]["title"] = "CDN evaluation scheduled"

    # Re-serialize with epithet
    content2 = serialize_day_entries(parsed, "Claude 1", "the Builder", BRANCH, FOUNDED)
    write_file_safe(empire_env["day_path"], content2)

    # Re-parse and verify
    final = parse_day_entries(read_file_safe(empire_env["day_path"]))
    assert len(final) == 3
    assert final[0]["ref"] == 2
    assert final[0]["type"] == "decision"
    assert "sub-ms latency" in final[0]["why"]
    assert final[1]["ref"] == 5
    assert final[2]["ref"] == 3
    assert final[2]["title"] == "CDN evaluation scheduled"


def test_dusk_entries_roundtrip(empire_env):
    """Dusk: create entries across layers, serialize, re-parse — layers and Why: preserved."""
    dusk_entries = [
        {"layer": 1, "ref": 4, "type": "decision", "title": "Payment mutex strategy",
         "why": "Concurrent checkout causes race conditions on inventory.",
         "body": "Mutex lock in payment.service.ts:142"},
        {"layer": 2, "ref": 2, "type": "observation", "title": "Empty cart returns 400",
         "why": "", "body": ""},
        {"layer": 2, "ref": 2, "type": "decision", "title": "Payment mutex",
         "why": "concurrent checkout race conditions", "body": ""},
        {"layer": 3, "ref": 1, "type": "observation", "title": "Prisma needs $disconnect on error",
         "why": "", "body": ""},
    ]

    content = serialize_dusk_entries(dusk_entries, "Claude II", "the Debugger")
    dusk_path = os.path.join(empire_env["dynasty_dir"], "dusk.md")
    write_file_safe(dusk_path, content)

    parsed = parse_dusk_entries(read_file_safe(dusk_path))

    layer1 = [e for e in parsed if e["layer"] == 1]
    layer2 = [e for e in parsed if e["layer"] == 2]
    layer3 = [e for e in parsed if e["layer"] == 3]

    assert len(layer1) == 1
    assert len(layer2) == 2
    assert len(layer3) == 1

    # Layer 1 decision preserves Why
    assert layer1[0]["type"] == "decision"
    assert "race conditions" in layer1[0]["why"]
    assert layer1[0]["ref"] == 4

    # Layer 2 decision preserves Why inline
    l2_decisions = [e for e in layer2 if e["type"] == "decision"]
    assert len(l2_decisions) == 1
    assert "concurrent checkout" in l2_decisions[0]["why"]

    # Layer 3 is observation
    assert layer3[0]["type"] == "observation"
    assert "Prisma" in layer3[0]["title"]


def test_dynasty_json_roundtrip(empire_env):
    """Dynasty JSON: write and read — all fields roundtrip correctly."""
    dynasty_data = {
        "current": 3,
        "branch": "feature/payments",
        "founded": "2026-01-15T08:00:00Z",
        "last_succession": "2026-03-01T12:00:00Z",
        "sessions_since_succession": 7,
        "epithets": {
            "1": "the Builder",
            "2": "the Debugger",
            "3": "the Gatekeeper",
        },
    }

    dynasty_dir = os.path.join(empire_env["dynasty_dir"], "sub")
    ensure_dynasty_dir(dynasty_dir)
    write_dynasty_json(dynasty_dir, dynasty_data)

    loaded = read_dynasty_json(dynasty_dir)
    assert loaded["current"] == 3
    assert loaded["branch"] == "feature/payments"
    assert loaded["founded"] == "2026-01-15T08:00:00Z"
    assert loaded["last_succession"] == "2026-03-01T12:00:00Z"
    assert loaded["sessions_since_succession"] == 7
    assert loaded["epithets"]["1"] == "the Builder"
    assert loaded["epithets"]["2"] == "the Debugger"
    assert loaded["epithets"]["3"] == "the Gatekeeper"


def test_epithet_generation_themed_work(empire_env):
    """Epithet: entries with clear theme produce the correct epithet."""
    # All test-related work should yield "the Sentinel"
    entries = [
        {"title": "Added unit tests for payment flow", "body": "jest test coverage now at 85%"},
        {"title": "Playwright spec for checkout", "body": "e2e test with assert on final total"},
        {"title": "Fixed flaky vitest in CI", "body": "resolved timing issue in spec"},
    ]
    assert generate_epithet(entries) == "the Sentinel"

    # All refactoring work should yield "the Reformer"
    entries_refactor = [
        {"title": "Refactor auth module", "body": "extract token validation to separate service"},
        {"title": "Simplify error handling", "body": "restructure catch blocks"},
        {"title": "Rename user model fields", "body": "clean up legacy naming convention"},
    ]
    assert generate_epithet(entries_refactor) == "the Reformer"

    # Empty entries
    assert generate_epithet([]) == "the Brief"


def test_full_lifecycle_end_to_end(empire_env):
    """End-to-end: init -> write entries -> score refs -> apply cache -> briefing -> succession check."""
    # 1. Verify initial state via session start
    vault = read_file_safe(empire_env["vault_path"])
    dynasty = read_dynasty_json(empire_env["dynasty_dir"])
    output = build_briefing_output(
        vault=vault,
        briefing="",
        dynasty=dynasty,
        branch=BRANCH,
    )
    assert "Claude I" in output

    # 2. Write day entries
    entries = [
        {"ref": 0, "type": "decision", "title": "Chose PostgreSQL over MySQL",
         "why": "Better JSON support for our document-heavy schema.",
         "body": "Updated prisma/schema.prisma provider to postgresql"},
        {"ref": 0, "type": "observation", "title": "Rate limiter added to auth endpoints",
         "why": "", "body": "express-rate-limit in middleware/rate-limit.ts"},
        {"ref": 0, "type": "observation", "title": "Fixed CORS config",
         "why": "", "body": "config/cors.ts updated for staging domain"},
    ]
    day_content = serialize_day_entries(entries, "Claude 1", None, BRANCH, FOUNDED)
    write_file_safe(empire_env["day_path"], day_content)

    # 3. Simulate tool uses that touch files from multiple entries
    # First tool use touches rate-limit.ts (entry 1)
    scores1 = score_entries_against_content(entries, "Edited middleware/rate-limit.ts")
    assert scores1[1] >= 2  # Exact file match
    # Second tool use touches prisma/schema.prisma (entry 0) and config/cors.ts (entry 2)
    scores2 = score_entries_against_content(entries, "Updated prisma/schema.prisma and config/cors.ts")
    assert scores2[0] >= 2  # Exact file match for entry 0
    assert scores2[2] >= 2  # Exact file match for entry 2

    # Merge scores and save cache
    merged = {}
    for scores in (scores1, scores2):
        for k, v in scores.items():
            if v > 0:
                merged[str(k)] = merged.get(str(k), 0) + v
    save_ref_cache(empire_env["cache_path"], merged)

    # 4. Stop hook: apply cache
    loaded_cache = load_ref_cache(empire_env["cache_path"])
    entries = apply_ref_cache(entries, loaded_cache)
    assert entries[0]["ref"] >= 2  # prisma/schema.prisma match
    assert entries[1]["ref"] >= 2  # rate-limit.ts match
    assert entries[2]["ref"] >= 2  # cors.ts match

    # 5. Generate briefing — no stale entries now, so no succession
    should_succeed, reason = check_succession_triggers(entries, sessions_since_last=0)
    assert should_succeed is False

    briefing = generate_briefing(
        entries=entries, name="Claude 1", epithet=None,
        branch=BRANCH, succession_suggested=False, succession_reason=None,
    )
    write_file_safe(empire_env["briefing_path"], briefing)
    assert "Briefing" in briefing
    assert "3 Day entries" in briefing

    # 6. Update dynasty
    dynasty = read_dynasty_json(empire_env["dynasty_dir"])
    dynasty["sessions_since_succession"] = 1
    write_dynasty_json(empire_env["dynasty_dir"], dynasty)

    # 7. Next session start should see the briefing
    vault2 = read_file_safe(empire_env["vault_path"])
    briefing2 = read_file_safe(empire_env["briefing_path"])
    dynasty2 = read_dynasty_json(empire_env["dynasty_dir"])
    output2 = build_briefing_output(
        vault=vault2,
        briefing=briefing2,
        dynasty=dynasty2,
        branch=BRANCH,
    )
    assert "Briefing" in output2
    assert "TypeScript" in output2  # vault still present

    # 8. Verify epithet for this session's work
    epithet = generate_epithet(entries)
    # entries mention prisma/schema and database-adjacent work
    assert isinstance(epithet, str)
    assert len(epithet) > 0
