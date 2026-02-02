from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import evaluate


def test_evaluate_all_writes_compliance_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True)
    (output_dir / "sample.json").write_text(json.dumps({"metadata": {}, "data": {}}))

    def fake_evaluate_output(*_args, **_kwargs):
        return {
            "repository": "sample",
            "output_file": str(output_dir / "sample.json"),
            "timestamp": "2026-01-01T00:00:00Z",
            "overall_score": 4.0,
            "decision": "PASS",
            "summary": {
                "total_checks": 1,
                "passed_checks": 1,
                "pass_rate": 100.0,
            },
            "dimensions": [],
        }

    monkeypatch.setattr(evaluate, "evaluate_output", fake_evaluate_output)

    results_dir = tmp_path / "results"
    evaluate.evaluate_all(output_dir, tmp_path / "gt", results_dir)

    assert (results_dir / "evaluation_report.json").exists()
    assert (results_dir / "scorecard.md").exists()
