"""Unit tests for accuracy checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.accuracy import run_accuracy_checks


class TestAccuracyChecks:
    """Tests for run_accuracy_checks function."""

    def test_sa1_total_secrets_match(self) -> None:
        """SA-1: Total secrets count matches expected."""
        analysis = {"results": {"total_secrets": 5}}
        ground_truth = {"expected": {"total_secrets": 5}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa1 = next(r for r in results if r.check_id == "SA-1")

        assert sa1.passed is True
        assert sa1.category == "Accuracy"

    def test_sa1_total_secrets_mismatch(self) -> None:
        """SA-1: Total secrets count mismatch fails."""
        analysis = {"results": {"total_secrets": 3}}
        ground_truth = {"expected": {"total_secrets": 5}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa1 = next(r for r in results if r.check_id == "SA-1")

        assert sa1.passed is False
        assert "expected 5, got 3" in sa1.message

    def test_sa2_unique_secrets_match(self) -> None:
        """SA-2: Unique secrets count matches."""
        analysis = {"results": {"unique_secrets": 3}}
        ground_truth = {"expected": {"unique_secrets": 3}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa2 = next(r for r in results if r.check_id == "SA-2")

        assert sa2.passed is True

    def test_sa3_secrets_in_head_match(self) -> None:
        """SA-3: Secrets in HEAD matches."""
        analysis = {"results": {"secrets_in_head": 2}}
        ground_truth = {"expected": {"secrets_in_head": 2}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa3 = next(r for r in results if r.check_id == "SA-3")

        assert sa3.passed is True

    def test_sa4_secrets_in_history_match(self) -> None:
        """SA-4: Secrets in history matches."""
        analysis = {"results": {"secrets_in_history": 1}}
        ground_truth = {"expected": {"secrets_in_history": 1}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa4 = next(r for r in results if r.check_id == "SA-4")

        assert sa4.passed is True

    def test_sa5_files_with_secrets_match(self) -> None:
        """SA-5: Files with secrets count matches."""
        analysis = {"results": {"files_with_secrets": 2}}
        ground_truth = {"expected": {"files_with_secrets": 2}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa5 = next(r for r in results if r.check_id == "SA-5")

        assert sa5.passed is True

    def test_sa6_commits_with_secrets_match(self) -> None:
        """SA-6: Commits with secrets count matches."""
        analysis = {"results": {"commits_with_secrets": 3}}
        ground_truth = {"expected": {"commits_with_secrets": 3}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa6 = next(r for r in results if r.check_id == "SA-6")

        assert sa6.passed is True

    def test_sa7_rule_ids_all_found(self) -> None:
        """SA-7: All expected rule IDs found."""
        analysis = {
            "results": {
                "secrets_by_rule": {
                    "github-pat": 1,
                    "stripe-access-token": 2,
                    "generic-api-key": 1,
                }
            }
        }
        ground_truth = {"expected": {"rule_ids": ["github-pat", "stripe-access-token"]}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa7 = next(r for r in results if r.check_id == "SA-7")

        assert sa7.passed is True

    def test_sa7_rule_ids_missing(self) -> None:
        """SA-7: Missing expected rule ID fails."""
        analysis = {"results": {"secrets_by_rule": {"github-pat": 1}}}
        ground_truth = {"expected": {"rule_ids": ["github-pat", "stripe-access-token"]}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa7 = next(r for r in results if r.check_id == "SA-7")

        assert sa7.passed is False
        assert "missing" in sa7.message.lower()

    def test_sa8_files_with_secrets_all_found(self) -> None:
        """SA-8: All expected files with secrets found."""
        analysis = {
            "results": {
                "files": {
                    ".env": {"secret_count": 1},
                    "config/api.py": {"secret_count": 1},
                }
            }
        }
        ground_truth = {"expected": {"files_with_secrets_list": [".env", "config/api.py"]}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa8 = next(r for r in results if r.check_id == "SA-8")

        assert sa8.passed is True

    def test_sa8_files_missing(self) -> None:
        """SA-8: Missing expected file fails."""
        analysis = {"results": {"files": {".env": {"secret_count": 1}}}}
        ground_truth = {"expected": {"files_with_secrets_list": [".env", "config/api.py"]}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa8 = next(r for r in results if r.check_id == "SA-8")

        assert sa8.passed is False

    def test_sa8_no_files_expected_passes(self) -> None:
        """SA-8: No specific files expected passes."""
        analysis = {"results": {"files": {}}}
        ground_truth = {"expected": {}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa8 = next(r for r in results if r.check_id == "SA-8")

        assert sa8.passed is True
        assert "No specific files expected" in sa8.message

    def test_sa9_rule_counts_match(self) -> None:
        """SA-9: Rule counts match expected."""
        analysis = {
            "results": {
                "secrets_by_rule": {"github-pat": 2, "stripe-access-token": 1}
            }
        }
        ground_truth = {
            "expected": {
                "secrets_by_rule": {"github-pat": 2, "stripe-access-token": 1}
            }
        }

        results = run_accuracy_checks(analysis, ground_truth)
        sa9 = next(r for r in results if r.check_id == "SA-9")

        assert sa9.passed is True

    def test_sa9_rule_counts_mismatch(self) -> None:
        """SA-9: Rule count mismatch fails."""
        analysis = {"results": {"secrets_by_rule": {"github-pat": 1}}}
        ground_truth = {"expected": {"secrets_by_rule": {"github-pat": 2}}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa9 = next(r for r in results if r.check_id == "SA-9")

        assert sa9.passed is False
        assert "mismatch" in sa9.message.lower()

    def test_sa10_findings_all_found(self) -> None:
        """SA-10: All expected findings found."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "rule_id": "github-pat", "line_number": 3},
                    {"file_path": "config/api.py", "rule_id": "stripe-access-token", "line_number": 5},
                ]
            }
        }
        ground_truth = {
            "expected": {
                "findings": [
                    {"file_path": ".env", "rule_id": "github-pat", "line_number": 3},
                    {"file_path": "config/api.py", "rule_id": "stripe-access-token", "line_number": 5},
                ]
            }
        }

        results = run_accuracy_checks(analysis, ground_truth)
        sa10 = next(r for r in results if r.check_id == "SA-10")

        assert sa10.passed is True

    def test_sa10_findings_missing(self) -> None:
        """SA-10: Missing expected finding fails."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "rule_id": "github-pat", "line_number": 3},
                ]
            }
        }
        ground_truth = {
            "expected": {
                "findings": [
                    {"file_path": ".env", "rule_id": "github-pat", "line_number": 3},
                    {"file_path": "config/api.py", "rule_id": "stripe-access-token", "line_number": 5},
                ]
            }
        }

        results = run_accuracy_checks(analysis, ground_truth)
        sa10 = next(r for r in results if r.check_id == "SA-10")

        assert sa10.passed is False
        assert "Missing" in sa10.message

    def test_sa10_no_findings_expected_passes(self) -> None:
        """SA-10: No specific findings expected passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa10 = next(r for r in results if r.check_id == "SA-10")

        assert sa10.passed is True

    def test_all_checks_return_10_results(self) -> None:
        """All 10 accuracy checks should be returned."""
        analysis = {
            "results": {
                "total_secrets": 0,
                "unique_secrets": 0,
                "secrets_in_head": 0,
                "secrets_in_history": 0,
                "files_with_secrets": 0,
                "commits_with_secrets": 0,
                "secrets_by_rule": {},
                "files": {},
                "findings": [],
            }
        }
        ground_truth = {"expected": {}}

        results = run_accuracy_checks(analysis, ground_truth)

        assert len(results) == 11
        check_ids = {r.check_id for r in results}
        expected_ids = {f"SA-{i}" for i in range(1, 12)}
        assert check_ids == expected_ids

    def test_handles_flat_analysis_format(self) -> None:
        """Should handle flat analysis format (no results wrapper)."""
        analysis = {"total_secrets": 5, "unique_secrets": 5}
        ground_truth = {"expected": {"total_secrets": 5, "unique_secrets": 5}}

        results = run_accuracy_checks(analysis, ground_truth)
        sa1 = next(r for r in results if r.check_id == "SA-1")
        sa2 = next(r for r in results if r.check_id == "SA-2")

        assert sa1.passed is True
        assert sa2.passed is True
