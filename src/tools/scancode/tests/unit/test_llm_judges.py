"""Unit tests for scancode LLM judges."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from evaluation.llm.judges import (
    ActionabilityJudge,
    LicenseAccuracyJudge,
    LicenseCoverageJudge,
    RiskClassificationJudge,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _seed_analysis_and_ground_truth(base: Path) -> None:
    analysis = {
        "schema_version": "1.0.0",
        "generated_at": "2025-01-01T00:00:00Z",
        "repo_name": "mit-only",
        "repo_path": "eval-repos/synthetic/mit-only",
        "results": {
            "tool": "license-analyzer",
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 1},
            "overall_risk": "low",
        },
    }
    ground_truth = {
        "licenses_found": ["MIT"],
        "overall_risk": "low",
    }

    _write_json(base / "outputs" / "mit-only.json", analysis)
    _write_json(base / "evaluation" / "ground-truth" / "mit-only.json", ground_truth)


def test_accuracy_judge_collects_evidence(tmp_path: Path) -> None:
    _seed_analysis_and_ground_truth(tmp_path)
    judge = LicenseAccuracyJudge(working_dir=tmp_path)
    evidence = judge.collect_evidence()

    assert "analysis_results" in evidence
    assert "ground_truth" in evidence
    assert evidence["analysis_results"]["mit-only"]["results"]["licenses_found"] == ["MIT"]

    passed, failures = judge.run_ground_truth_assertions()
    assert passed
    assert failures == []


def test_coverage_judge_collects_evidence(tmp_path: Path) -> None:
    _seed_analysis_and_ground_truth(tmp_path)
    judge = LicenseCoverageJudge(working_dir=tmp_path)
    evidence = judge.collect_evidence()

    assert "analysis_results" in evidence
    assert "ground_truth" in evidence
    assert evidence["ground_truth"]["mit-only"]["overall_risk"] == "low"

    passed, failures = judge.run_ground_truth_assertions()
    assert passed
    assert failures == []


def test_actionability_judge_collects_evidence(tmp_path: Path) -> None:
    _seed_analysis_and_ground_truth(tmp_path)
    judge = ActionabilityJudge(working_dir=tmp_path)
    evidence = judge.collect_evidence()

    assert "analysis_results" in evidence
    assert evidence["analysis_results"]["mit-only"]["results"]["overall_risk"] == "low"

    passed, failures = judge.run_ground_truth_assertions()
    assert passed
    assert failures == []


def test_risk_classification_judge_collects_evidence(tmp_path: Path) -> None:
    # RiskClassificationJudge expects overall_risk in data or at top level
    analysis = {
        "schema_version": "1.0.0",
        "generated_at": "2025-01-01T00:00:00Z",
        "repo_name": "mit-only",
        "repo_path": "eval-repos/synthetic/mit-only",
        "overall_risk": "low",
        "results": {
            "tool": "license-analyzer",
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 1},
        },
    }
    ground_truth = {
        "licenses_found": ["MIT"],
        "overall_risk": "low",
    }
    _write_json(tmp_path / "outputs" / "mit-only.json", analysis)
    _write_json(tmp_path / "evaluation" / "ground-truth" / "mit-only.json", ground_truth)

    judge = RiskClassificationJudge(working_dir=tmp_path)
    evidence = judge.collect_evidence()

    assert "analysis_results" in evidence
    assert "ground_truth" in evidence
    assert evidence["analysis_results"]["mit-only"]["overall_risk"] == "low"

    passed, failures = judge.run_ground_truth_assertions()
    assert passed, f"Assertions failed: {failures}"
    assert failures == []


def test_risk_classification_judge_weight() -> None:
    """Verify RiskClassificationJudge has correct weight."""
    judge = RiskClassificationJudge()
    assert judge.weight == 0.25


def test_all_judge_weights_sum_to_one() -> None:
    """Verify all judge weights sum to 1.0."""
    judges = [
        LicenseAccuracyJudge(),
        LicenseCoverageJudge(),
        ActionabilityJudge(),
        RiskClassificationJudge(),
    ]
    total_weight = sum(j.weight for j in judges)
    assert abs(total_weight - 1.0) < 0.001, f"Weights sum to {total_weight}, expected 1.0"
