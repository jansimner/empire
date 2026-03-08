import json
import os
import pytest
from unittest.mock import patch

from core.dashboard import relative_time, render_dashboard


class TestRelativeTime:
    def test_bad_input(self):
        assert relative_time("not-a-date") == "unknown"

    def test_recent_time(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        assert relative_time(now) == "just now"


class TestRenderDashboard:
    def _setup_empire(self, tmp_path, dynasty_json, day_md="", dawn_md="", dusk_md="", vault_md=""):
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text(vault_md)

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text(day_md)
        (dynasty_dir / "dawn.md").write_text(dawn_md)
        (dynasty_dir / "dusk.md").write_text(dusk_md)
        return dynasty_dir

    def test_no_empire_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("core.dashboard.get_project_root", return_value=None):
            result = render_dashboard()
        assert "No Empire found" in result

    def test_basic_output(self, tmp_path, monkeypatch):
        dynasty_dir = self._setup_empire(tmp_path, {
            "current": 1, "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        })
        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.resolve_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "# Empire — main" in result
        assert "**Dawn:**" in result
        assert "**Day:** Claude I" in result
        assert "**Dusk:** none" in result
        assert "**Vault:** 0/50 lines" in result
        assert "**Pressure:**" in result
        assert "**Last succession:** never" in result

    def test_with_entries_and_epithet(self, tmp_path, monkeypatch):
        dynasty_dir = self._setup_empire(
            tmp_path,
            {
                "current": 3, "branch": "main",
                "founded": "2026-01-01T00:00:00Z",
                "last_succession": "2026-03-01T12:00:00Z",
                "sessions_since_succession": 2,
                "epithets": {"2": "the Builder"},
            },
            day_md=(
                "# Day\n## Entries\n\n"
                "### [ref:5] [decision] Added auth\n"
                "Why: Security.\nWhat: JWT tokens.\n\n"
                "### [ref:0] [observation] Tested deploy\nAll good.\n"
            ),
            dawn_md="## Git State\n- item1\n- item2\n## Dusk Wisdom\n- wisdom1\n",
            dusk_md=(
                "# Dusk\n## Layer 1 (detailed)\n"
                "### [ref:3] [observation] Old pattern\nSome detail.\n"
            ),
            vault_md="# Vault\n## Project\ntest line\n",
        )
        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.resolve_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "Claude III" in result
        assert "2 entries" in result
        assert "3 staged" in result
        assert '**Dusk:** Claude II "the Builder"' in result
        assert "1 wisdom" in result

    def test_first_dynasty_no_dusk(self, tmp_path, monkeypatch):
        dynasty_dir = self._setup_empire(tmp_path, {
            "current": 1, "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        })
        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.resolve_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "**Dusk:** none" in result

    def test_succession_warning(self, tmp_path, monkeypatch):
        dynasty_dir = self._setup_empire(
            tmp_path,
            {
                "current": 1, "branch": "main",
                "founded": "2026-01-01T00:00:00Z",
                "last_succession": None,
                "sessions_since_succession": 6,
                "epithets": {},
            },
            day_md="# Day\n## Entries\n\n### [ref:1] [observation] Test\nBody.\n",
        )
        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.resolve_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "**Succession suggested:**" in result

    def test_pressure_bar(self, tmp_path, monkeypatch):
        dynasty_dir = self._setup_empire(
            tmp_path,
            {
                "current": 1, "branch": "main",
                "founded": "2026-01-01T00:00:00Z",
                "last_succession": None,
                "sessions_since_succession": 0,
                "epithets": {},
            },
            day_md=(
                "# Day\n## Entries\n\n"
                "### [ref:0] [observation] Stale entry\nBody.\n\n"
                "### [ref:0] [observation] Another stale\nBody.\n"
            ),
        )
        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.resolve_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "▓▓▓▓▓▓▓▓▓▓" in result
        assert "100%" in result
