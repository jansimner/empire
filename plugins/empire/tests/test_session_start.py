import json
import os
import pytest
from unittest.mock import patch
from hooks.session_start import build_briefing_output, main
from core.state import read_dynasty_json, read_file_safe
from core.paths import reset_project_root_cache


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_project_root_cache()
    yield
    reset_project_root_cache()


def test_build_briefing_with_vault_and_briefing(tmp_path):
    vault = "# 🏛️ Vault\n- TypeScript + NestJS\n- Prisma ORM"
    briefing = "# ☀️ Briefing\nWorking on auth. Pressure: 30%"

    dynasty = {"current": 3, "branch": "main", "epithets": {"2": "the Builder", "3": None}}

    output = build_briefing_output(
        vault=vault,
        briefing=briefing,
        dynasty=dynasty,
        branch="main",
    )
    assert "Vault" in output
    assert "TypeScript" in output
    assert "Briefing" in output
    assert "auth" in output


def test_build_briefing_no_empire_initialized():
    output = build_briefing_output(
        vault="",
        briefing="",
        dynasty={"current": 1, "epithets": {}},
        branch="main",
    )
    assert output == ""


@patch("hooks.session_start.get_project_root")
@patch("hooks.session_start.get_current_branch")
@patch("hooks.session_start.resolve_dynasty_dir")
def test_session_start_increments_session_counter(
    mock_dynasty_dir, mock_branch, mock_project_root, tmp_path,
):
    """SessionStart must increment sessions_since_succession so crashed sessions still count."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    empire_dir = project_root / ".empire"
    empire_dir.mkdir()
    (empire_dir / "vault.md").write_text("")

    dynasty_dir = tmp_path / "dynasty"
    dynasty_dir.mkdir()
    (dynasty_dir / "dynasty.json").write_text(json.dumps({
        "current": 1,
        "branch": "main",
        "sessions_since_succession": 3,
        "epithets": {},
    }))

    mock_project_root.return_value = str(project_root)
    mock_branch.return_value = "main"
    mock_dynasty_dir.return_value = str(dynasty_dir)

    main()

    dynasty = read_dynasty_json(str(dynasty_dir))
    assert dynasty["sessions_since_succession"] == 4
