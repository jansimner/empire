import os
import subprocess
import tempfile
import pytest
from unittest.mock import patch
from core.paths import (
    get_project_root,
    get_memory_dir,
    get_current_branch,
    get_dynasty_dir,
    resolve_dynasty_dir,
    sanitize_branch_name,
)


def test_sanitize_branch_name_simple():
    assert sanitize_branch_name("main") == "main"


def test_sanitize_branch_name_with_slashes():
    assert sanitize_branch_name("feature/payments") == "feature-payments"


def test_sanitize_branch_name_with_special_chars():
    assert sanitize_branch_name("feature/my_branch@2") == "feature-my_branch-2"


def test_get_project_root_finds_empire_dir(tmp_path):
    empire_dir = tmp_path / ".empire"
    empire_dir.mkdir()
    with patch("os.getcwd", return_value=str(tmp_path)):
        assert get_project_root() == str(tmp_path)


def test_get_project_root_returns_none_when_missing(tmp_path):
    with patch("os.getcwd", return_value=str(tmp_path)):
        assert get_project_root() is None


def test_get_memory_dir_constructs_path(tmp_path):
    with patch("os.path.expanduser", return_value=str(tmp_path)):
        with patch("core.paths.get_project_root", return_value="/home/user/myproject"):
            result = get_memory_dir()
            assert "empire" in result
            assert "-home-user-myproject" in result


def test_get_dynasty_dir_uses_sanitized_branch(tmp_path):
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        result = get_dynasty_dir("feature/payments")
        assert result.endswith("dynasty/feature-payments")


def test_get_current_branch_reads_git(tmp_path):
    # Create a git repo
    os.system(f"git init {tmp_path} --quiet")
    os.system(f"git -C {tmp_path} commit --allow-empty -m 'init' --quiet")
    with patch("os.getcwd", return_value=str(tmp_path)):
        branch = get_current_branch()
        assert branch in ("main", "master")


def test_get_current_branch_falls_back_to_symbolic_ref():
    """When rev-parse fails (fresh repo, no commits), symbolic-ref is used."""
    rev_parse_result = subprocess.CompletedProcess(
        args=[], returncode=128, stdout="", stderr="fatal: bad default revision"
    )
    symbolic_ref_result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="master\n", stderr=""
    )

    with patch("core.paths.subprocess.run") as mock_run:
        mock_run.side_effect = [rev_parse_result, symbolic_ref_result]
        assert get_current_branch() == "master"
        assert mock_run.call_count == 2
        # First call is rev-parse, second is symbolic-ref
        assert "rev-parse" in mock_run.call_args_list[0][0][0]
        assert "symbolic-ref" in mock_run.call_args_list[1][0][0]


def test_get_current_branch_falls_back_to_main_when_git_unavailable():
    """When git is totally unavailable, we fall back to 'main'."""
    with patch("core.paths.subprocess.run", side_effect=FileNotFoundError):
        assert get_current_branch() == "main"


def test_resolve_dynasty_dir_returns_primary_when_exists(tmp_path):
    """resolve_dynasty_dir returns the primary branch dir when dynasty.json exists there."""
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        dynasty_dir = get_dynasty_dir("main")
        os.makedirs(dynasty_dir, exist_ok=True)
        with open(os.path.join(dynasty_dir, "dynasty.json"), "w") as f:
            f.write("{}")

        result = resolve_dynasty_dir("main")
        assert result == dynasty_dir


def test_resolve_dynasty_dir_falls_back_to_master(tmp_path):
    """If dynasty.json is under 'master/' but branch is 'main', find it."""
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        master_dir = get_dynasty_dir("master")
        os.makedirs(master_dir, exist_ok=True)
        with open(os.path.join(master_dir, "dynasty.json"), "w") as f:
            f.write("{}")

        result = resolve_dynasty_dir("main")
        assert result == master_dir


def test_resolve_dynasty_dir_falls_back_to_main(tmp_path):
    """If dynasty.json is under 'main/' but branch is 'master', find it."""
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        main_dir = get_dynasty_dir("main")
        os.makedirs(main_dir, exist_ok=True)
        with open(os.path.join(main_dir, "dynasty.json"), "w") as f:
            f.write("{}")

        result = resolve_dynasty_dir("master")
        assert result == main_dir


def test_resolve_dynasty_dir_returns_primary_when_nothing_exists(tmp_path):
    """When no dynasty.json exists anywhere, return the primary path."""
    with patch("core.paths.get_memory_dir", return_value=str(tmp_path)):
        result = resolve_dynasty_dir("develop")
        expected = get_dynasty_dir("develop")
        assert result == expected
