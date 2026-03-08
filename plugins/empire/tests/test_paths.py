import os
import tempfile
import pytest
from unittest.mock import patch
from core.paths import (
    get_project_root,
    get_memory_dir,
    get_current_branch,
    get_dynasty_dir,
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
            assert "home-user-myproject" in result


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
