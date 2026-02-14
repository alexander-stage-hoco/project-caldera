"""Unit tests for git-blame-scanner checks/accuracy.py.

Tests cover the uncovered check functions:
- check_unique_authors_positive: pass and fail paths
- check_exclusive_files_bound: pass and fail paths
- check_single_author_consistency: pass and fail paths
- check_high_concentration_consistency: pass and fail paths
"""

from __future__ import annotations

import pytest

from scripts.checks.accuracy import (
    check_unique_authors_positive,
    check_exclusive_files_bound,
    check_single_author_consistency,
    check_high_concentration_consistency,
)


# ---------------------------------------------------------------------------
# check_unique_authors_positive
# ---------------------------------------------------------------------------

class TestUniqueAuthorsPositive:
    """Tests for check_unique_authors_positive."""

    def test_pass_all_valid(self):
        """All files with unique_authors >= 1 should pass."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "unique_authors": 1},
                    {"path": "b.py", "unique_authors": 3},
                    {"path": "c.py", "unique_authors": 10},
                ]
            }
        }
        results = check_unique_authors_positive(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
        assert "3" in results[0]["message"]  # file count mentioned

    def test_fail_zero_authors(self):
        """A file with unique_authors == 0 should fail."""
        output = {
            "data": {
                "files": [
                    {"path": "ok.py", "unique_authors": 2},
                    {"path": "bad.py", "unique_authors": 0},
                ]
            }
        }
        results = check_unique_authors_positive(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "bad.py" in results[0]["message"]

    def test_fail_negative_authors(self):
        """A file with negative unique_authors should fail."""
        output = {
            "data": {
                "files": [
                    {"path": "neg.py", "unique_authors": -1},
                ]
            }
        }
        results = check_unique_authors_positive(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_empty_files(self):
        """No files should pass (vacuously true)."""
        output = {"data": {"files": []}}
        results = check_unique_authors_positive(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"


# ---------------------------------------------------------------------------
# check_exclusive_files_bound
# ---------------------------------------------------------------------------

class TestExclusiveFilesBound:
    """Tests for check_exclusive_files_bound."""

    def test_pass_valid_bounds(self):
        """exclusive_files <= total_files for all authors should pass."""
        output = {
            "data": {
                "authors": [
                    {"author_email": "a@x.com", "exclusive_files": 0, "total_files": 5},
                    {"author_email": "b@x.com", "exclusive_files": 3, "total_files": 3},
                    {"author_email": "c@x.com", "exclusive_files": 1, "total_files": 10},
                ]
            }
        }
        results = check_exclusive_files_bound(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_fail_exclusive_exceeds_total(self):
        """exclusive_files > total_files should fail."""
        output = {
            "data": {
                "authors": [
                    {"author_email": "a@x.com", "exclusive_files": 5, "total_files": 3},
                ]
            }
        }
        results = check_exclusive_files_bound(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "a@x.com" in results[0]["message"]

    def test_empty_authors(self):
        """No authors should pass (vacuously true)."""
        output = {"data": {"authors": []}}
        results = check_exclusive_files_bound(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"


# ---------------------------------------------------------------------------
# check_single_author_consistency
# ---------------------------------------------------------------------------

class TestSingleAuthorConsistency:
    """Tests for check_single_author_consistency."""

    def test_pass_consistent(self):
        """Summary matches actual single-author file count."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "unique_authors": 1},
                    {"path": "b.py", "unique_authors": 2},
                    {"path": "c.py", "unique_authors": 1},
                ],
                "summary": {"single_author_files": 2},
            }
        }
        results = check_single_author_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_fail_mismatch(self):
        """Summary disagrees with actual count."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "unique_authors": 1},
                    {"path": "b.py", "unique_authors": 1},
                ],
                "summary": {"single_author_files": 1},  # Wrong: should be 2
            }
        }
        results = check_single_author_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "counted 2" in results[0]["message"]
        assert "reported 1" in results[0]["message"]

    def test_pass_zero_single_author(self):
        """No single-author files, summary says 0."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "unique_authors": 3},
                ],
                "summary": {"single_author_files": 0},
            }
        }
        results = check_single_author_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"


# ---------------------------------------------------------------------------
# check_high_concentration_consistency
# ---------------------------------------------------------------------------

class TestHighConcentrationConsistency:
    """Tests for check_high_concentration_consistency."""

    def test_pass_consistent(self):
        """Summary matches actual high-concentration file count."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 95.0},
                    {"path": "b.py", "top_author_pct": 50.0},
                    {"path": "c.py", "top_author_pct": 80.0},  # Exactly 80 => counts
                ],
                "summary": {"high_concentration_files": 2},
            }
        }
        results = check_high_concentration_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_fail_mismatch(self):
        """Summary disagrees with actual count."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 100.0},
                    {"path": "b.py", "top_author_pct": 90.0},
                ],
                "summary": {"high_concentration_files": 1},  # Wrong: should be 2
            }
        }
        results = check_high_concentration_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert "counted 2" in results[0]["message"]

    def test_pass_none_high_concentration(self):
        """No high-concentration files, summary says 0."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 33.3},
                    {"path": "b.py", "top_author_pct": 50.0},
                ],
                "summary": {"high_concentration_files": 0},
            }
        }
        results = check_high_concentration_consistency(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_boundary_exactly_80(self):
        """Files with exactly 80% should be counted as high concentration."""
        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 80.0},
                    {"path": "b.py", "top_author_pct": 79.99},
                ],
                "summary": {"high_concentration_files": 1},
            }
        }
        results = check_high_concentration_consistency(output, None)
        assert results[0]["status"] == "pass"
