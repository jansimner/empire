import json
import os
import pytest
from unittest.mock import patch

from core.dashboard import (
    BOX_WIDTH,
    box_bottom,
    box_line,
    box_mid,
    box_top,
    display_width,
    pad_right,
    relative_time,
    render_dashboard,
)


class TestDisplayWidth:
    def test_ascii(self):
        assert display_width("hello") == 5

    def test_empty(self):
        assert display_width("") == 0

    def test_basic_emoji(self):
        assert display_width("👑") == 2
        assert display_width("🌿") == 2
        assert display_width("📊") == 2

    def test_emoji_with_variation_selector(self):
        assert display_width("☀️") == 2  # U+2600 + U+FE0F
        assert display_width("🏛️") == 2  # U+1F3DB + U+FE0F
        assert display_width("⚠️") == 2  # U+26A0 + U+FE0F

    def test_box_drawing(self):
        assert display_width("─") == 1
        assert display_width("│") == 1
        assert display_width("┌") == 1

    def test_shade_blocks(self):
        assert display_width("▓") == 1
        assert display_width("░") == 1
        assert display_width("▓▓▓░░░") == 6

    def test_mixed_emoji_and_text(self):
        assert display_width("👑 hello") == 8  # 2 + 1 + 5

    def test_emoji_with_vs_in_context(self):
        # ☀️ is 2 display + space + text
        assert display_width("☀️ Day") == 6  # 2 + 1 + 3


class TestPadRight:
    def test_basic(self):
        result = pad_right("hi", 10)
        assert display_width(result) == 10
        assert result == "hi        "

    def test_already_at_width(self):
        result = pad_right("hello", 5)
        assert result == "hello"

    def test_wider_than_target(self):
        result = pad_right("hello world", 5)
        assert result == "hello world"  # no truncation

    def test_with_emoji(self):
        result = pad_right("👑 hi", 10)
        assert display_width(result) == 10
        # 👑=2 + space=1 + hi=2 = 5, needs 5 more spaces
        assert result == "👑 hi     "


class TestBoxElements:
    def test_box_top_width(self):
        assert display_width(box_top()) == BOX_WIDTH + 2

    def test_box_mid_width(self):
        assert display_width(box_mid()) == BOX_WIDTH + 2

    def test_box_bottom_width(self):
        assert display_width(box_bottom()) == BOX_WIDTH + 2

    def test_box_line_width(self):
        result = box_line("  hello")
        assert display_width(result) == BOX_WIDTH + 2

    def test_box_line_with_emoji(self):
        result = box_line("  👑 EMPIRE STATUS")
        assert display_width(result) == BOX_WIDTH + 2

    def test_box_line_with_vs_emoji(self):
        result = box_line("  ☀️  Day:   Claude I")
        assert display_width(result) == BOX_WIDTH + 2

    def test_all_lines_same_width(self):
        """Every box element must produce the same display width."""
        target = BOX_WIDTH + 2
        assert display_width(box_top()) == target
        assert display_width(box_mid()) == target
        assert display_width(box_bottom()) == target
        assert display_width(box_line("  👑 EMPIRE STATUS")) == target
        assert display_width(box_line("  ☀️  Day:   Claude I  ???  3 entries")) == target
        assert display_width(box_line("  🏛️  Vault:    9/50 lines")) == target
        assert display_width(box_line("  📊 Pressure: ▓▓▓▓▓▓▓▓▓▓ 100%")) == target


class TestRelativeTime:
    def test_never_returns_for_bad_input(self):
        assert relative_time("not-a-date") == "unknown"

    def test_recent_time(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        assert relative_time(now) == "just now"


class TestRenderDashboard:
    """Integration tests for the full dashboard render."""

    def test_no_empire_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("core.dashboard.get_project_root", return_value=None):
            result = render_dashboard()
        assert "No Empire found" in result

    def test_all_lines_same_display_width(self, tmp_path, monkeypatch):
        """The critical test: every line in the box must have the same display width."""
        # Set up minimal empire state
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text("# Vault\n## Project\ntest\n")

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        dynasty_json = {
            "current": 3,
            "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": "2026-03-01T12:00:00Z",
            "sessions_since_succession": 2,
            "epithets": {"2": "the Builder"},
        }
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text(
            "# Day\n## Entries\n\n"
            "### [ref:5] [decision] Added auth\n"
            "Why: Security.\nWhat: JWT tokens.\n\n"
            "### [ref:0] [observation] Tested deploy\nAll good.\n"
        )
        (dynasty_dir / "dawn.md").write_text(
            "## Git State\n- item1\n- item2\n## Dusk Wisdom\n- wisdom1\n"
        )
        (dynasty_dir / "dusk.md").write_text(
            "# Dusk\n## Layer 1 (detailed)\n"
            "### [ref:3] [observation] Old pattern\nSome detail.\n"
        )

        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.get_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        lines = result.strip().split("\n")
        widths = [display_width(line) for line in lines]

        # All lines must be the same width
        assert len(set(widths)) == 1, (
            f"Inconsistent widths: {list(zip(range(len(widths)), widths))}\n{result}"
        )

    def test_contains_empire_status(self, tmp_path, monkeypatch):
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text("")

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        dynasty_json = {
            "current": 1,
            "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text("")
        (dynasty_dir / "dawn.md").write_text("")
        (dynasty_dir / "dusk.md").write_text("")

        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.get_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "EMPIRE STATUS" in result
        assert "Dynasty of Claude" in result
        assert "Vault" in result
        assert "Pressure" in result

    def test_first_dynasty_shows_no_dusk(self, tmp_path, monkeypatch):
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text("")

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        dynasty_json = {
            "current": 1,
            "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text("")
        (dynasty_dir / "dawn.md").write_text("")
        (dynasty_dir / "dusk.md").write_text("")

        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.get_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "Dusk:  none" in result

    def test_succession_warning_when_triggered(self, tmp_path, monkeypatch):
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text("")

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        # 6 sessions triggers succession
        dynasty_json = {
            "current": 1,
            "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 6,
            "epithets": {},
        }
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text(
            "# Day\n## Entries\n\n### [ref:1] [observation] Test\nBody.\n"
        )
        (dynasty_dir / "dawn.md").write_text("")
        (dynasty_dir / "dusk.md").write_text("")

        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.get_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        assert "Succession suggested" in result
        # Still must be aligned
        lines = result.strip().split("\n")
        widths = [display_width(line) for line in lines]
        assert len(set(widths)) == 1

    def test_long_succession_reason_truncated(self, tmp_path, monkeypatch):
        """Very long reasons should be truncated to fit the box."""
        empire_dir = tmp_path / ".empire"
        empire_dir.mkdir()
        (empire_dir / "vault.md").write_text("")

        dynasty_dir = tmp_path / "dynasty"
        dynasty_dir.mkdir(parents=True)
        # Create many stale entries to trigger succession with a long reason
        entries_md = "# Day\n## Entries\n\n"
        for i in range(35):
            entries_md += f"### [ref:0] [observation] Entry number {i} with extra detail\nSome body text here.\n\n"

        dynasty_json = {
            "current": 1,
            "branch": "main",
            "founded": "2026-01-01T00:00:00Z",
            "last_succession": None,
            "sessions_since_succession": 0,
            "epithets": {},
        }
        (dynasty_dir / "dynasty.json").write_text(json.dumps(dynasty_json))
        (dynasty_dir / "day.md").write_text(entries_md)
        (dynasty_dir / "dawn.md").write_text("")
        (dynasty_dir / "dusk.md").write_text("")

        monkeypatch.chdir(tmp_path)
        with (
            patch("core.dashboard.get_project_root", return_value=str(tmp_path)),
            patch("core.dashboard.get_current_branch", return_value="main"),
            patch("core.dashboard.get_dynasty_dir", return_value=str(dynasty_dir)),
        ):
            result = render_dashboard()

        lines = result.strip().split("\n")
        widths = [display_width(line) for line in lines]
        assert len(set(widths)) == 1, f"Widths: {widths}"
