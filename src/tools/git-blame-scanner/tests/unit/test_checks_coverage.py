"""Unit tests for git-blame-scanner checks/coverage.py.

Tests cover the uncovered check functions:
- check_has_authors: pass and fail paths
- check_file_fields_complete: pass and fail paths
- check_author_fields_complete: pass and fail paths
- check_knowledge_silos_identified: pass, warn, and no-silo paths
"""

from __future__ import annotations

import pytest

from scripts.checks.coverage import (
    check_has_authors,
    check_file_fields_complete,
    check_author_fields_complete,
    check_knowledge_silos_identified,
)


# ---------------------------------------------------------------------------
# check_has_authors
# ---------------------------------------------------------------------------

class TestHasAuthors:
    """Tests for check_has_authors."""

    def test_pass_authors_present(self):
        """At least one author present should pass."""
        output = {
            "data": {
                "authors": [
                    {"author_email": "a@x.com", "total_files": 1},
                ]
            }
        }
        results = check_has_authors(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "1" in results[0]["message"]

    def test_fail_no_authors(self):
        """Empty authors list should fail."""
        output = {"data": {"authors": []}}
        results = check_has_authors(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_pass_multiple_authors(self):
        """Multiple authors should pass and report count."""
        output = {
            "data": {
                "authors": [
                    {"author_email": "a@x.com"},
                    {"author_email": "b@x.com"},
                    {"author_email": "c@x.com"},
                ]
            }
        }
        results = check_has_authors(output, None)
        assert results[0]["status"] == "pass"
        assert "3" in results[0]["message"]


# ---------------------------------------------------------------------------
# check_file_fields_complete
# ---------------------------------------------------------------------------

class TestFileFieldsComplete:
    """Tests for check_file_fields_complete."""

    def test_pass_all_fields_present(self):
        """Files with all required fields should pass."""
        output = {
            "data": {
                "files": [
                    {
                        "path": "a.py",
                        "total_lines": 100,
                        "unique_authors": 2,
                        "top_author": "a@x.com",
                        "top_author_pct": 80.0,
                        "last_modified": "2025-01-01",
                        "churn_30d": 1,
                        "churn_90d": 3,
                    },
                ]
            }
        }
        results = check_file_fields_complete(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_fail_missing_fields(self):
        """Files missing required fields should fail."""
        output = {
            "data": {
                "files": [
                    {
                        "path": "incomplete.py",
                        "total_lines": 50,
                        # Missing: unique_authors, top_author, top_author_pct, etc.
                    },
                ]
            }
        }
        results = check_file_fields_complete(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "incomplete.py" in results[0]["message"]

    def test_pass_empty_files(self):
        """No files should pass (vacuously true)."""
        output = {"data": {"files": []}}
        results = check_file_fields_complete(output, None)
        assert results[0]["status"] == "pass"

    def test_fail_limits_violation_reporting(self):
        """Only first 3 violations are included in message."""
        files = [
            {"path": f"bad_{i}.py", "total_lines": i}
            for i in range(5)
        ]
        output = {"data": {"files": files}}
        results = check_file_fields_complete(output, None)
        assert results[0]["status"] == "fail"
        # Message should contain at most 3 violation examples
        msg = results[0]["message"]
        assert "5 files" in msg


# ---------------------------------------------------------------------------
# check_author_fields_complete
# ---------------------------------------------------------------------------

class TestAuthorFieldsComplete:
    """Tests for check_author_fields_complete."""

    def test_pass_all_fields_present(self):
        """Authors with all required fields should pass."""
        output = {
            "data": {
                "authors": [
                    {
                        "author_email": "a@x.com",
                        "total_files": 5,
                        "total_lines": 500,
                        "exclusive_files": 2,
                        "avg_ownership_pct": 60.0,
                    },
                ]
            }
        }
        results = check_author_fields_complete(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_fail_missing_fields(self):
        """Authors missing required fields should fail."""
        output = {
            "data": {
                "authors": [
                    {
                        "author_email": "incomplete@x.com",
                        "total_files": 3,
                        # Missing: total_lines, exclusive_files, avg_ownership_pct
                    },
                ]
            }
        }
        results = check_author_fields_complete(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "incomplete@x.com" in results[0]["message"]

    def test_pass_empty_authors(self):
        """No authors should pass (vacuously true)."""
        output = {"data": {"authors": []}}
        results = check_author_fields_complete(output, None)
        assert results[0]["status"] == "pass"


# ---------------------------------------------------------------------------
# check_knowledge_silos_identified
# ---------------------------------------------------------------------------

class TestKnowledgeSilosIdentified:
    """Tests for check_knowledge_silos_identified."""

    def test_pass_no_expected_silos(self):
        """No single-author files > 100 lines means no silos expected."""
        output = {
            "data": {
                "files": [
                    {"path": "small.py", "unique_authors": 1, "total_lines": 50},
                    {"path": "shared.py", "unique_authors": 3, "total_lines": 200},
                ],
                "knowledge_silos": [],
                "summary": {"knowledge_silo_count": 0},
            }
        }
        results = check_knowledge_silos_identified(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "No knowledge silos expected" in results[0]["message"]

    def test_pass_count_matches(self):
        """Silo count in summary matches actual qualifying files."""
        output = {
            "data": {
                "files": [
                    {"path": "silo1.py", "unique_authors": 1, "total_lines": 150},
                    {"path": "silo2.py", "unique_authors": 1, "total_lines": 200},
                    {"path": "shared.py", "unique_authors": 2, "total_lines": 300},
                ],
                "knowledge_silos": ["silo1.py", "silo2.py"],
                "summary": {"knowledge_silo_count": 2},
            }
        }
        results = check_knowledge_silos_identified(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "2 knowledge silos correctly" in results[0]["message"]

    def test_warn_count_mismatch(self):
        """Silo count mismatch produces a warning."""
        output = {
            "data": {
                "files": [
                    {"path": "silo1.py", "unique_authors": 1, "total_lines": 150},
                    {"path": "silo2.py", "unique_authors": 1, "total_lines": 200},
                ],
                "knowledge_silos": ["silo1.py"],
                "summary": {"knowledge_silo_count": 1},  # Should be 2
            }
        }
        results = check_knowledge_silos_identified(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "warn"
        assert "expected 2" in results[0]["message"]
        assert "got 1" in results[0]["message"]

    def test_boundary_exactly_100_lines_not_silo(self):
        """Files with exactly 100 lines are NOT knowledge silos (> 100 required)."""
        output = {
            "data": {
                "files": [
                    {"path": "boundary.py", "unique_authors": 1, "total_lines": 100},
                ],
                "knowledge_silos": [],
                "summary": {"knowledge_silo_count": 0},
            }
        }
        results = check_knowledge_silos_identified(output, None)
        assert results[0]["status"] == "pass"
        assert "No knowledge silos expected" in results[0]["message"]

    def test_boundary_101_lines_is_silo(self):
        """Files with 101 lines and single author ARE knowledge silos."""
        output = {
            "data": {
                "files": [
                    {"path": "silo.py", "unique_authors": 1, "total_lines": 101},
                ],
                "knowledge_silos": ["silo.py"],
                "summary": {"knowledge_silo_count": 1},
            }
        }
        results = check_knowledge_silos_identified(output, None)
        assert results[0]["status"] == "pass"
