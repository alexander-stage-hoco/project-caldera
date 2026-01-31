"""
Tests for evaluation orchestration and scoring.

Tests cover:
- All evaluation check execution
- Category score computation (4 categories)
- Weighted overall score calculation
- Decision thresholds (STRONG_PASS/PASS/WEAK_PASS/FAIL)
- Scorecard JSON generation
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from evaluate import (
    compute_category_scores,
    compute_overall_score,
    determine_decision,
    generate_scorecard_json,
    CATEGORY_WEIGHTS,
)
from checks import CheckResult, EvaluationReport


class TestCategoryScoreComputation:
    """Test category-level score computation."""

    def test_compute_category_scores_single_category(self):
        """Compute scores for a single category."""
        checks = [
            CheckResult("AC-1", "Test 1", "accuracy", True, 1.0, 0.8, 0.9, "Pass"),
            CheckResult("AC-2", "Test 2", "accuracy", False, 0.6, 0.8, 0.6, "Fail"),
            CheckResult("AC-3", "Test 3", "accuracy", True, 1.0, 0.8, 1.0, "Pass"),
        ]

        scores = compute_category_scores(checks)

        assert "accuracy" in scores
        assert scores["accuracy"]["checks_total"] == 3
        assert scores["accuracy"]["checks_passed"] == 2
        assert scores["accuracy"]["score"] == pytest.approx(2 / 3)

    def test_compute_category_scores_multiple_categories(self):
        """Compute scores across multiple categories."""
        checks = [
            CheckResult("AC-1", "Accuracy 1", "accuracy", True, 1.0, 0.8, 0.9, "Pass"),
            CheckResult("CV-1", "Coverage 1", "coverage", True, 1.0, 0.8, 0.85, "Pass"),
            CheckResult("CV-2", "Coverage 2", "coverage", False, 0.5, 0.8, 0.5, "Fail"),
            CheckResult("EC-1", "Edge Case 1", "edge_cases", True, 1.0, 0.8, 0.9, "Pass"),
            CheckResult("PF-1", "Performance 1", "performance", True, 1.0, 0.8, 0.95, "Pass"),
        ]

        scores = compute_category_scores(checks)

        assert len(scores) == 4
        assert scores["accuracy"]["checks_total"] == 1
        assert scores["accuracy"]["checks_passed"] == 1
        assert scores["coverage"]["checks_total"] == 2
        assert scores["coverage"]["checks_passed"] == 1
        assert scores["edge_cases"]["score"] == 1.0
        assert scores["performance"]["score"] == 1.0

    def test_compute_category_scores_applies_weights(self):
        """Verify category weights are applied correctly."""
        checks = [
            CheckResult("AC-1", "Accuracy", "accuracy", True, 1.0, 0.8, 1.0, "Pass"),
        ]

        scores = compute_category_scores(checks)

        expected_weight = CATEGORY_WEIGHTS["accuracy"]
        assert scores["accuracy"]["weight"] == expected_weight
        assert scores["accuracy"]["weighted_score"] == pytest.approx(1.0 * expected_weight)

    def test_compute_category_scores_empty_checks(self):
        """Handle empty check list."""
        scores = compute_category_scores([])

        assert scores == {}

    def test_compute_category_scores_all_passing(self):
        """All checks passing gives score of 1.0."""
        checks = [
            CheckResult("AC-1", "Test 1", "accuracy", True, 1.0, 0.8, 0.9, "Pass"),
            CheckResult("AC-2", "Test 2", "accuracy", True, 1.0, 0.8, 0.95, "Pass"),
        ]

        scores = compute_category_scores(checks)

        assert scores["accuracy"]["score"] == 1.0

    def test_compute_category_scores_all_failing(self):
        """All checks failing gives score of 0.0."""
        checks = [
            CheckResult("AC-1", "Test 1", "accuracy", False, 0.3, 0.8, 0.3, "Fail"),
            CheckResult("AC-2", "Test 2", "accuracy", False, 0.5, 0.8, 0.5, "Fail"),
        ]

        scores = compute_category_scores(checks)

        assert scores["accuracy"]["score"] == 0.0


class TestOverallScoreComputation:
    """Test overall weighted score computation."""

    def test_compute_overall_score_simple(self):
        """Compute overall score from category scores."""
        category_scores = {
            "accuracy": {"weighted_score": 0.32},     # 0.40 * 0.80
            "coverage": {"weighted_score": 0.20},     # 0.25 * 0.80
            "edge_cases": {"weighted_score": 0.16},   # 0.20 * 0.80
            "performance": {"weighted_score": 0.12},  # 0.15 * 0.80
        }

        overall = compute_overall_score(category_scores)

        assert overall == pytest.approx(0.80)

    def test_compute_overall_score_perfect(self):
        """Perfect scores in all categories."""
        category_scores = {
            "accuracy": {"weighted_score": 0.40},
            "coverage": {"weighted_score": 0.25},
            "edge_cases": {"weighted_score": 0.20},
            "performance": {"weighted_score": 0.15},
        }

        overall = compute_overall_score(category_scores)

        assert overall == pytest.approx(1.0)

    def test_compute_overall_score_zero(self):
        """Zero scores in all categories."""
        category_scores = {
            "accuracy": {"weighted_score": 0.0},
            "coverage": {"weighted_score": 0.0},
            "edge_cases": {"weighted_score": 0.0},
            "performance": {"weighted_score": 0.0},
        }

        overall = compute_overall_score(category_scores)

        assert overall == pytest.approx(0.0)

    def test_compute_overall_score_empty(self):
        """Empty category scores."""
        overall = compute_overall_score({})

        assert overall == 0.0


class TestDecisionDetermination:
    """Test decision threshold logic."""

    def test_determine_decision_strong_pass(self):
        """Score >= 0.80 with all categories >= 70% is STRONG_PASS."""
        category_scores = {
            "accuracy": {"score": 0.85},
            "coverage": {"score": 0.80},
            "edge_cases": {"score": 0.75},
            "performance": {"score": 0.90},
        }

        decision, reason = determine_decision(0.82, category_scores)

        assert decision == "STRONG_PASS"
        assert "0.82" in reason or "0.820" in reason

    def test_determine_decision_pass(self):
        """Score >= 0.70 and < 0.80 with all categories >= 70% is PASS."""
        category_scores = {
            "accuracy": {"score": 0.75},
            "coverage": {"score": 0.72},
            "edge_cases": {"score": 0.70},
            "performance": {"score": 0.80},
        }

        decision, reason = determine_decision(0.74, category_scores)

        assert decision == "PASS"
        assert "0.74" in reason or "0.740" in reason

    def test_determine_decision_weak_pass(self):
        """Score >= 0.60 and < 0.70 with all categories >= 70% is WEAK_PASS."""
        category_scores = {
            "accuracy": {"score": 0.70},
            "coverage": {"score": 0.70},
            "edge_cases": {"score": 0.70},
            "performance": {"score": 0.70},
        }

        decision, reason = determine_decision(0.65, category_scores)

        assert decision == "WEAK_PASS"
        assert "0.65" in reason or "0.650" in reason

    def test_determine_decision_fail_low_score(self):
        """Score < 0.60 is FAIL."""
        category_scores = {
            "accuracy": {"score": 0.70},
            "coverage": {"score": 0.70},
            "edge_cases": {"score": 0.70},
            "performance": {"score": 0.70},
        }

        decision, reason = determine_decision(0.55, category_scores)

        assert decision == "FAIL"
        assert "below" in reason.lower()

    def test_determine_decision_fail_category_minimum(self):
        """Any category below 70% is FAIL regardless of overall score."""
        category_scores = {
            "accuracy": {"score": 0.90},
            "coverage": {"score": 0.65},  # Below 70%
            "edge_cases": {"score": 0.85},
            "performance": {"score": 0.80},
        }

        decision, reason = determine_decision(0.85, category_scores)

        assert decision == "FAIL"
        assert "coverage" in reason.lower()
        assert "65" in reason

    def test_determine_decision_fail_multiple_categories(self):
        """Multiple categories below minimum are all listed."""
        category_scores = {
            "accuracy": {"score": 0.60},   # Below 70%
            "coverage": {"score": 0.50},   # Below 70%
            "edge_cases": {"score": 0.85},
            "performance": {"score": 0.80},
        }

        decision, reason = determine_decision(0.70, category_scores)

        assert decision == "FAIL"
        assert "accuracy" in reason.lower()
        assert "coverage" in reason.lower()

    def test_determine_decision_boundary_70(self):
        """Exactly 70% category score passes minimum."""
        category_scores = {
            "accuracy": {"score": 0.70},
            "coverage": {"score": 0.70},
            "edge_cases": {"score": 0.70},
            "performance": {"score": 0.70},
        }

        decision, _ = determine_decision(0.70, category_scores)

        assert decision == "PASS"


class TestScorecardGeneration:
    """Test scorecard JSON generation."""

    def test_generate_scorecard_structure(self):
        """Verify scorecard has required structure."""
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={
                "total_checks": 10,
                "passed": 8,
                "failed": 2,
                "overall_score": 0.78
            },
            category_scores={
                "accuracy": {"weight": 0.4, "checks_total": 4, "checks_passed": 3, "score": 0.75, "weighted_score": 0.30},
                "coverage": {"weight": 0.25, "checks_total": 3, "checks_passed": 3, "score": 1.0, "weighted_score": 0.25},
            },
            checks=[
                {"check_id": "AC-1", "name": "Test", "category": "accuracy", "passed": True, "score": 0.9, "message": "OK"},
            ],
            decision="PASS",
            decision_reason="Score meets threshold"
        )

        scorecard = generate_scorecard_json(report)

        assert scorecard["tool"] == "roslyn-analyzers"
        assert "summary" in scorecard
        assert "dimensions" in scorecard
        assert "thresholds" in scorecard
        assert "critical_failures" in scorecard

    def test_generate_scorecard_summary(self):
        """Verify scorecard summary section."""
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={
                "total_checks": 10,
                "passed": 8,
                "failed": 2,
                "overall_score": 0.78
            },
            category_scores={},
            checks=[],
            decision="PASS",
            decision_reason="Test"
        )

        scorecard = generate_scorecard_json(report)

        summary = scorecard["summary"]
        assert summary["total_checks"] == 10
        assert summary["passed"] == 8
        assert summary["failed"] == 2
        assert summary["decision"] == "PASS"
        assert summary["score_percent"] == pytest.approx(78.0)
        # Normalized to 5-point scale
        assert summary["normalized_score"] == pytest.approx(3.90)

    def test_generate_scorecard_dimensions(self):
        """Verify scorecard dimensions section."""
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={"total_checks": 4, "passed": 3, "failed": 1, "overall_score": 0.75},
            category_scores={
                "accuracy": {
                    "weight": 0.4,
                    "checks_total": 2,
                    "checks_passed": 2,
                    "score": 1.0,
                    "weighted_score": 0.4
                },
                "coverage": {
                    "weight": 0.25,
                    "checks_total": 2,
                    "checks_passed": 1,
                    "score": 0.5,
                    "weighted_score": 0.125
                },
            },
            checks=[
                {"check_id": "AC-1", "name": "Test 1", "category": "accuracy", "passed": True, "score": 1.0, "message": "OK"},
                {"check_id": "AC-2", "name": "Test 2", "category": "accuracy", "passed": True, "score": 0.9, "message": "OK"},
                {"check_id": "CV-1", "name": "Test 3", "category": "coverage", "passed": True, "score": 0.8, "message": "OK"},
                {"check_id": "CV-2", "name": "Test 4", "category": "coverage", "passed": False, "score": 0.2, "message": "Fail"},
            ],
            decision="PASS",
            decision_reason="Test"
        )

        scorecard = generate_scorecard_json(report)

        dims = scorecard["dimensions"]
        assert len(dims) == 2

        accuracy_dim = next(d for d in dims if "accuracy" in d["name"].lower())
        assert accuracy_dim["total_checks"] == 2
        assert accuracy_dim["passed"] == 2
        assert accuracy_dim["failed"] == 0
        assert accuracy_dim["score"] == pytest.approx(5.0)  # 1.0 * 5.0
        assert len(accuracy_dim["checks"]) == 2

    def test_generate_scorecard_thresholds(self):
        """Verify scorecard includes threshold documentation."""
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={"total_checks": 0, "passed": 0, "failed": 0, "overall_score": 0.0},
            category_scores={},
            checks=[],
            decision="FAIL",
            decision_reason="Test"
        )

        scorecard = generate_scorecard_json(report)

        thresholds = scorecard["thresholds"]
        assert "STRONG_PASS" in thresholds
        assert "PASS" in thresholds
        assert "WEAK_PASS" in thresholds
        assert "FAIL" in thresholds

    def test_generate_scorecard_critical_failures(self):
        """Verify critical failures are identified."""
        report = EvaluationReport(
            evaluation_id="test-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={"total_checks": 2, "passed": 0, "failed": 2, "overall_score": 0.0},
            category_scores={},
            checks=[
                {"check_id": "CRITICAL-1", "name": "Critical Test", "category": "accuracy", "passed": False, "score": 0.0, "message": "Critical failure"},
                {"check_id": "AC-1", "name": "Normal Test", "category": "accuracy", "passed": False, "score": 0.0, "message": "Normal failure"},
            ],
            decision="FAIL",
            decision_reason="Test"
        )

        scorecard = generate_scorecard_json(report)

        # Only "critical" in check_id should be in critical_failures
        critical = scorecard["critical_failures"]
        assert len(critical) == 1
        assert critical[0]["check_id"] == "CRITICAL-1"


class TestCategoryWeights:
    """Test category weight configuration."""

    def test_category_weights_sum_to_one(self):
        """Category weights should sum to 1.0."""
        total = sum(CATEGORY_WEIGHTS.values())
        assert total == pytest.approx(1.0)

    def test_category_weights_expected_categories(self):
        """Verify expected categories are present."""
        expected = ["accuracy", "coverage", "edge_cases", "performance"]
        for cat in expected:
            assert cat in CATEGORY_WEIGHTS

    def test_category_weights_accuracy_highest(self):
        """Accuracy should have the highest weight."""
        accuracy_weight = CATEGORY_WEIGHTS["accuracy"]
        for cat, weight in CATEGORY_WEIGHTS.items():
            if cat != "accuracy":
                assert accuracy_weight >= weight, f"Accuracy should have highest weight, but {cat} is higher"


class TestCheckResultDataclass:
    """Test CheckResult dataclass behavior."""

    def test_check_result_creation(self):
        """Create CheckResult with all fields."""
        cr = CheckResult(
            check_id="AC-1",
            name="Test Check",
            category="accuracy",
            passed=True,
            score=0.95,
            threshold=0.80,
            actual_value=0.95,
            message="All checks passed"
        )

        assert cr.check_id == "AC-1"
        assert cr.name == "Test Check"
        assert cr.category == "accuracy"
        assert cr.passed is True
        assert cr.score == 0.95
        assert cr.threshold == 0.80
        assert cr.actual_value == 0.95
        assert cr.message == "All checks passed"
        assert cr.evidence == {}

    def test_check_result_with_evidence(self):
        """Create CheckResult with evidence dict."""
        cr = CheckResult(
            check_id="AC-1",
            name="Test Check",
            category="accuracy",
            passed=False,
            score=0.60,
            threshold=0.80,
            actual_value=0.60,
            message="Below threshold",
            evidence={"expected": 10, "actual": 6, "files": ["a.cs", "b.cs"]}
        )

        assert cr.evidence["expected"] == 10
        assert cr.evidence["actual"] == 6
        assert len(cr.evidence["files"]) == 2


class TestEvaluationReportDataclass:
    """Test EvaluationReport dataclass behavior."""

    def test_evaluation_report_creation(self):
        """Create EvaluationReport with all fields."""
        report = EvaluationReport(
            evaluation_id="eval-001",
            timestamp="2026-01-22T10:00:00Z",
            analysis_file="/path/to/analysis.json",
            summary={"total_checks": 10, "passed": 8, "failed": 2},
            category_scores={"accuracy": {"score": 0.80}},
            checks=[],
            decision="PASS",
            decision_reason="Score meets threshold"
        )

        assert report.evaluation_id == "eval-001"
        assert report.timestamp == "2026-01-22T10:00:00Z"
        assert report.analysis_file == "/path/to/analysis.json"
        assert report.summary["total_checks"] == 10
        assert report.decision == "PASS"
