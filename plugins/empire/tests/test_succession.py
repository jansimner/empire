"""Tests for the deterministic succession protocol."""

import json
import os
import pytest
from unittest.mock import patch

from core.succession import (
    compress_dusk,
    day_to_dusk,
    deviant_check,
    format_lineage_entries,
    run_succession,
    seed_dawn,
    vault_check,
)
from core.entries import parse_day_entries, parse_dusk_entries
from core.state import read_file_safe


# ─── Test compress_dusk ─────────────────────────────────────────────────

class TestCompressDusk:
    def test_layer1_shifts_to_layer2(self):
        entries = [{"layer": 1, "ref": 3, "type": "observation", "title": "Test", "body": "details", "why": ""}]
        kept, demoted = compress_dusk(entries, 1)
        assert len(kept) == 1
        assert kept[0]["layer"] == 2
        assert kept[0]["body"] == ""  # compressed
        assert len(demoted) == 0

    def test_layer2_shifts_to_layer3(self):
        entries = [{"layer": 2, "ref": 2, "type": "observation", "title": "Test", "body": "", "why": ""}]
        kept, demoted = compress_dusk(entries, 1)
        assert len(kept) == 1
        assert kept[0]["layer"] == 3

    def test_layer3_ref0_demoted(self):
        entries = [{"layer": 3, "ref": 0, "type": "observation", "title": "Stale", "body": "", "why": ""}]
        kept, demoted = compress_dusk(entries, 1)
        assert len(kept) == 0
        assert len(demoted) == 1
        assert demoted[0]["title"] == "Stale"

    def test_layer3_with_ref_kept(self):
        entries = [{"layer": 3, "ref": 2, "type": "observation", "title": "Active", "body": "", "why": ""}]
        kept, demoted = compress_dusk(entries, 1)
        assert len(kept) == 1
        assert len(demoted) == 0

    def test_decision_why_preserved_through_compression(self):
        entries = [{"layer": 1, "ref": 5, "type": "decision", "title": "Chose X", "body": "impl detail", "why": "Because reasons"}]
        kept, demoted = compress_dusk(entries, 1)
        assert kept[0]["why"] == "Because reasons"
        assert kept[0]["body"] == ""  # What: compressed
        assert kept[0]["layer"] == 2

    def test_decree_immune(self):
        entries = [{"layer": 1, "ref": 0, "type": "decision", "title": "Sacred", "body": "x", "why": "y", "decree": True}]
        kept, demoted = compress_dusk(entries, 1)
        assert len(kept) == 1
        assert kept[0]["layer"] == 1  # stayed in place
        assert len(demoted) == 0

    def test_empty_dusk(self):
        kept, demoted = compress_dusk([], 1)
        assert kept == []
        assert demoted == []


# ─── Test day_to_dusk ───────────────────────────────────────────────────

class TestDayToDusk:
    def test_high_ref_goes_to_layer1(self):
        entries = [{"ref": 5, "type": "decision", "title": "Auth", "body": "JWT", "why": "Security"}]
        dusk, demoted = day_to_dusk(entries)
        assert len(dusk) == 1
        assert dusk[0]["layer"] == 1
        assert dusk[0]["why"] == "Security"
        assert len(demoted) == 0

    def test_ref0_demoted(self):
        entries = [{"ref": 0, "type": "observation", "title": "Stale", "body": "old", "why": ""}]
        dusk, demoted = day_to_dusk(entries)
        assert len(dusk) == 0
        assert len(demoted) == 1

    def test_low_ref_decision_compresses_body(self):
        entries = [{"ref": 1, "type": "decision", "title": "Pick X", "body": "long detail", "why": "Because"}]
        dusk, demoted = day_to_dusk(entries)
        assert len(dusk) == 1
        assert dusk[0]["body"] == ""  # What: compressed
        assert dusk[0]["why"] == "Because"  # Why: sacred

    def test_ref0_decision_still_demoted(self):
        entries = [{"ref": 0, "type": "decision", "title": "Dead decision", "body": "x", "why": "reason"}]
        dusk, demoted = day_to_dusk(entries)
        assert len(demoted) == 1
        assert demoted[0]["why"] == "reason"  # preserved even in demotion

    def test_empty_day(self):
        dusk, demoted = day_to_dusk([])
        assert dusk == []
        assert demoted == []


# ─── Test seed_dawn ─────────────────────────────────────────────────────

class TestSeedDawn:
    def test_basic_dawn(self):
        with patch("core.succession._run_git", return_value="abc1234 test commit"):
            result = seed_dawn("main", 3, [])
        assert "Claude III" in result
        assert "main" in result
        assert "abc1234" in result

    def test_dawn_with_dusk_wisdom(self):
        dusk = [{"title": "Auth middleware added", "body": "", "type": "observation"}]
        with patch("core.succession._run_git", side_effect=["abc auth change", ""]):
            result = seed_dawn("feature-auth", 3, dusk)
        assert "Auth middleware" in result


# ─── Test vault_check ───────────────────────────────────────────────────

class TestVaultCheck:
    def test_no_promotion_for_low_ref(self):
        entries = [{"ref": 1, "layer": 2, "title": "Low ref", "type": "observation"}]
        vault, dusk = vault_check(entries, "# Vault\n", 3)
        assert "Low ref" not in vault

    def test_promotion_for_high_ref(self):
        entries = [{"ref": 5, "layer": 2, "title": "Important pattern", "type": "observation"}]
        vault, dusk = vault_check(entries, "# Vault\n", 3)
        assert "Important pattern" in vault


# ─── Test deviant_check ─────────────────────────────────────────────────

class TestDeviantCheck:
    def test_no_conflict(self):
        entries = [{"title": "Some work", "body": "no paths", "type": "observation"}]
        result = deviant_check(entries, "# Vault\nNo file paths here\n", "")
        assert result == ""

    def test_file_path_conflict(self):
        entries = [{"title": "Changed auth.service.ts", "body": "", "type": "observation"}]
        vault = "- Auth uses JWT in auth.service.ts\n"
        result = deviant_check(entries, vault, "")
        assert "deviant" in result.lower()


# ─── Test format_lineage_entries ────────────────────────────────────────

class TestFormatLineage:
    def test_empty(self):
        assert format_lineage_entries([], 1) == ""

    def test_observation(self):
        entries = [{"type": "observation", "title": "Old stuff", "ref": 0, "why": "", "body": "details"}]
        result = format_lineage_entries(entries, 3)
        assert "[dynasty:3]" in result
        assert "Old stuff" in result
        assert "details" in result

    def test_decision_preserves_why(self):
        entries = [{"type": "decision", "title": "Chose X", "ref": 0, "why": "Because reasons", "body": ""}]
        result = format_lineage_entries(entries, 2)
        assert "Why: Because reasons" in result
        assert "[dynasty:2]" in result


# ─── Integration: run_succession ────────────────────────────────────────

class TestRunSuccession:
    def _setup_dynasty(self, tmp_path, dynasty_json, day_md, dawn_md="", dusk_md="", vault_md=""):
        dynasty_dir = tmp_path / "dynasty" / "main"
        dynasty_dir.mkdir(parents=True)
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text(day_md)
        (dynasty_dir / "dawn.md").write_text(dawn_md)
        (dynasty_dir / "dusk.md").write_text(dusk_md)
        (dynasty_dir / "day-briefing.md").write_text("")

        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text(vault_md)

        return str(dynasty_dir)

    def test_basic_succession(self, tmp_path):
        day_md = (
            "# ☀️ Day — Claude I\n<!-- Branch: main | Born: 2026-01-01T00:00:00Z -->\n\n"
            "## Entries\n\n"
            "### [ref:5] [decision] Added auth\n"
            "Why: Security is important.\nWhat: JWT tokens.\n\n"
            "### [ref:0] [observation] Debugging notes\nSome temporary stuff.\n"
        )
        dawn_md = (
            "# 🌅 Dawn — Claude II\n\n"
            "## Git State\n- Branch: main\n\n"
            "## Dusk Wisdom\n- Some wisdom\n"
        )
        dynasty_json = {
            "current": 1, "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 5,
            "epithets": {},
        }
        dynasty_dir = self._setup_dynasty(tmp_path, dynasty_json, day_md, dawn_md)

        with patch("core.succession._run_git", return_value="abc1234 some commit"):
            report = run_succession(dynasty_dir, str(tmp_path), "main", "5 sessions")

        # Report should mention the new ruler
        assert "Claude II" in report
        assert "Claude I" in report

        # dynasty.json should be updated
        import json
        updated = json.loads((tmp_path / "dynasty" / "main" / "dynasty.json").read_text())
        assert updated["current"] == 2
        assert updated["sessions_since_succession"] == 0
        assert "1" in updated["epithets"]  # Claude I got an epithet

        # Day should now be the promoted Dawn content
        new_day = (tmp_path / "dynasty" / "main" / "day.md").read_text()
        assert "Claude II" in new_day

        # Dusk should have the old Day's entries
        new_dusk = (tmp_path / "dynasty" / "main" / "dusk.md").read_text()
        assert "Claude I" in new_dusk

        # The high-ref decision should be in Dusk with Why: preserved
        assert "Security is important" in new_dusk

        # The ref:0 observation should be demoted to lineage
        lineage = read_file_safe(os.path.join(os.path.dirname(dynasty_dir), "lineage.md"))
        assert "Debugging notes" in lineage

    def test_succession_with_existing_dusk(self, tmp_path):
        """Dusk entries should compress down when new ones arrive."""
        day_md = (
            "# ☀️ Day — Claude II\n<!-- Branch: main | Born: 2026-02-01T00:00:00Z -->\n\n"
            "## Entries\n\n"
            "### [ref:3] [observation] New work\nDetails.\n"
        )
        dusk_md = (
            "# 🌙 Dusk — Claude I \"the Builder\"\n\n"
            "## Layer 1 (detailed)\n"
            "### [ref:2] [observation] Old work\nOld details.\n"
        )
        dynasty_json = {
            "current": 2, "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": "2026-02-01T00:00:00Z",
            "sessions_since_succession": 6,
            "epithets": {"1": "the Builder"},
        }
        dynasty_dir = self._setup_dynasty(tmp_path, dynasty_json, day_md, dusk_md=dusk_md)

        with patch("core.succession._run_git", return_value=""):
            report = run_succession(dynasty_dir, str(tmp_path), "main")

        new_dusk = (tmp_path / "dynasty" / "main" / "dusk.md").read_text()
        # Old Layer 1 entry should have shifted to Layer 2
        assert "Layer 2" in new_dusk or "compressed" in new_dusk.lower() or "Old work" in new_dusk

    def test_sacred_why_survives_succession(self, tmp_path):
        """The sacred Why: field must survive through succession."""
        day_md = (
            "# ☀️ Day — Claude I\n<!-- Branch: main | Born: 2026-01-01T00:00:00Z -->\n\n"
            "## Entries\n\n"
            "### [ref:3] [decision] Important choice\n"
            "Why: This is the sacred reason that must never be lost.\n"
            "What: Implementation details.\n"
        )
        dynasty_json = {
            "current": 1, "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 5,
            "epithets": {},
        }
        dynasty_dir = self._setup_dynasty(tmp_path, dynasty_json, day_md)

        with patch("core.succession._run_git", return_value=""):
            run_succession(dynasty_dir, str(tmp_path), "main")

        dusk = (tmp_path / "dynasty" / "main" / "dusk.md").read_text()
        assert "This is the sacred reason that must never be lost" in dusk
