from __future__ import annotations

import json
from pathlib import Path

from evaluation.llm.judges.base import BaseJudge


class _DummyJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "dummy"

    @property
    def weight(self) -> float:
        return 1.0

    def get_default_prompt(self) -> str:
        return ""

    def collect_evidence(self) -> dict:
        return {}

    def evaluate(self):
        raise NotImplementedError


def test_load_all_analysis_results_recursive_outputs(tmp_path: Path) -> None:
    output_root = tmp_path / "outputs"
    run_dir = output_root / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "output.json").write_text(json.dumps({"results": {"files": []}}))

    judge = _DummyJudge(output_dir=output_root)
    results = judge.load_all_analysis_results()

    assert "run-123" in results
    assert results["run-123"]["results"]["files"] == []
