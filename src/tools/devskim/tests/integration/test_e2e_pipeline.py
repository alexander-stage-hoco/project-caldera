"""End-to-end integration tests for DevSkim analysis pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_DIR = Path(__file__).parent.parent.parent
EVAL_REPOS = TOOL_DIR / "eval-repos" / "synthetic"

sys.path.insert(0, str(TOOL_DIR / "scripts"))


class TestE2EPipeline:
    """End-to-end tests for the analysis pipeline."""

    @pytest.fixture
    def synthetic_repo_path(self) -> Path:
        """Get path to synthetic test repo."""
        if not EVAL_REPOS.exists():
            pytest.skip("Synthetic eval repos not found")
        # Use csharp synthetic repo
        csharp_repo = EVAL_REPOS / "csharp"
        if not csharp_repo.exists():
            pytest.skip("C# synthetic repo not found")
        return csharp_repo

    @pytest.mark.integration
    def test_analyze_script_exists(self) -> None:
        """Analyze script should exist."""
        analyze_script = TOOL_DIR / "scripts" / "analyze.py"
        assert analyze_script.exists(), f"analyze.py not found at {analyze_script}"

    @pytest.mark.integration
    def test_evaluate_script_exists(self) -> None:
        """Evaluate script should exist."""
        evaluate_script = TOOL_DIR / "scripts" / "evaluate.py"
        assert evaluate_script.exists(), f"evaluate.py not found at {evaluate_script}"

    @pytest.mark.integration
    def test_makefile_exists(self) -> None:
        """Makefile should exist."""
        makefile = TOOL_DIR / "Makefile"
        assert makefile.exists(), f"Makefile not found at {makefile}"

    @pytest.mark.integration
    def test_makefile_has_required_targets(self) -> None:
        """Makefile should have required targets."""
        makefile = TOOL_DIR / "Makefile"
        if not makefile.exists():
            pytest.skip("Makefile not found")
        
        content = makefile.read_text()
        required_targets = ["setup", "analyze", "evaluate", "clean", "test"]
        for target in required_targets:
            assert f"{target}:" in content, f"Missing target: {target}"

    @pytest.mark.integration
    def test_synthetic_repo_has_test_files(self, synthetic_repo_path: Path) -> None:
        """Synthetic repo should have test files."""
        cs_files = list(synthetic_repo_path.glob("*.cs"))
        assert len(cs_files) > 0, "No C# files in synthetic repo"

    @pytest.mark.integration
    def test_synthetic_repo_has_vulnerable_files(self, synthetic_repo_path: Path) -> None:
        """Synthetic repo should have files with known vulnerabilities."""
        expected_files = ["InsecureCrypto.cs", "Deserialization.cs"]
        for file_name in expected_files:
            file_path = synthetic_repo_path / file_name
            assert file_path.exists(), f"Missing vulnerable test file: {file_name}"


class TestEvaluationFramework:
    """Tests for the evaluation framework."""

    def test_checks_module_imports(self) -> None:
        """Checks module should import correctly."""
        from checks import (
            CheckResult,
            CheckCategory,
            EvaluationReport,
            run_accuracy_checks,
            run_coverage_checks,
            run_edge_case_checks,
            run_performance_checks,
            run_output_quality_checks,
            run_integration_fit_checks,
        )
        
        assert CheckResult is not None
        assert CheckCategory is not None
        assert EvaluationReport is not None

    def test_evaluation_report_properties(self) -> None:
        """EvaluationReport should have required properties."""
        from checks import CheckResult, CheckCategory, EvaluationReport
        
        checks = [
            CheckResult(
                check_id="AC-1",
                name="Test check",
                category=CheckCategory.ACCURACY,
                passed=True,
                score=0.9,
                message="Test passed",
                evidence={}
            )
        ]
        
        report = EvaluationReport(
            timestamp="2026-01-23T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="evaluation/ground-truth",
            checks=checks
        )
        
        assert report.passed == 1
        assert report.failed == 0
        assert report.total == 1
        assert report.score == 0.9
        assert "accuracy" in report.score_by_category

    def test_check_result_to_dict(self) -> None:
        """CheckResult should serialize to dict."""
        from checks import CheckResult, CheckCategory
        
        result = CheckResult(
            check_id="AC-1",
            name="Test check",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.9,
            message="Test passed",
            evidence={"key": "value"}
        )
        
        d = result.to_dict()
        assert d["check_id"] == "AC-1"
        assert d["passed"] is True
        assert d["score"] == 0.9
        assert d["category"] == "accuracy"

    def test_evaluation_report_decision(self) -> None:
        """EvaluationReport decision should be correct."""
        from checks import CheckResult, CheckCategory, EvaluationReport
        
        # High score = STRONG_PASS
        high_checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, True, 0.9, "Pass", {})
        ]
        high_report = EvaluationReport("", "", "", high_checks)
        assert high_report.decision == "STRONG_PASS"
        
        # Low score = FAIL
        low_checks = [
            CheckResult("AC-1", "Test", CheckCategory.ACCURACY, False, 0.3, "Fail", {})
        ]
        low_report = EvaluationReport("", "", "", low_checks)
        assert low_report.decision == "FAIL"
