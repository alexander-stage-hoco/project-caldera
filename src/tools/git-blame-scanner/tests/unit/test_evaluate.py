"""Unit tests for git-blame-scanner evaluate script."""

from __future__ import annotations

import pytest


def test_check_loading():
    """Test that check modules load correctly."""
    from evaluate import load_checks
    checks = load_checks()
    assert len(checks) > 0


def test_summary_computation():
    """Test summary statistics computation."""
    from evaluate import compute_summary

    results = [
        {"check_id": "test.a", "status": "pass"},
        {"check_id": "test.b", "status": "fail"},
    ]
    summary = compute_summary(results)
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1


def test_summary_with_warn_and_error():
    """Test summary with warn and error statuses."""
    from evaluate import compute_summary

    results = [
        {"check_id": "test.a", "status": "pass"},
        {"check_id": "test.b", "status": "fail"},
        {"check_id": "test.c", "status": "warn"},
        {"check_id": "test.d", "status": "error"},
    ]
    summary = compute_summary(results)
    assert summary["total"] == 4
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["warned"] == 1
    assert summary["errored"] == 1
    assert summary["decision"] == "FAIL"


def test_summary_all_pass():
    """Test summary when all checks pass."""
    from evaluate import compute_summary

    results = [
        {"check_id": "test.a", "status": "pass"},
        {"check_id": "test.b", "status": "pass"},
        {"check_id": "test.c", "status": "warn"},
    ]
    summary = compute_summary(results)
    assert summary["decision"] == "PASS"
    assert summary["score"] == pytest.approx(2 / 3, rel=0.01)


class TestAccuracyChecks:
    """Tests for accuracy check functions."""

    def test_ownership_bounds_valid(self):
        """Test ownership bounds check with valid data."""
        from checks.accuracy import check_ownership_bounds

        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 100.0},
                    {"path": "b.py", "top_author_pct": 50.0},
                    {"path": "c.py", "top_author_pct": 0.0},
                ]
            }
        }
        results = check_ownership_bounds(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_ownership_bounds_invalid(self):
        """Test ownership bounds check with invalid data."""
        from checks.accuracy import check_ownership_bounds

        output = {
            "data": {
                "files": [
                    {"path": "a.py", "top_author_pct": 150.0},
                    {"path": "b.py", "top_author_pct": -10.0},
                ]
            }
        }
        results = check_ownership_bounds(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_churn_monotonicity_valid(self):
        """Test churn monotonicity with valid data."""
        from checks.accuracy import check_churn_monotonicity

        output = {
            "data": {
                "files": [
                    {"path": "a.py", "churn_30d": 2, "churn_90d": 5},
                    {"path": "b.py", "churn_30d": 0, "churn_90d": 0},
                    {"path": "c.py", "churn_30d": 3, "churn_90d": 3},
                ]
            }
        }
        results = check_churn_monotonicity(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_churn_monotonicity_invalid(self):
        """Test churn monotonicity with invalid data."""
        from checks.accuracy import check_churn_monotonicity

        output = {
            "data": {
                "files": [
                    {"path": "a.py", "churn_30d": 10, "churn_90d": 5},
                ]
            }
        }
        results = check_churn_monotonicity(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"


class TestCoverageChecks:
    """Tests for coverage check functions."""

    def test_has_files_present(self):
        """Test has_files check when files are present."""
        from checks.coverage import check_has_files

        output = {
            "data": {
                "files": [{"path": "a.py"}]
            }
        }
        results = check_has_files(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_has_files_empty(self):
        """Test has_files check when no files."""
        from checks.coverage import check_has_files

        output = {"data": {"files": []}}
        results = check_has_files(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_has_summary_complete(self):
        """Test has_summary with complete summary."""
        from checks.coverage import check_has_summary

        output = {
            "data": {
                "summary": {
                    "total_files_analyzed": 10,
                    "total_authors": 3,
                    "single_author_files": 2,
                    "single_author_pct": 20.0,
                    "high_concentration_files": 5,
                    "high_concentration_pct": 50.0,
                }
            }
        }
        results = check_has_summary(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_has_summary_incomplete(self):
        """Test has_summary with missing fields."""
        from checks.coverage import check_has_summary

        output = {
            "data": {
                "summary": {
                    "total_files_analyzed": 10,
                }
            }
        }
        results = check_has_summary(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"


class TestPerformanceChecks:
    """Tests for performance check functions."""

    def test_paths_normalized_valid(self):
        """Test path normalization with valid paths."""
        from checks.performance import check_paths_normalized

        output = {
            "data": {
                "files": [
                    {"path": "src/main.py"},
                    {"path": "tests/test_main.py"},
                ]
            }
        }
        results = check_paths_normalized(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_paths_normalized_invalid(self):
        """Test path normalization with invalid paths."""
        from checks.performance import check_paths_normalized

        output = {
            "data": {
                "files": [
                    {"path": "/absolute/path.py"},
                    {"path": "./relative/path.py"},
                ]
            }
        }
        results = check_paths_normalized(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "fail"

    def test_metadata_complete(self):
        """Test metadata completeness check."""
        from checks.performance import check_metadata_complete

        output = {
            "metadata": {
                "tool_name": "git-blame-scanner",
                "tool_version": "1.0.0",
                "run_id": "test",
                "repo_id": "test",
                "branch": "main",
                "commit": "a" * 40,
                "timestamp": "2025-01-01T00:00:00Z",
                "schema_version": "1.0.0",
            }
        }
        results = check_metadata_complete(output, None)
        assert len(results) == 1
        assert results[0]["status"] == "pass"
