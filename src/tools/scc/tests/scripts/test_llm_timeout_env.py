from __future__ import annotations

import os

import pytest

from scripts import llm_evaluate


class DummyEvaluator:
    def __init__(self, working_dir, model, timeout):
        self.timeout = timeout

    def register_focused_judges(self):
        pass

    def register_all_judges(self):
        pass

    def evaluate(self, run_assertions=True):
        class Result:
            run_id = "run"
            total_score = 5.0
            average_confidence = 1.0
            decision = "PASS"
            dimensions = []
            programmatic_score = None
            combined_score = None

        return Result()

    def save_results(self, result):
        return llm_evaluate.Path("/tmp/llm.json")

    def generate_markdown_report(self, result):
        return ""


def test_llm_timeout_env(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, int] = {}

    class CapturingEvaluator(DummyEvaluator):
        def __init__(self, working_dir, model, timeout):
            super().__init__(working_dir, model, timeout)
            captured["timeout"] = timeout

    monkeypatch.setenv("LLM_TIMEOUT", "300")
    monkeypatch.setattr(llm_evaluate, "LLMEvaluator", CapturingEvaluator)
    args = ["--mode", "focused", "--model", "opus", "--working-dir", "."]
    monkeypatch.setattr(llm_evaluate.sys, "argv", ["llm_evaluate.py", *args])

    llm_evaluate.main()
    assert captured["timeout"] == 300
