"""Tests for LLM judge envelope handling."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.llm.judges.ccn_accuracy import CCNAccuracyJudge
from evaluation.llm.judges.function_detection import FunctionDetectionJudge
from evaluation.llm.judges.hotspot_ranking import HotspotRankingJudge
from evaluation.llm.judges.statistics import StatisticsJudge


def _write_envelope(tmp_path: Path) -> Path:
    output_path = tmp_path / "output" / "output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    envelope = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-25T09:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-25T09:00:00Z",
            "root_path": "synthetic",
            "lizard_version": "lizard 1.17.10",
            "summary": {
                "total_files": 1,
                "total_functions": 1,
                "total_nloc": 10,
                "total_ccn": 1,
                "ccn_distribution": {
                    "count": 1,
                    "min": 1,
                    "max": 1,
                    "mean": 1,
                    "median": 1,
                    "p25": 1,
                    "p50": 1,
                    "p75": 1,
                    "p90": 1,
                    "p95": 1,
                    "p99": 1,
                    "stddev": 0,
                    "gini": 0,
                },
                "nloc_distribution": {
                    "count": 1,
                    "min": 10,
                    "max": 10,
                    "mean": 10,
                    "median": 10,
                    "p25": 10,
                    "p50": 10,
                    "p75": 10,
                    "p90": 10,
                    "p95": 10,
                    "p99": 10,
                    "stddev": 0,
                    "gini": 0,
                },
                "params_distribution": {
                    "count": 1,
                    "min": 1,
                    "max": 1,
                    "mean": 1,
                    "median": 1,
                    "p25": 1,
                    "p50": 1,
                    "p75": 1,
                    "p90": 1,
                    "p95": 1,
                    "p99": 1,
                    "stddev": 0,
                    "gini": 0,
                },
            },
            "directories": [],
            "files": [
                {
                    "path": "simple.py",
                    "language": "Python",
                    "nloc": 10,
                    "function_count": 1,
                    "total_ccn": 1,
                    "avg_ccn": 1.0,
                    "max_ccn": 1,
                    "functions": [
                        {
                            "name": "simple",
                            "ccn": 1,
                            "nloc": 10,
                            "parameter_count": 1,
                            "start_line": 1,
                            "end_line": 10,
                        }
                    ],
                }
            ],
        },
    }
    output_path.write_text(json.dumps(envelope))
    return output_path


def _write_ground_truth(tmp_path: Path) -> None:
    gt_dir = tmp_path / "evaluation" / "ground-truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    gt = {
        "language": "python",
        "generated_at": "2026-01-25T09:00:00Z",
        "lizard_version": "lizard 1.17.10",
        "total_files": 1,
        "total_functions": 1,
        "total_ccn": 1,
        "files": {
            "simple.py": {
                "expected_functions": 1,
                "total_ccn": 1,
                "functions": {
                    "simple": {
                        "ccn": 1,
                        "nloc": 10,
                        "params": 1,
                        "start_line": 1,
                        "end_line": 10,
                    }
                },
            }
        },
    }
    (gt_dir / "python.json").write_text(json.dumps(gt))


def test_judges_load_envelope(tmp_path: Path) -> None:
    analysis_path = _write_envelope(tmp_path)
    _write_ground_truth(tmp_path)

    judges = [
        CCNAccuracyJudge(working_dir=tmp_path, analysis_path=analysis_path),
        FunctionDetectionJudge(working_dir=tmp_path, analysis_path=analysis_path),
        StatisticsJudge(working_dir=tmp_path, analysis_path=analysis_path),
        HotspotRankingJudge(working_dir=tmp_path, analysis_path=analysis_path),
    ]

    for judge in judges:
        evidence = judge.collect_evidence()
        assert "error" not in evidence

        ok, failures = judge.run_ground_truth_assertions()
        assert ok, f"{judge.dimension_name} failures: {failures}"
