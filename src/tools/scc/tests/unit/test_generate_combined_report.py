"""Tests for scripts/generate_combined_report.py - combined scorecard generation."""
from __future__ import annotations

import json

import pytest
from scripts.generate_combined_report import (
    load_latest_file,
    load_programmatic_results,
    load_llm_results,
    compute_combined_score,
    generate_combined_scorecard,
)


# ---------------------------------------------------------------------------
# Tests: load_latest_file
# ---------------------------------------------------------------------------

class TestLoadLatestFile:
    def test_returns_latest_matching(self, tmp_path):
        (tmp_path / "eval-001.json").write_text("{}")
        (tmp_path / "eval-002.json").write_text("{}")
        result = load_latest_file("eval-*.json", tmp_path)
        assert result is not None
        assert result.name == "eval-002.json"

    def test_returns_none_no_match(self, tmp_path):
        result = load_latest_file("eval-*.json", tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# Tests: load_programmatic_results
# ---------------------------------------------------------------------------

class TestLoadProgrammaticResults:
    def test_load_from_static_path(self, tmp_path):
        data = {
            "run_id": "test-run",
            "total_score": 4.2,
            "decision": "STRONG_PASS",
            "dimensions": [
                {"dimension": "output_quality", "checks_total": 8, "checks_passed": 7, "score": 4},
                {"dimension": "reliability", "checks_total": 5, "checks_passed": 5, "score": 5},
            ],
        }
        eval_path = tmp_path / "evaluation_report.json"
        eval_path.write_text(json.dumps(data))

        result = load_programmatic_results(None, tmp_path)
        assert result["run_id"] == "test-run"
        assert result["total_score"] == 4.2
        assert result["total_checks"] == 13
        assert result["passed_checks"] == 12

    def test_not_found(self, tmp_path):
        result = load_programmatic_results(None, tmp_path)
        assert "error" in result

    def test_explicit_file(self, tmp_path):
        data = {
            "run_id": "explicit",
            "total_score": 3.5,
            "decision": "PASS",
            "dimensions": [],
        }
        path = tmp_path / "custom.json"
        path.write_text(json.dumps(data))

        result = load_programmatic_results(path, tmp_path)
        assert result["run_id"] == "explicit"


# ---------------------------------------------------------------------------
# Tests: load_llm_results
# ---------------------------------------------------------------------------

class TestLoadLlmResults:
    def test_load_from_static_path(self, tmp_path):
        data = {
            "run_id": "llm-run",
            "total_score": 3.8,
            "average_confidence": 0.85,
            "decision": "PASS",
            "dimensions": [
                {"name": "Output Quality", "score": 4, "weight": 0.3, "confidence": 0.9},
            ],
        }
        (tmp_path / "llm_evaluation.json").write_text(json.dumps(data))

        result = load_llm_results(None, tmp_path)
        assert result["run_id"] == "llm-run"
        assert result["total_score"] == 3.8

    def test_not_found(self, tmp_path):
        result = load_llm_results(None, tmp_path)
        assert "error" in result


# ---------------------------------------------------------------------------
# Tests: compute_combined_score
# ---------------------------------------------------------------------------

class TestComputeCombinedScore:
    def test_perfect_scores(self):
        score, decision = compute_combined_score(5.0, 5.0)
        assert score == 5.0
        assert decision == "STRONG_PASS"

    def test_strong_pass(self):
        score, decision = compute_combined_score(4.5, 3.5)
        # 4.5*0.6 + 3.5*0.4 = 2.7 + 1.4 = 4.1
        assert score == pytest.approx(4.1)
        assert decision == "STRONG_PASS"

    def test_pass(self):
        score, decision = compute_combined_score(4.0, 3.0)
        # 4.0*0.6 + 3.0*0.4 = 2.4 + 1.2 = 3.6
        assert score == pytest.approx(3.6)
        assert decision == "PASS"

    def test_weak_pass(self):
        score, decision = compute_combined_score(3.5, 2.5)
        # 3.5*0.6 + 2.5*0.4 = 2.1 + 1.0 = 3.1
        assert score == pytest.approx(3.1)
        assert decision == "WEAK_PASS"

    def test_fail(self):
        score, decision = compute_combined_score(2.0, 2.0)
        # 2.0*0.6 + 2.0*0.4 = 1.2 + 0.8 = 2.0
        assert score == pytest.approx(2.0)
        assert decision == "FAIL"

    def test_custom_weights(self):
        score, decision = compute_combined_score(5.0, 1.0, prog_weight=0.80, llm_weight=0.20)
        # 5.0*0.8 + 1.0*0.2 = 4.0 + 0.2 = 4.2
        assert score == pytest.approx(4.2)
        assert decision == "STRONG_PASS"


# ---------------------------------------------------------------------------
# Tests: generate_combined_scorecard
# ---------------------------------------------------------------------------

class TestGenerateCombinedScorecard:
    def test_basic_generation(self, tmp_path):
        prog = {
            "run_id": "prog-001",
            "total_score": 4.2,
            "total_checks": 20,
            "passed_checks": 18,
            "dimensions": [
                {"dimension": "output_quality", "checks_passed": 8, "checks_total": 8, "score": 5},
            ],
        }
        llm = {
            "run_id": "llm-001",
            "total_score": 3.8,
            "average_confidence": 0.85,
            "dimensions": [
                {"name": "Output Quality", "score": 4, "weight": 0.3, "confidence": 0.9},
            ],
        }
        output_file = tmp_path / "scorecard.md"
        content = generate_combined_scorecard(prog, llm, output_file)

        assert "Combined" in content
        assert "Programmatic" in content
        assert "LLM-as-Judge" in content
        assert output_file.exists()

    def test_with_errors(self, tmp_path):
        prog = {"error": "Programmatic results not found"}
        llm = {"error": "LLM results not found"}
        output_file = tmp_path / "scorecard.md"
        content = generate_combined_scorecard(prog, llm, output_file)

        assert "Error" in content
        assert "not found" in content

    def test_decision_thresholds_present(self, tmp_path):
        prog = {"total_score": 3.0, "run_id": "p", "passed_checks": 5, "total_checks": 10, "dimensions": []}
        llm = {"total_score": 3.0, "run_id": "l", "average_confidence": 0.7, "dimensions": []}
        output_file = tmp_path / "scorecard.md"
        content = generate_combined_scorecard(prog, llm, output_file)

        assert "STRONG_PASS" in content
        assert "WEAK_PASS" in content
        assert "FAIL" in content
