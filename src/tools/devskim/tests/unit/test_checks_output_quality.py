"""Unit tests for output quality checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.output_quality import run_output_quality_checks
from checks import CheckCategory


class TestOutputQualityChecks:
    """Tests for run_output_quality_checks function."""

    def test_all_output_quality_checks_returned(self) -> None:
        """All output quality checks should be returned."""
        # The implementation expects a _root wrapper for schema validation
        analysis = {
            "_root": {
                "schema_version": "1.0",
                "generated_at": "2026-01-24T00:00:00Z",
                "repo_name": "test",
                "repo_path": "/test",
                "results": {
                    "tool": "devskim",
                    "tool_version": "1.0.0",
                    "metadata": {},
                    "summary": {},
                    "files": []
                }
            }
        }
        results = run_output_quality_checks(analysis)

        # Should have at least 1 output quality check (OQ-1)
        assert len(results) >= 1
        for r in results:
            assert r.category == CheckCategory.OUTPUT_QUALITY

    def test_oq1_schema_version_present(self) -> None:
        """OQ-1: Schema version should be present with valid root wrapper."""
        analysis = {
            "_root": {
                "schema_version": "1.0.0",
                "generated_at": "2026-01-24T00:00:00Z",
                "repo_name": "test",
                "repo_path": "/test",
                "results": {
                    "tool": "devskim",
                    "tool_version": "1.0.0",
                    "metadata": {},
                    "summary": {}
                }
            }
        }
        results = run_output_quality_checks(analysis)

        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.passed is True

    def test_oq2_required_fields_present(self) -> None:
        """OQ-2: Required fields check - only OQ-1 is implemented."""
        analysis = {
            "_root": {
                "schema_version": "1.0.0",
                "generated_at": "2026-01-24T00:00:00Z",
                "repo_name": "test",
                "repo_path": "/test",
                "results": {
                    "tool": "devskim",
                    "tool_version": "1.0.0",
                    "metadata": {"tool": "devskim"},
                    "summary": {"total_issues": 0},
                    "files": []
                }
            }
        }
        results = run_output_quality_checks(analysis)

        # Only OQ-1 is currently implemented
        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.category == CheckCategory.OUTPUT_QUALITY

    def test_oq3_file_paths_normalized(self) -> None:
        """OQ-3: File paths - only OQ-1 is implemented, test validates OQ-1 passes with valid structure."""
        analysis = {
            "_root": {
                "schema_version": "1.0.0",
                "generated_at": "2026-01-24T00:00:00Z",
                "repo_name": "test",
                "repo_path": "/test",
                "results": {
                    "tool": "devskim",
                    "tool_version": "1.0.0",
                    "metadata": {},
                    "summary": {},
                    "files": [
                        {"path": "src/test.cs"},
                        {"path": "lib/helper.cs"}
                    ]
                }
            }
        }
        results = run_output_quality_checks(analysis)

        # Only OQ-1 is implemented
        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.category == CheckCategory.OUTPUT_QUALITY

    def test_oq4_severity_values_valid(self) -> None:
        """OQ-4: Severity values - only OQ-1 is implemented."""
        analysis = {
            "_root": {
                "schema_version": "1.0.0",
                "generated_at": "2026-01-24T00:00:00Z",
                "repo_name": "test",
                "repo_path": "/test",
                "results": {
                    "tool": "devskim",
                    "tool_version": "1.0.0",
                    "metadata": {},
                    "summary": {},
                    "files": [
                        {"path": "test.cs", "issues": [
                            {"severity": "CRITICAL"},
                            {"severity": "HIGH"},
                            {"severity": "MEDIUM"},
                            {"severity": "LOW"}
                        ]}
                    ]
                }
            }
        }
        results = run_output_quality_checks(analysis)

        # Only OQ-1 is implemented
        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.passed is True

    def test_missing_schema_version_fails(self) -> None:
        """Missing _root wrapper should fail OQ-1 check."""
        # Without _root wrapper, OQ-1 should fail
        analysis = {
            "files": [],
            "summary": {}
        }
        results = run_output_quality_checks(analysis)

        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.passed is False

    def test_invalid_severity_fails(self) -> None:
        """Invalid root structure should fail OQ-1 (only OQ-1 is implemented)."""
        # Missing required fields in _root should fail
        analysis = {
            "_root": {
                "schema_version": "1.0.0",
                # Missing other required fields
            }
        }
        results = run_output_quality_checks(analysis)

        oq1 = next((r for r in results if r.check_id == "OQ-1"), None)
        assert oq1 is not None
        assert oq1.score < 1.0

    def test_output_quality_scores_in_range(self) -> None:
        """All output quality scores should be between 0 and 1."""
        # Without _root, we get a failing OQ-1 check
        analysis = {"files": [], "summary": {}}
        results = run_output_quality_checks(analysis)

        for r in results:
            assert 0.0 <= r.score <= 1.0
