"""Unit tests for detection checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.detection import run_detection_checks


class TestDetectionChecks:
    """Tests for run_detection_checks function."""

    def test_sd1_no_false_negatives(self) -> None:
        """SD-1: Actual >= expected (no false negatives) passes."""
        analysis = {"results": {"total_secrets": 5}}
        ground_truth = {"expected": {"total_secrets": 3}}

        results = run_detection_checks(analysis, ground_truth)
        sd1 = next(r for r in results if r.check_id == "SD-1")

        assert sd1.passed is True
        assert "Found 5 secrets, expected at least 3" in sd1.message

    def test_sd1_false_negatives_detected(self) -> None:
        """SD-1: Actual < expected (false negatives) fails."""
        analysis = {"results": {"total_secrets": 2}}
        ground_truth = {"expected": {"total_secrets": 5}}

        results = run_detection_checks(analysis, ground_truth)
        sd1 = next(r for r in results if r.check_id == "SD-1")

        assert sd1.passed is False

    def test_sd1_exact_match_passes(self) -> None:
        """SD-1: Exact match passes."""
        analysis = {"results": {"total_secrets": 3}}
        ground_truth = {"expected": {"total_secrets": 3}}

        results = run_detection_checks(analysis, ground_truth)
        sd1 = next(r for r in results if r.check_id == "SD-1")

        assert sd1.passed is True

    def test_sd2_no_unexpected_rules(self) -> None:
        """SD-2: No unexpected rule IDs passes."""
        analysis = {"results": {"secrets_by_rule": {"github-pat": 1, "stripe-key": 1}}}
        ground_truth = {"expected": {"rule_ids": ["github-pat", "stripe-key", "aws-key"]}}

        results = run_detection_checks(analysis, ground_truth)
        sd2 = next(r for r in results if r.check_id == "SD-2")

        assert sd2.passed is True

    def test_sd2_unexpected_rules_found(self) -> None:
        """SD-2: Unexpected rule IDs found fails."""
        analysis = {
            "results": {
                "secrets_by_rule": {"github-pat": 1, "unexpected-rule": 1}
            }
        }
        ground_truth = {"expected": {"rule_ids": ["github-pat"]}}

        results = run_detection_checks(analysis, ground_truth)
        sd2 = next(r for r in results if r.check_id == "SD-2")

        assert sd2.passed is False
        assert "Unexpected rules" in sd2.message

    def test_sd2_no_expected_rules_skips(self) -> None:
        """SD-2: No expected rules defined skips check."""
        analysis = {"results": {"secrets_by_rule": {"github-pat": 1}}}
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd2 = next(r for r in results if r.check_id == "SD-2")

        assert sd2.passed is True
        assert "skipping" in sd2.message.lower()

    def test_sd3_historical_secrets_match(self) -> None:
        """SD-3: Historical secrets count matches."""
        analysis = {"results": {"secrets_in_history": 2}}
        ground_truth = {"expected": {"secrets_in_history": 2}}

        results = run_detection_checks(analysis, ground_truth)
        sd3 = next(r for r in results if r.check_id == "SD-3")

        assert sd3.passed is True

    def test_sd3_historical_secrets_mismatch(self) -> None:
        """SD-3: Historical secrets mismatch fails."""
        analysis = {"results": {"secrets_in_history": 1}}
        ground_truth = {"expected": {"secrets_in_history": 3}}

        results = run_detection_checks(analysis, ground_truth)
        sd3 = next(r for r in results if r.check_id == "SD-3")

        assert sd3.passed is False

    def test_sd4_clean_repo_zero_secrets(self) -> None:
        """SD-4: Clean repo with zero secrets passes."""
        analysis = {"results": {"total_secrets": 0}}
        ground_truth = {"expected": {"total_secrets": 0}}

        results = run_detection_checks(analysis, ground_truth)
        sd4 = next(r for r in results if r.check_id == "SD-4")

        assert sd4.passed is True

    def test_sd4_clean_repo_has_secrets_fails(self) -> None:
        """SD-4: Clean repo with secrets fails."""
        analysis = {"results": {"total_secrets": 2}}
        ground_truth = {"expected": {"total_secrets": 0}}

        results = run_detection_checks(analysis, ground_truth)
        sd4 = next(r for r in results if r.check_id == "SD-4")

        assert sd4.passed is False

    def test_sd4_repo_expected_to_have_secrets_na(self) -> None:
        """SD-4: Repo expected to have secrets is N/A."""
        analysis = {"results": {"total_secrets": 3}}
        ground_truth = {"expected": {"total_secrets": 3}}

        results = run_detection_checks(analysis, ground_truth)
        sd4 = next(r for r in results if r.check_id == "SD-4")

        assert sd4.passed is True
        assert "N/A" in sd4.message

    def test_sd5_entropy_values_valid(self) -> None:
        """SD-5: All entropy values in valid range passes."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "line_number": 1, "entropy": 3.5},
                    {"file_path": "config.py", "line_number": 5, "entropy": 5.2},
                    {"file_path": "secrets.txt", "line_number": 10, "entropy": 0.0},
                    {"file_path": "keys.json", "line_number": 1, "entropy": 8.0},
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd5 = next(r for r in results if r.check_id == "SD-5")

        assert sd5.passed is True
        assert "All entropy values valid" in sd5.message

    def test_sd5_entropy_negative_fails(self) -> None:
        """SD-5: Negative entropy value fails."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "line_number": 1, "entropy": -1.0},
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd5 = next(r for r in results if r.check_id == "SD-5")

        assert sd5.passed is False
        assert "Invalid entropy" in sd5.message

    def test_sd5_entropy_above_8_fails(self) -> None:
        """SD-5: Entropy above 8 bits fails."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "line_number": 1, "entropy": 9.5},
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd5 = next(r for r in results if r.check_id == "SD-5")

        assert sd5.passed is False

    def test_sd5_empty_findings_passes(self) -> None:
        """SD-5: Empty findings passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd5 = next(r for r in results if r.check_id == "SD-5")

        assert sd5.passed is True

    def test_sd6_all_secrets_masked(self) -> None:
        """SD-6: All secrets have masked preview passes."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "secret_preview": "ghp_1234*******"},
                    {"file_path": "config.py", "secret_preview": "sk_live_****"},
                    {"file_path": "short.txt", "secret_preview": "abc"},  # short is ok
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd6 = next(r for r in results if r.check_id == "SD-6")

        assert sd6.passed is True

    def test_sd6_unmasked_secret_fails(self) -> None:
        """SD-6: Unmasked long secret fails."""
        analysis = {
            "results": {
                "findings": [
                    {"file_path": ".env", "secret_preview": "ghp_1234567890abcdefghij"},  # no asterisks, > 8 chars
                ]
            }
        }
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd6 = next(r for r in results if r.check_id == "SD-6")

        assert sd6.passed is False
        assert "Unmasked" in sd6.message

    def test_sd6_empty_findings_passes(self) -> None:
        """SD-6: Empty findings passes."""
        analysis = {"results": {"findings": []}}
        ground_truth = {"expected": {}}

        results = run_detection_checks(analysis, ground_truth)
        sd6 = next(r for r in results if r.check_id == "SD-6")

        assert sd6.passed is True

    def test_all_checks_return_6_results(self) -> None:
        """All 6 detection checks should be returned."""
        analysis = {
            "results": {
                "total_secrets": 0,
                "secrets_by_rule": {},
                "secrets_in_history": 0,
                "findings": [],
            }
        }
        ground_truth = {"expected": {"total_secrets": 0}}

        results = run_detection_checks(analysis, ground_truth)

        assert len(results) == 6
        check_ids = {r.check_id for r in results}
        expected_ids = {f"SD-{i}" for i in range(1, 7)}
        assert check_ids == expected_ids

    def test_handles_flat_analysis_format(self) -> None:
        """Should handle flat analysis format (no results wrapper)."""
        analysis = {
            "total_secrets": 2,
            "secrets_by_rule": {"github-pat": 2},
            "secrets_in_history": 0,
            "findings": [],
        }
        ground_truth = {"expected": {"total_secrets": 2, "rule_ids": ["github-pat"]}}

        results = run_detection_checks(analysis, ground_truth)
        sd1 = next(r for r in results if r.check_id == "SD-1")
        sd2 = next(r for r in results if r.check_id == "SD-2")

        assert sd1.passed is True
        assert sd2.passed is True
