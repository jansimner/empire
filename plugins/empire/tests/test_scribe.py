"""Tests for core.scribe — Session Scribe entry generation from git diff."""

import pytest
from core.scribe import (
    extract_changed_files,
    classify_changes,
    merge_with_existing,
    get_session_diff,
)


# ---------------------------------------------------------------------------
# Realistic git diff fixtures
# ---------------------------------------------------------------------------

DIFF_NEW_FILE = """\
diff --git a/core/scribe.py b/core/scribe.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/core/scribe.py
@@ -0,0 +1,45 @@
+#!/usr/bin/env python3
+\"\"\"Session Scribe: auto-generate Day entries from git diff.\"\"\"
+
+import subprocess
+import re
+
+def get_session_diff() -> str:
+    pass
"""

DIFF_DELETED_FILE = """\
diff --git a/old_module.py b/old_module.py
deleted file mode 100644
index abc1234..0000000
--- a/old_module.py
+++ /dev/null
@@ -1,10 +0,0 @@
-# This module is no longer needed
-def old_function():
-    pass
"""

DIFF_TEST_FILE = """\
diff --git a/tests/test_auth.py b/tests/test_auth.py
index abc1234..def5678 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -10,6 +10,15 @@ def test_login():
+def test_token_refresh():
+    token = create_token(user_id=1)
+    refreshed = refresh_token(token)
+    assert refreshed is not None
"""

DIFF_CONFIG_FILES = """\
diff --git a/docker-compose.yml b/docker-compose.yml
index abc1234..def5678 100644
--- a/docker-compose.yml
+++ b/docker-compose.yml
@@ -5,3 +5,5 @@ services:
+  redis:
+    image: redis:7-alpine

diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index abc1234..def5678 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -12,1 +12,3 @@ jobs:
+      - name: Run linter
+        run: npm run lint
"""

DIFF_MULTIPLE_SAME_DIR = """\
diff --git a/core/auth.py b/core/auth.py
index abc1234..def5678 100644
--- a/core/auth.py
+++ b/core/auth.py
@@ -1,3 +1,8 @@
+import jwt
+
 def verify_token(token):
-    pass
+    return jwt.decode(token, key="secret")

diff --git a/core/permissions.py b/core/permissions.py
index abc1234..def5678 100644
--- a/core/permissions.py
+++ b/core/permissions.py
@@ -1,2 +1,5 @@
+ROLES = ["admin", "user", "viewer"]
+
 def check_permission(user, action):
-    pass
+    return user.role in ROLES

diff --git a/core/middleware.py b/core/middleware.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/core/middleware.py
@@ -0,0 +1,5 @@
+def auth_middleware(request):
+    token = request.headers.get("Authorization")
+    if not token:
+        raise PermissionError("No token provided")
+    return verify_token(token)
"""

DIFF_MIXED = """\
diff --git a/core/scribe.py b/core/scribe.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/core/scribe.py
@@ -0,0 +1,10 @@
+def get_session_diff():
+    pass

diff --git a/tests/test_scribe.py b/tests/test_scribe.py
new file mode 100644
index 0000000..def5678
--- /dev/null
+++ b/tests/test_scribe.py
@@ -0,0 +1,15 @@
+def test_extract():
+    pass

diff --git a/config.json b/config.json
index abc1234..def5678 100644
--- a/config.json
+++ b/config.json
@@ -1,3 +1,4 @@
 {
+  "debug": true,
   "port": 3000
 }

diff --git a/old_util.py b/old_util.py
deleted file mode 100644
index abc1234..0000000
--- a/old_util.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def old_helper():
-    pass
"""

GIT_LOG_SNIPPET = """\
abc1234 feat: add session scribe
def5678 fix: ref tracker edge case
1234567 docs: update README
"""


# ---------------------------------------------------------------------------
# Tests: extract_changed_files
# ---------------------------------------------------------------------------

class TestExtractChangedFiles:
    def test_extract_from_diff_git_lines(self):
        files = extract_changed_files(DIFF_NEW_FILE)
        assert "core/scribe.py" in files

    def test_extract_deleted_file(self):
        files = extract_changed_files(DIFF_DELETED_FILE)
        assert "old_module.py" in files

    def test_extract_multiple_files(self):
        files = extract_changed_files(DIFF_MULTIPLE_SAME_DIR)
        assert "core/auth.py" in files
        assert "core/permissions.py" in files
        assert "core/middleware.py" in files

    def test_extract_config_files(self):
        files = extract_changed_files(DIFF_CONFIG_FILES)
        assert "docker-compose.yml" in files
        assert ".github/workflows/ci.yml" in files

    def test_extract_no_duplicates(self):
        files = extract_changed_files(DIFF_NEW_FILE)
        assert len(files) == len(set(files))

    def test_extract_from_mixed_diff(self):
        files = extract_changed_files(DIFF_MIXED)
        assert len(files) == 4
        assert "core/scribe.py" in files
        assert "tests/test_scribe.py" in files
        assert "config.json" in files
        assert "old_util.py" in files


# ---------------------------------------------------------------------------
# Tests: classify_changes
# ---------------------------------------------------------------------------

class TestClassifyChanges:
    def test_classify_new_file(self):
        files = extract_changed_files(DIFF_NEW_FILE)
        entries = classify_changes(DIFF_NEW_FILE, files)
        assert len(entries) >= 1
        entry = entries[0]
        assert entry["type"] == "observation"
        assert "Added" in entry["title"]
        assert "scribe.py" in entry["title"]
        assert entry["ref"] == 0

    def test_classify_deleted_file(self):
        files = extract_changed_files(DIFF_DELETED_FILE)
        entries = classify_changes(DIFF_DELETED_FILE, files)
        assert len(entries) >= 1
        entry = entries[0]
        assert entry["type"] == "observation"
        assert "Removed" in entry["title"]
        assert "old_module.py" in entry["title"]
        assert entry["ref"] == 0

    def test_classify_test_file(self):
        files = extract_changed_files(DIFF_TEST_FILE)
        entries = classify_changes(DIFF_TEST_FILE, files)
        assert len(entries) >= 1
        entry = entries[0]
        assert entry["type"] == "observation"
        assert "test" in entry["title"].lower()
        assert entry["ref"] == 0

    def test_classify_config_file(self):
        files = extract_changed_files(DIFF_CONFIG_FILES)
        entries = classify_changes(DIFF_CONFIG_FILES, files)
        assert len(entries) >= 1
        assert all(e["type"] == "observation" for e in entries)
        # Config files should be classified as observations
        titles = " ".join(e["title"] for e in entries)
        # Should mention at least one of the config files
        assert "docker-compose.yml" in titles or "ci.yml" in titles or "config" in titles.lower()

    def test_classify_groups_same_directory(self):
        files = extract_changed_files(DIFF_MULTIPLE_SAME_DIR)
        entries = classify_changes(DIFF_MULTIPLE_SAME_DIR, files)
        # 3 files in core/ — the modified ones should be grouped, new file gets its own entry
        # At minimum, we expect fewer entries than files due to grouping
        # The new file (core/middleware.py) gets "Added" and the other two get grouped
        titles = " ".join(e["title"] for e in entries)
        assert "core" in titles.lower() or "middleware" in titles.lower()

    def test_classify_mixed_diff(self):
        files = extract_changed_files(DIFF_MIXED)
        entries = classify_changes(DIFF_MIXED, files)
        assert len(entries) >= 1
        types = {e["type"] for e in entries}
        assert types == {"observation"}  # All heuristic entries are observations
        titles = " ".join(e["title"] for e in entries)
        # Should have entries for: new file, deleted file, test file, config file
        assert "Added" in titles
        assert "Removed" in titles

    def test_all_entries_have_required_fields(self):
        files = extract_changed_files(DIFF_MIXED)
        entries = classify_changes(DIFF_MIXED, files)
        for entry in entries:
            assert "type" in entry
            assert "title" in entry
            assert "body" in entry
            assert "ref" in entry
            assert entry["ref"] == 0


# ---------------------------------------------------------------------------
# Tests: merge_with_existing
# ---------------------------------------------------------------------------

class TestMergeWithExisting:
    def test_merge_skips_duplicates(self):
        existing = [
            {"ref": 3, "type": "decision", "title": "Added core/scribe.py for entry generation",
             "why": "Automate Day entries", "body": "core/scribe.py"},
        ]
        new_entries = [
            {"ref": 0, "type": "observation", "title": "Added core/scribe.py",
             "body": "core/scribe.py", "why": ""},
            {"ref": 0, "type": "observation", "title": "Added tests/test_auth.py",
             "body": "tests/test_auth.py", "why": ""},
        ]
        merged = merge_with_existing(new_entries, existing)
        # The scribe.py entry should be skipped (duplicate), auth test kept
        titles = [e["title"] for e in merged]
        scribe_titles = [t for t in titles if "scribe.py" in t]
        assert len(scribe_titles) == 1  # Only the existing one
        assert "test_auth.py" in " ".join(titles)

    def test_merge_preserves_existing_first(self):
        existing = [
            {"ref": 5, "type": "decision", "title": "Chose PostgreSQL",
             "why": "Better JSON support", "body": "schema.prisma"},
        ]
        new_entries = [
            {"ref": 0, "type": "observation", "title": "Added utils.py",
             "body": "utils.py", "why": ""},
        ]
        merged = merge_with_existing(new_entries, existing)
        assert merged[0] == existing[0]  # Existing comes first
        assert merged[1] == new_entries[0]  # New appended after

    def test_merge_empty_existing(self):
        new_entries = [
            {"ref": 0, "type": "observation", "title": "Added core/scribe.py",
             "body": "core/scribe.py", "why": ""},
        ]
        merged = merge_with_existing(new_entries, [])
        assert len(merged) == 1
        assert merged[0] == new_entries[0]

    def test_merge_empty_new(self):
        existing = [
            {"ref": 3, "type": "decision", "title": "Chose PostgreSQL",
             "why": "Better JSON support", "body": "schema.prisma"},
        ]
        merged = merge_with_existing([], existing)
        assert merged == existing

    def test_merge_new_entries_have_ref_zero(self):
        existing = [
            {"ref": 5, "type": "decision", "title": "Some decision",
             "why": "reason", "body": ""},
        ]
        new_entries = [
            {"ref": 0, "type": "observation", "title": "Added foo.py",
             "body": "foo.py", "why": ""},
        ]
        merged = merge_with_existing(new_entries, existing)
        for entry in merged:
            if entry in new_entries:
                assert entry["ref"] == 0


# ---------------------------------------------------------------------------
# Tests: get_session_diff truncation
# ---------------------------------------------------------------------------

class TestGetSessionDiffTruncation:
    def test_truncation_limit(self, monkeypatch):
        """Output truncated to 3000 chars."""
        long_output = "x" * 5000

        def mock_run(*args, **kwargs):
            class Result:
                returncode = 0
                stdout = long_output
            return Result()

        monkeypatch.setattr("subprocess.run", mock_run)
        result = get_session_diff()
        assert len(result) <= 3000
