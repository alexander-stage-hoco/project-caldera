"""Tests for checks/__init__.py uncovered functions (load_analysis, check_not_contains, check_boolean)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import (
    CheckResult,
    EvaluationReport,
    check_boolean,
    check_not_contains,
    load_analysis,
)


# ---------------------------------------------------------------------------
# load_analysis
# ---------------------------------------------------------------------------
class TestLoadAnalysis:
    """Tests for load_analysis JSON loader with normalization."""

    def test_loads_results_format(self, tmp_path: Path) -> None:
        """Legacy format with 'results' key should be normalized."""
        data = {
            "schema_version": "2.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "repo_name": "test-repo",
            "repo_path": "/tmp/test-repo",
            "results": {
                "tool": "gitleaks",
                "total_secrets": 3,
                "findings": [],
            },
        }
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        result = load_analysis(path)

        assert result["tool"] == "gitleaks"
        assert result["total_secrets"] == 3
        assert result["schema_version"] == "2.0.0"
        assert result["timestamp"] == "2026-01-01T00:00:00Z"
        assert result["repository"] == "test-repo"
        assert result["repo_path"] == "/tmp/test-repo"
        assert result["_root"] is not None

    def test_loads_flat_format(self, tmp_path: Path) -> None:
        """Flat format (no 'results' key) should be returned as-is."""
        data = {"total_secrets": 0, "findings": []}
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        result = load_analysis(path)

        assert result["total_secrets"] == 0
        assert "_root" not in result

    def test_loads_empty_results(self, tmp_path: Path) -> None:
        """Empty results dict."""
        data = {
            "schema_version": "1.0.0",
            "generated_at": "t",
            "repo_name": "empty",
            "repo_path": "/tmp",
            "results": {},
        }
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))

        result = load_analysis(path)
        assert result.get("schema_version") == "1.0.0"
        assert "_root" in result


# ---------------------------------------------------------------------------
# check_not_contains and check_boolean (covered but verifying edge cases)
# ---------------------------------------------------------------------------
class TestCheckNotContains:
    """Additional edge cases for check_not_contains."""

    def test_forbidden_found(self) -> None:
        result = check_not_contains(
            "T-1", "Test", "Forbidden check",
            forbidden_items=["bad", "worse"],
            actual_set={"good", "bad", "ok"},
        )
        assert result.passed is False
        assert "bad" in result.message

    def test_no_forbidden(self) -> None:
        result = check_not_contains(
            "T-1", "Test", "Clean check",
            forbidden_items=["bad"],
            actual_set=["good", "ok"],
        )
        assert result.passed is True


class TestCheckBoolean:
    """Additional edge cases for check_boolean."""

    def test_true_matches_true(self) -> None:
        result = check_boolean("T-1", "Test", "Bool check", expected=True, actual=True)
        assert result.passed is True

    def test_true_does_not_match_false(self) -> None:
        result = check_boolean("T-1", "Test", "Bool check", expected=True, actual=False)
        assert result.passed is False
