import json
import pytest
from core.ref_tracker import score_entries_against_content, load_ref_cache, save_ref_cache


ENTRIES = [
    {"ref": 2, "title": "Added rate limiting", "body": "express-rate-limit in middleware/rate-limit.ts"},
    {"ref": 0, "title": "Considered Redis", "body": "session store decision"},
]


def test_tier1_exact_file_path_match():
    scores = score_entries_against_content(ENTRIES, "middleware/rate-limit.ts")
    assert scores[0] >= 2

def test_tier2_directory_overlap():
    scores = score_entries_against_content(ENTRIES, "middleware/cors.ts")
    assert scores[0] >= 1

def test_tier3_needs_two_keyword_matches():
    scores_single = score_entries_against_content(ENTRIES, "session")
    scores_double = score_entries_against_content(ENTRIES, "session store")
    assert scores_single.get(1, 0) == 0
    assert scores_double.get(1, 0) >= 1

def test_no_match_returns_empty():
    scores = score_entries_against_content(ENTRIES, "completely unrelated xyz")
    assert all(v == 0 for v in scores.values())

def test_tier1_absolute_path_matches_relative():
    """Absolute paths in tool content match relative paths in entries."""
    scores = score_entries_against_content(
        ENTRIES,
        "/home/user/project/middleware/rate-limit.ts",
        project_root="/home/user/project",
    )
    assert scores[0] >= 2  # tier-1 match after normalization


def test_tier2_absolute_directory_matches_relative():
    """Absolute directory paths match relative directories in entries."""
    scores = score_entries_against_content(
        ENTRIES,
        "/home/user/project/middleware/cors.ts",
        project_root="/home/user/project",
    )
    assert scores[0] >= 1  # tier-2 directory match


def test_ref_cache_roundtrip(tmp_path):
    cache_path = str(tmp_path / "ref_cache.json")
    data = {"0": 3, "1": 1}
    save_ref_cache(cache_path, data)
    loaded = load_ref_cache(cache_path)
    assert loaded == data

def test_ref_cache_missing_file(tmp_path):
    loaded = load_ref_cache(str(tmp_path / "nope.json"))
    assert loaded == {}
