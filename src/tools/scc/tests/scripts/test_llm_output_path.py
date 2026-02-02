from __future__ import annotations

import json
from pathlib import Path

import scripts.llm_evaluate as llm_evaluate


class _DummyResult:
    def __init__(self):
        self.run_id = "dummy"
        self.timestamp = "2026-01-01T00:00:00Z"
        self.model = "test"
        self.dimensions = []
        self.total_score = 4.0
        self.average_confidence = 0.9
        self.decision = "PASS"
        self.programmatic_score = None
        self.combined_score = None

    def to_json(self, indent: int = 2) -> str:
        return json.dumps({"run_id": self.run_id}, indent=indent)


class _DummyEvaluator:
    def __init__(self, *args, **kwargs):
        self.results_dir = Path.cwd() / "results"

    def register_focused_judges(self):
        return None

    def register_all_judges(self):
        return None

    def evaluate(self, run_assertions: bool = True):
        return _DummyResult()

    def compute_combined_score(self, result, programmatic_score):
        return result

    def save_results(self, result):
        output_file = self.results_dir / "llm_evaluation.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.to_json())
        return output_file

    def generate_markdown_report(self, result):
        return "# Report"


def test_llm_evaluate_writes_output_path(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "llm_evaluation.json"
    monkeypatch.setattr(llm_evaluate, "LLMEvaluator", _DummyEvaluator)
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm_evaluate.py",
            "--mode",
            "focused",
            "--output",
            str(output_path),
        ],
    )

    exit_code = llm_evaluate.main()

    assert exit_code == 0
    assert output_path.exists()
