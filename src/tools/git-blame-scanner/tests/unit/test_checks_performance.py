"""Unit tests for git-blame-scanner checks/performance.py.

Tests cover the uncovered check functions:
- check_reasonable_file_count: zero, normal, and very large counts
- check_author_count_reasonable: zero authors, ratio > 1, normal ratio
- check_commit_sha_valid: valid 40-char hex, invalid formats
"""

from __future__ import annotations

import pytest

from scripts.checks.performance import (
    check_reasonable_file_count,
    check_author_count_reasonable,
    check_commit_sha_valid,
)


# ---------------------------------------------------------------------------
# check_reasonable_file_count
# ---------------------------------------------------------------------------

class TestReasonableFileCount:
    """Tests for check_reasonable_file_count."""

    def test_fail_zero_files(self):
        """Zero files analyzed should fail."""
        output = {
            "data": {
                "files": [],
                "summary": {"total_files_analyzed": 0},
            }
        }
        results = check_reasonable_file_count(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "No files" in results[0]["message"]

    def test_pass_normal_count(self):
        """A moderate file count should pass."""
        output = {
            "data": {
                "files": [{"path": f"f{i}.py"} for i in range(50)],
                "summary": {"total_files_analyzed": 50},
            }
        }
        results = check_reasonable_file_count(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "50" in results[0]["message"]

    def test_warn_very_large_count(self):
        """Over 100k files should warn."""
        output = {
            "data": {
                "files": [],
                "summary": {"total_files_analyzed": 200000},
            }
        }
        results = check_reasonable_file_count(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "warn"
        assert "200000" in results[0]["message"]

    def test_fallback_to_files_length(self):
        """If total_files_analyzed is missing, falls back to len(files)."""
        output = {
            "data": {
                "files": [{"path": "a.py"}, {"path": "b.py"}],
                "summary": {},
            }
        }
        results = check_reasonable_file_count(output, None)
        assert results[0]["status"] == "pass"
        assert "2" in results[0]["message"]


# ---------------------------------------------------------------------------
# check_author_count_reasonable
# ---------------------------------------------------------------------------

class TestAuthorCountReasonable:
    """Tests for check_author_count_reasonable."""

    def test_pass_no_files(self):
        """No files => skipped, still passes."""
        output = {
            "data": {
                "files": [],
                "authors": [],
            }
        }
        results = check_author_count_reasonable(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "skipped" in results[0]["message"].lower()

    def test_fail_no_authors_with_files(self):
        """Files present but no authors should fail."""
        output = {
            "data": {
                "files": [{"path": "a.py"}],
                "authors": [],
            }
        }
        results = check_author_count_reasonable(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "No authors" in results[0]["message"]

    def test_pass_ratio_less_than_one(self):
        """Fewer authors than files (typical) should pass."""
        output = {
            "data": {
                "files": [{"path": f"f{i}.py"} for i in range(10)],
                "authors": [
                    {"author_email": "a@x.com"},
                    {"author_email": "b@x.com"},
                ],
            }
        }
        results = check_author_count_reasonable(output, None)
        assert results[0]["status"] == "pass"
        assert "0.20" in results[0]["message"]

    def test_pass_ratio_greater_than_one(self):
        """More authors than files (many contributors) should still pass."""
        output = {
            "data": {
                "files": [{"path": "single.py"}],
                "authors": [
                    {"author_email": f"dev{i}@x.com"} for i in range(5)
                ],
            }
        }
        results = check_author_count_reasonable(output, None)
        assert results[0]["status"] == "pass"
        assert "many contributors" in results[0]["message"].lower()


# ---------------------------------------------------------------------------
# check_commit_sha_valid
# ---------------------------------------------------------------------------

class TestCommitShaValid:
    """Tests for check_commit_sha_valid."""

    def test_pass_valid_sha(self):
        """A valid 40-char lowercase hex SHA should pass."""
        output = {
            "metadata": {"commit": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"}
        }
        results = check_commit_sha_valid(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_pass_all_zeros(self):
        """All-zeros SHA (placeholder for non-git) should pass."""
        output = {"metadata": {"commit": "0" * 40}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "pass"

    def test_warn_short_sha(self):
        """Short SHA should warn."""
        output = {"metadata": {"commit": "abc123"}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "warn"

    def test_warn_non_hex_chars(self):
        """SHA with non-hex characters should warn."""
        output = {"metadata": {"commit": "g" * 40}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "warn"

    def test_warn_empty_sha(self):
        """Empty commit SHA should warn."""
        output = {"metadata": {"commit": ""}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "warn"

    def test_warn_missing_commit(self):
        """Missing commit key should warn."""
        output = {"metadata": {}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "warn"

    def test_pass_uppercase_hex(self):
        """Uppercase hex should also pass (the check uses .lower())."""
        output = {"metadata": {"commit": "A" * 40}}
        results = check_commit_sha_valid(output, None)
        assert results[0]["status"] == "pass"
