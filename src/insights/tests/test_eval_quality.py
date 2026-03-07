"""Tests for the evaluation quality checker."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from insights.evidence.entities import (
    EvaluationScore,
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)
from insights.evidence.eval_quality import (
    EvalQualityFlag,
    EvalQualityReport,
    check_evaluation_quality,
    _check_coverage,
    _check_uniformity,
    _check_reasoning_presence,
    _check_score_severity_contradictions,
    _check_confidence_calibration,
    _check_avg_score_range,
)


def _make_evidence(eid: str = "E-CCN-001", category: str = "complexity") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        evidence_type="metric_threshold",
        category=category,
        location="src/foo.py",
        excerpt="complex function",
        observation="High complexity",
        why_it_matters="Hard to maintain",
        tool_source="lizard",
        run_pk=1,
    )


def _make_claim(cid: str = "CLM-CCN-001", category: str = "complexity") -> TechnicalClaim:
    return TechnicalClaim(
        claim_id=cid,
        category=category,
        statement="High complexity detected",
        evidence_ids=("E-CCN-001",),
        implication="Maintenance risk",
        confidence="high",
        triggered_by="complexity_hotspot",
    )


def _make_risk(
    rid: str = "RISK-001", severity: str = "high",
) -> ExecutionRisk:
    return ExecutionRisk(
        risk_id=rid,
        description="Complexity risk",
        technical_cause="High CCN",
        claim_ids=("CLM-CCN-001",),
        manifests_in=("src/foo.py",),
        triggered_by="complexity_cluster",
        severity=severity,
    )


def _make_score(
    entity_id: str = "CLM-CCN-001",
    entity_type: str = "claim",
    dimension: str = "validity",
    score: int = 4,
    confidence: float = 0.8,
    reasoning: str = "Well supported",
) -> EvaluationScore:
    return EvaluationScore(
        entity_id=entity_id,
        entity_type=entity_type,
        dimension=dimension,
        score=score,
        confidence=confidence,
        reasoning=reasoning,
    )


class TestCoverage(unittest.TestCase):
    def test_good_coverage(self):
        registry = EvidenceRegistry(
            evidence=[_make_evidence()],
            claims=[_make_claim()],
            risks=[_make_risk()],
        )
        # 1 category + 1 claim + 1 risk = 3 expected, 3 scores
        scores = [
            _make_score("CAT-COMPLEXITY", "evidence", "quality"),
            _make_score("CLM-CCN-001", "claim", "validity"),
            _make_score("RISK-001", "risk", "coherence"),
        ]
        flag = _check_coverage(scores, registry, 0.7)
        self.assertTrue(flag.passed)
        self.assertAlmostEqual(flag.metric, 1.0)

    def test_empty_scores_low_coverage(self):
        registry = EvidenceRegistry(
            evidence=[_make_evidence()],
            claims=[_make_claim()],
            risks=[_make_risk()],
        )
        flag = _check_coverage([], registry, 0.7)
        self.assertFalse(flag.passed)
        self.assertAlmostEqual(flag.metric, 0.0)

    def test_empty_registry_passes(self):
        registry = EvidenceRegistry()
        flag = _check_coverage([], registry, 0.7)
        self.assertTrue(flag.passed)
        self.assertAlmostEqual(flag.metric, 1.0)


class TestUniformity(unittest.TestCase):
    def test_all_same_score_flags(self):
        scores = [_make_score(score=4) for _ in range(10)]
        flag = _check_uniformity(scores, 0.8)
        self.assertFalse(flag.passed)
        self.assertAlmostEqual(flag.metric, 1.0)

    def test_diverse_scores_pass(self):
        scores = [
            _make_score(score=1), _make_score(score=2),
            _make_score(score=3), _make_score(score=4),
            _make_score(score=5),
        ]
        flag = _check_uniformity(scores, 0.8)
        self.assertTrue(flag.passed)
        self.assertAlmostEqual(flag.metric, 0.2)

    def test_empty_scores_pass(self):
        flag = _check_uniformity([], 0.8)
        self.assertTrue(flag.passed)


class TestReasoningPresence(unittest.TestCase):
    def test_all_have_reasoning(self):
        scores = [_make_score(reasoning="Good") for _ in range(5)]
        flag = _check_reasoning_presence(scores, 0.8)
        self.assertTrue(flag.passed)
        self.assertAlmostEqual(flag.metric, 1.0)

    def test_missing_reasoning_flags(self):
        scores = [
            _make_score(reasoning=None),
            _make_score(reasoning=""),
            _make_score(reasoning="   "),
            _make_score(reasoning="OK"),
        ]
        flag = _check_reasoning_presence(scores, 0.8)
        self.assertFalse(flag.passed)
        self.assertAlmostEqual(flag.metric, 0.25)


class TestScoreSeverityContradictions(unittest.TestCase):
    def test_critical_risk_score_5_flags(self):
        registry = EvidenceRegistry(
            risks=[_make_risk("RISK-001", severity="critical")],
        )
        registry.add_evaluation(
            _make_score("RISK-001", "risk", "coherence", score=5),
        )
        flag = _check_score_severity_contradictions(registry, 0)
        self.assertFalse(flag.passed)
        self.assertEqual(flag.metric, 1.0)

    def test_low_risk_score_1_flags(self):
        registry = EvidenceRegistry(
            risks=[_make_risk("RISK-001", severity="low")],
        )
        registry.add_evaluation(
            _make_score("RISK-001", "risk", "coherence", score=1),
        )
        flag = _check_score_severity_contradictions(registry, 0)
        self.assertFalse(flag.passed)

    def test_no_contradiction(self):
        registry = EvidenceRegistry(
            risks=[_make_risk("RISK-001", severity="high")],
        )
        registry.add_evaluation(
            _make_score("RISK-001", "risk", "coherence", score=3),
        )
        flag = _check_score_severity_contradictions(registry, 0)
        self.assertTrue(flag.passed)
        self.assertEqual(flag.metric, 0.0)


class TestConfidenceCalibration(unittest.TestCase):
    def test_extreme_scores_well_calibrated(self):
        scores = [
            _make_score(score=5, confidence=0.9),
            _make_score(score=1, confidence=0.8),
        ]
        flag = _check_confidence_calibration(scores, 0.6)
        self.assertTrue(flag.passed)

    def test_extreme_scores_poorly_calibrated(self):
        scores = [
            _make_score(score=5, confidence=0.3),
            _make_score(score=1, confidence=0.2),
            _make_score(score=5, confidence=0.4),
        ]
        flag = _check_confidence_calibration(scores, 0.6)
        self.assertFalse(flag.passed)

    def test_no_extreme_scores_passes(self):
        scores = [_make_score(score=3, confidence=0.5)]
        flag = _check_confidence_calibration(scores, 0.6)
        self.assertTrue(flag.passed)


class TestAvgScoreRange(unittest.TestCase):
    def test_normal_range(self):
        scores = [_make_score(score=3), _make_score(score=4)]
        flag = _check_avg_score_range(scores, 2.0, 4.5)
        self.assertTrue(flag.passed)
        self.assertAlmostEqual(flag.metric, 3.5)

    def test_too_generous(self):
        scores = [_make_score(score=5) for _ in range(10)]
        flag = _check_avg_score_range(scores, 2.0, 4.5)
        self.assertFalse(flag.passed)
        self.assertAlmostEqual(flag.metric, 5.0)

    def test_too_harsh(self):
        scores = [_make_score(score=1) for _ in range(10)]
        flag = _check_avg_score_range(scores, 2.0, 4.5)
        self.assertFalse(flag.passed)
        self.assertAlmostEqual(flag.metric, 1.0)


class TestCheckEvaluationQuality(unittest.TestCase):
    def test_perfect_scores_pass_all(self):
        registry = EvidenceRegistry(
            evidence=[_make_evidence()],
            claims=[_make_claim()],
            risks=[_make_risk()],
        )
        scores = [
            _make_score("CAT-COMPLEXITY", "evidence", "quality", score=4, confidence=0.8, reasoning="Good evidence"),
            _make_score("CLM-CCN-001", "claim", "validity", score=3, confidence=0.7, reasoning="Valid claim"),
            _make_score("RISK-001", "risk", "coherence", score=3, confidence=0.7, reasoning="Coherent risk"),
        ]
        for s in scores:
            registry.add_evaluation(s)

        report = check_evaluation_quality(scores, registry)
        self.assertTrue(report.passed)
        self.assertEqual(len(report.flags), 6)
        self.assertTrue(all(f.passed for f in report.flags))

    def test_empty_scores_triggers_coverage_flag(self):
        registry = EvidenceRegistry(
            evidence=[_make_evidence()],
            claims=[_make_claim()],
            risks=[_make_risk()],
        )
        report = check_evaluation_quality([], registry)
        self.assertFalse(report.passed)
        coverage_flag = next(f for f in report.flags if f.check == "coverage")
        self.assertFalse(coverage_flag.passed)

    def test_all_same_score_triggers_uniformity(self):
        registry = EvidenceRegistry(
            evidence=[
                _make_evidence("E-CCN-001", "complexity"),
                _make_evidence("E-SEC-001", "security"),
            ],
            claims=[_make_claim("CLM-CCN-001"), _make_claim("CLM-CCN-002")],
            risks=[_make_risk("RISK-001"), _make_risk("RISK-002")],
        )
        # All scores = 4 (6 scores, all same value = 100% uniformity)
        scores = [
            _make_score("CAT-COMPLEXITY", "evidence", "quality", score=4, reasoning="R"),
            _make_score("CAT-SECURITY", "evidence", "quality", score=4, reasoning="R"),
            _make_score("CLM-CCN-001", "claim", "validity", score=4, reasoning="R"),
            _make_score("CLM-CCN-002", "claim", "validity", score=4, reasoning="R"),
            _make_score("RISK-001", "risk", "coherence", score=4, reasoning="R"),
            _make_score("RISK-002", "risk", "coherence", score=4, reasoning="R"),
        ]
        report = check_evaluation_quality(scores, registry)
        uniformity_flag = next(f for f in report.flags if f.check == "uniformity")
        self.assertFalse(uniformity_flag.passed)

    def test_report_summary_keys(self):
        registry = EvidenceRegistry()
        report = check_evaluation_quality([], registry)
        expected_keys = {"coverage", "uniformity", "reasoning_presence", "contradictions", "confidence_calibration", "avg_score_range"}
        self.assertEqual(set(report.summary.keys()), expected_keys)

    def test_registry_eval_quality_integration(self):
        """verify eval_quality field works on EvidenceRegistry."""
        registry = EvidenceRegistry()
        self.assertIsNone(registry.eval_quality)

        report = check_evaluation_quality([], registry)
        registry.eval_quality = report
        self.assertIsNotNone(registry.eval_quality)
        self.assertTrue(registry.eval_quality.passed)

        vs = registry.validation_summary()
        self.assertIn("eval_quality_passed", vs)
        self.assertTrue(vs["eval_quality_passed"])


if __name__ == "__main__":
    unittest.main()
