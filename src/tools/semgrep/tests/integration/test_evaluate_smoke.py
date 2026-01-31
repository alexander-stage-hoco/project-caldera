"""Smoke test for programmatic evaluation output."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import json

from evaluate import run_evaluation


def test_run_evaluation_smoke(tmp_path: Path, sample_analysis_data: dict) -> None:
    analysis_path = tmp_path / "analysis.json"
    analysis_path.write_text(json.dumps(sample_analysis_data))

    ground_truth_dir = tmp_path / "ground-truth"
    ground_truth_dir.mkdir(parents=True)
    ground_truth = {
        "language": "python",
        "files": {
            "main.py": {
                "expected_smells": [
                    {"smell_id": "D1_EMPTY_CATCH", "count": 1, "lines": [10]},
                    {"smell_id": "E2_ASYNC_VOID", "count": 1, "lines": [25]},
                ]
            }
        },
    }
    (ground_truth_dir / "python.json").write_text(json.dumps(ground_truth))

    report = run_evaluation(
        analysis_path=str(analysis_path),
        ground_truth_dir=str(ground_truth_dir),
        skip_performance=True,
    )

    assert report.total > 0
    assert 0.0 <= report.score <= 1.0
