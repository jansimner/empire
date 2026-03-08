import json
import os
import pytest
from unittest.mock import patch
from hooks.session_start import build_briefing_output


def test_build_briefing_with_vault_and_briefing(tmp_path):
    vault_path = tmp_path / "vault.md"
    vault_path.write_text("# 🏛️ Vault\n- TypeScript + NestJS\n- Prisma ORM")

    briefing_path = tmp_path / "day-briefing.md"
    briefing_path.write_text("# ☀️ Briefing\nWorking on auth. Pressure: 30%")

    dynasty_dir = tmp_path / "dynasty"
    dynasty_dir.mkdir()
    (dynasty_dir / "dynasty.json").write_text(json.dumps({
        "current": 3, "branch": "main",
        "epithets": {"2": "the Builder", "3": None},
    }))

    output = build_briefing_output(
        vault_path=str(vault_path),
        briefing_path=str(briefing_path),
        dynasty_dir=str(dynasty_dir),
        branch="main",
    )
    assert "Vault" in output
    assert "TypeScript" in output
    assert "Briefing" in output
    assert "auth" in output


def test_build_briefing_no_empire_initialized():
    output = build_briefing_output(
        vault_path="/nonexistent/vault.md",
        briefing_path="/nonexistent/briefing.md",
        dynasty_dir="/nonexistent/dynasty",
        branch="main",
    )
    assert output == ""
