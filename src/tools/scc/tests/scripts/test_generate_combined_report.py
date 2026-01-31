"""Tests for combined scorecard generation."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_combined_report import generate_combined_scorecard, load_programmatic_results


def test_load_programmatic_results_computes_totals(tmp_path):
    """Totals derive from dimension-level checks."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    payload = {
        "run_id": "eval-123",
        "timestamp": "2026-01-01T00:00:00Z",
        "dimensions": [
            {"dimension": "output_quality", "checks_passed": 8, "checks_total": 8, "score": 5},
            {"dimension": "integration_fit", "checks_passed": 6, "checks_total": 7, "score": 4},
        ],
        "total_score": 4.8,
        "decision": "PASS",
    }
    file_path = results_dir / "eval-123_checks.json"
    file_path.write_text(json.dumps(payload))

    data = load_programmatic_results(None, results_dir)

    assert data["passed_checks"] == 14
    assert data["total_checks"] == 15


def test_generate_combined_scorecard_uses_dimension_names(tmp_path):
    """Combined report uses programmatic dimension names."""
    prog_results = {
        "run_id": "eval-123",
        "total_score": 5.0,
        "passed_checks": 10,
        "total_checks": 12,
        "dimensions": [
            {"dimension": "output_quality", "checks_passed": 8, "checks_total": 8, "score": 5},
            {"dimension": "integration_fit", "checks_passed": 2, "checks_total": 4, "score": 3},
        ],
    }
    llm_results = {
        "run_id": "llm-123",
        "total_score": 4.0,
        "average_confidence": 0.8,
        "dimensions": [],
    }

    output_file = tmp_path / "combined.md"
    content = generate_combined_scorecard(prog_results, llm_results, output_file)

    assert "output_quality" in content
    assert "integration_fit" in content
    assert output_file.exists()
