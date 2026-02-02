"""Unit tests for coverage checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.coverage import run_coverage_checks


class TestCoverageChecks:
    """Tests for run_coverage_checks function."""

    def test_sc1_schema_version_present(self) -> None:
        """SC-1: Schema version present passes."""
        analysis = {"results": {"schema_version": "2.0.0"}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc1 = next(r for r in results if r.check_id == "SC-1")

        assert sc1.passed is True
        assert "present" in sc1.message.lower()

    def test_sc1_schema_version_missing(self) -> None:
        """SC-1: Schema version missing fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc1 = next(r for r in results if r.check_id == "SC-1")

        assert sc1.passed is False
        assert "missing" in sc1.message.lower()

    def test_sc2_tool_version_present(self) -> None:
        """SC-2: Tool version present passes."""
        analysis = {"results": {"tool_version": "8.18.4"}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc2 = next(r for r in results if r.check_id == "SC-2")

        assert sc2.passed is True

    def test_sc2_tool_version_empty(self) -> None:
        """SC-2: Empty tool version fails."""
        analysis = {"results": {"tool_version": ""}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc2 = next(r for r in results if r.check_id == "SC-2")

        assert sc2.passed is False

    def test_sc2_tool_version_missing(self) -> None:
        """SC-2: Missing tool version fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc2 = next(r for r in results if r.check_id == "SC-2")

        assert sc2.passed is False

    def test_sc3_timestamp_present(self) -> None:
        """SC-3: Timestamp present passes."""
        analysis = {"results": {"timestamp": "2026-01-21T00:00:00Z"}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc3 = next(r for r in results if r.check_id == "SC-3")

        assert sc3.passed is True

    def test_sc3_timestamp_missing(self) -> None:
        """SC-3: Timestamp missing fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc3 = next(r for r in results if r.check_id == "SC-3")

        assert sc3.passed is False

    def test_sc4_all_summary_metrics_present(self) -> None:
        """SC-4: All summary metrics present passes."""
        analysis = {
            "results": {
                "total_secrets": 5,
                "unique_secrets": 4,
                "secrets_in_head": 3,
                "secrets_in_history": 2,
                "files_with_secrets": 2,
                "commits_with_secrets": 1,
            }
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc4 = next(r for r in results if r.check_id == "SC-4")

        assert sc4.passed is True
        assert "All summary metrics present" in sc4.message

    def test_sc4_some_metrics_missing(self) -> None:
        """SC-4: Missing some summary metrics fails."""
        analysis = {
            "results": {
                "total_secrets": 5,
                "unique_secrets": 4,
                # missing secrets_in_head, secrets_in_history, etc.
            }
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc4 = next(r for r in results if r.check_id == "SC-4")

        assert sc4.passed is False
        assert "Missing" in sc4.message

    def test_sc5_findings_list_present(self) -> None:
        """SC-5: Findings list present passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc5 = next(r for r in results if r.check_id == "SC-5")

        assert sc5.passed is True

    def test_sc5_findings_list_missing(self) -> None:
        """SC-5: Findings list missing fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc5 = next(r for r in results if r.check_id == "SC-5")

        assert sc5.passed is False

    def test_sc6_files_summary_present(self) -> None:
        """SC-6: Files summary present passes."""
        analysis = {"results": {"files": {}}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc6 = next(r for r in results if r.check_id == "SC-6")

        assert sc6.passed is True

    def test_sc6_files_summary_missing(self) -> None:
        """SC-6: Files summary missing fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc6 = next(r for r in results if r.check_id == "SC-6")

        assert sc6.passed is False

    def test_sc7_directories_present(self) -> None:
        """SC-7: Directories present passes."""
        analysis = {"results": {"directories": {}}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc7 = next(r for r in results if r.check_id == "SC-7")

        assert sc7.passed is True

    def test_sc7_directories_missing(self) -> None:
        """SC-7: Directories missing fails."""
        analysis = {"results": {}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc7 = next(r for r in results if r.check_id == "SC-7")

        assert sc7.passed is False

    def test_sc8_all_findings_have_required_fields(self) -> None:
        """SC-8: All findings have required fields passes."""
        analysis = {
            "results": {
                "findings": [
                    {
                        "file_path": ".env",
                        "line_number": 5,
                        "rule_id": "github-pat",
                        "secret_type": "github-pat",
                        "commit_hash": "abc123",
                        "fingerprint": "fp123",
                    },
                    {
                        "file_path": "config.py",
                        "line_number": 10,
                        "rule_id": "stripe-key",
                        "secret_type": "stripe-key",
                        "commit_hash": "def456",
                        "fingerprint": "fp456",
                    },
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc8 = next(r for r in results if r.check_id == "SC-8")

        assert sc8.passed is True

    def test_sc8_finding_missing_required_field(self) -> None:
        """SC-8: Finding missing required field fails."""
        analysis = {
            "results": {
                "findings": [
                    {
                        "file_path": ".env",
                        # missing line_number
                        "rule_id": "github-pat",
                        "secret_type": "github-pat",
                        "commit_hash": "abc123",
                        "fingerprint": "fp123",
                    }
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc8 = next(r for r in results if r.check_id == "SC-8")

        assert sc8.passed is False
        assert "Invalid" in sc8.message

    def test_sc8_finding_with_null_field(self) -> None:
        """SC-8: Finding with null required field fails."""
        analysis = {
            "results": {
                "findings": [
                    {
                        "file_path": ".env",
                        "line_number": None,
                        "rule_id": "github-pat",
                        "secret_type": "github-pat",
                        "commit_hash": "abc123",
                        "fingerprint": "fp123",
                    }
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc8 = next(r for r in results if r.check_id == "SC-8")

        assert sc8.passed is False

    def test_sc8_empty_findings_passes(self) -> None:
        """SC-8: Empty findings list passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)
        sc8 = next(r for r in results if r.check_id == "SC-8")

        assert sc8.passed is True

    def test_all_checks_return_8_results(self) -> None:
        """All 8 coverage checks should be returned."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)

        assert len(results) == 8
        check_ids = {r.check_id for r in results}
        expected_ids = {f"SC-{i}" for i in range(1, 9)}
        assert check_ids == expected_ids

    def test_handles_flat_analysis_format(self) -> None:
        """Should handle flat analysis format (no results wrapper)."""
        analysis = {
            "schema_version": "2.0.0",
            "tool_version": "8.18.4",
            "timestamp": "2026-01-21T00:00:00Z",
            "total_secrets": 0,
            "unique_secrets": 0,
            "secrets_in_head": 0,
            "secrets_in_history": 0,
            "files_with_secrets": 0,
            "commits_with_secrets": 0,
            "findings": [],
            "files": {},
            "directories": {},
        }
        ground_truth = {"expected": {}}

        results = run_coverage_checks(analysis, ground_truth)

        # All should pass for complete flat format
        sc1 = next(r for r in results if r.check_id == "SC-1")
        sc2 = next(r for r in results if r.check_id == "SC-2")

        assert sc1.passed is True
        assert sc2.passed is True
