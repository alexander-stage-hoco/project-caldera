"""Unit tests for accuracy checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.accuracy import run_accuracy_checks
from checks import CheckCategory


class TestAccuracyChecks:
    """Tests for run_accuracy_checks function."""

    def test_ac1_sql_injection_detection(self) -> None:
        """AC-1: SQL injection detection with ground truth."""
        analysis = {
            "summary": {"issues_by_category": {"sql_injection": 3}},
            "files": [
                {"path": "test.cs", "issues": [
                    {"dd_category": "sql_injection"},
                    {"dd_category": "sql_injection"},
                    {"dd_category": "sql_injection"},
                ]}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac1 = next((r for r in results if r.check_id == "AC-1"), None)
        assert ac1 is not None
        assert ac1.category == CheckCategory.ACCURACY

    def test_ac2_hardcoded_secrets_detection(self) -> None:
        """AC-2: Hardcoded secrets detection."""
        analysis = {
            "summary": {"issues_by_category": {"hardcoded_secret": 2}},
            "files": [
                {"path": "config.py", "issues": [
                    {"dd_category": "hardcoded_secret"},
                    {"dd_category": "hardcoded_secret"},
                ]}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac2 = next((r for r in results if r.check_id == "AC-2"), None)
        assert ac2 is not None
        assert ac2.category == CheckCategory.ACCURACY

    def test_ac3_insecure_crypto_detection(self) -> None:
        """AC-3: Insecure crypto detection - validates check runs and returns result."""
        analysis = {
            "summary": {"issues_by_category": {"insecure_crypto": 10}},
            "files": [
                {"path": "InsecureCrypto.cs", "issues": [
                    {"dd_category": "insecure_crypto"} for _ in range(10)
                ]}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))

        ac3 = next((r for r in results if r.check_id == "AC-3"), None)
        assert ac3 is not None
        assert ac3.category == CheckCategory.ACCURACY
        # Score should be positive with 10 findings
        assert ac3.score >= 0.5

    def test_ac4_path_traversal_detection(self) -> None:
        """AC-4: Path traversal detection."""
        analysis = {
            "summary": {"issues_by_category": {"path_traversal": 1}},
            "files": [{"path": "test.py", "issues": [{"dd_category": "path_traversal"}]}]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac4 = next((r for r in results if r.check_id == "AC-4"), None)
        assert ac4 is not None

    def test_ac5_xss_detection(self) -> None:
        """AC-5: XSS detection."""
        analysis = {
            "summary": {"issues_by_category": {"xss": 2}},
            "files": [{"path": "web.js", "issues": [{"dd_category": "xss"}, {"dd_category": "xss"}]}]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac5 = next((r for r in results if r.check_id == "AC-5"), None)
        assert ac5 is not None

    def test_ac6_deserialization_detection(self) -> None:
        """AC-6: Deserialization detection - validates check runs and returns result."""
        analysis = {
            "summary": {"issues_by_category": {"deserialization": 2}},
            "files": [
                {"path": "Deserialization.cs", "issue_count": 2, "issues": [
                    {"dd_category": "deserialization"},
                    {"dd_category": "deserialization"},
                ]}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))

        ac6 = next((r for r in results if r.check_id == "AC-6"), None)
        assert ac6 is not None
        assert ac6.category == CheckCategory.ACCURACY
        # Score should be positive with 2 findings matching ground truth
        assert ac6.score >= 0.5

    def test_ac7_false_positive_rate(self) -> None:
        """AC-7: False positive rate check."""
        analysis = {
            "summary": {"total_issues": 10},
            "files": [
                {"path": "SafeCode.cs", "issue_count": 0, "issues": []},
                {"path": "InsecureCrypto.cs", "issue_count": 10, "issues": [{"dd_category": "insecure_crypto"}] * 10}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac7 = next((r for r in results if r.check_id == "AC-7"), None)
        assert ac7 is not None
        assert ac7.score >= 0.7  # Should have good FP rate with no issues in SafeCode.cs

    def test_ac8_overall_precision_recall(self) -> None:
        """AC-8: Overall precision/recall check."""
        analysis = {
            "summary": {"total_issues": 12},
            "files": [
                {"path": "InsecureCrypto.cs", "issue_count": 10, "issues": [{"dd_category": "insecure_crypto"}] * 10},
                {"path": "Deserialization.cs", "issue_count": 2, "issues": [{"dd_category": "deserialization"}] * 2}
            ]
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        ac8 = next((r for r in results if r.check_id == "AC-8"), None)
        assert ac8 is not None
        assert "precision" in ac8.evidence or "Precision" in ac8.message.lower()

    def test_all_accuracy_checks_returned(self) -> None:
        """All 8 accuracy checks should be returned."""
        analysis = {
            "summary": {"total_issues": 0, "issues_by_category": {}},
            "files": []
        }
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        assert len(results) == 8
        check_ids = {r.check_id for r in results}
        expected_ids = {f"AC-{i}" for i in range(1, 9)}
        assert check_ids == expected_ids

    def test_empty_analysis_handles_gracefully(self) -> None:
        """Empty analysis should not raise errors."""
        analysis = {}
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        assert len(results) == 8
        for r in results:
            assert r.category == CheckCategory.ACCURACY

    def test_check_results_have_required_fields(self) -> None:
        """All check results should have required fields."""
        analysis = {"summary": {}, "files": []}
        results = run_accuracy_checks(analysis, str(Path(__file__).parent.parent.parent / "evaluation/ground-truth"))
        
        for result in results:
            assert result.check_id is not None
            assert result.name is not None
            assert result.category is not None
            assert isinstance(result.passed, bool)
            assert 0.0 <= result.score <= 1.0
            assert result.message is not None
