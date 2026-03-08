import json
import os
import pytest
from core.state import (
    read_dynasty_json,
    write_dynasty_json,
    ensure_dynasty_dir,
    read_file_safe,
    write_file_safe,
    count_lines,
    check_succession_triggers,
)


def test_read_dynasty_json_default(tmp_path):
    result = read_dynasty_json(str(tmp_path / "nonexistent"))
    assert result["current"] == 0
    assert result["branch"] == "main"
    assert result["epithets"] == {}


def test_write_and_read_dynasty_json(tmp_path):
    dynasty_dir = str(tmp_path / "dynasty")
    os.makedirs(dynasty_dir)
    data = {"current": 3, "branch": "main", "founded": "2026-03-08", "epithets": {"1": "the Builder"}}
    write_dynasty_json(dynasty_dir, data)
    result = read_dynasty_json(dynasty_dir)
    assert result["current"] == 3
    assert result["epithets"]["1"] == "the Builder"


def test_ensure_dynasty_dir_creates(tmp_path):
    dynasty_dir = str(tmp_path / "dynasty" / "main")
    ensure_dynasty_dir(dynasty_dir)
    assert os.path.isdir(dynasty_dir)


def test_read_file_safe_returns_empty_on_missing(tmp_path):
    result = read_file_safe(str(tmp_path / "nope.md"))
    assert result == ""


def test_write_and_read_file(tmp_path):
    path = str(tmp_path / "test.md")
    write_file_safe(path, "hello world")
    assert read_file_safe(path) == "hello world"


def test_count_lines():
    assert count_lines("one\ntwo\nthree") == 3
    assert count_lines("") == 0
    assert count_lines("single") == 1


def test_succession_triggers_no_entries():
    should, reason = check_succession_triggers(entries=[], sessions_since_last=0)
    assert should is False


def test_succession_triggers_too_many_entries():
    entries = [{"ref": 1, "title": f"entry {i}"} for i in range(35)]
    should, reason = check_succession_triggers(entries=entries, sessions_since_last=1)
    assert should is True
    assert ">30 entries" in reason


def test_succession_triggers_too_many_sessions():
    entries = [{"ref": 1, "title": "entry"}]
    should, reason = check_succession_triggers(entries=entries, sessions_since_last=6)
    assert should is True
    assert "sessions" in reason


def test_succession_triggers_stale_entries():
    entries = [{"ref": 0, "title": f"stale {i}"} for i in range(8)]
    entries += [{"ref": 3, "title": "active 1"}, {"ref": 5, "title": "active 2"}]
    should, reason = check_succession_triggers(entries=entries, sessions_since_last=1)
    assert should is True
    assert "stale" in reason.lower()
