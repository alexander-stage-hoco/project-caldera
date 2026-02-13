"""Tests for D4: Evaluation Infrastructure checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from checks.d4_evaluation_infra import (
    _check_judge_base_shared,
    _check_judge_min_4,
    _check_observability_enforced,
    _check_prompt_evidence,
    check_d4,
)
from discovery import ToolFiles, discover_tool_files


def _mock_tf(**overrides) -> ToolFiles:
    defaults = dict(
        tool_name="test",
        tool_dir=Path("/tmp/test"),
        adapter_file=None,
        entity_names=[],
        adapter_class=None,
        repo_class=None,
        entities_file=Path("/tmp/entities.py"),
        repositories_file=Path("/tmp/repositories.py"),
        schema_sql=Path("/tmp/schema.sql"),
        orchestrator_file=Path("/tmp/orchestrator.py"),
        adapter_init=Path("/tmp/__init__.py"),
        analyze_py=None,
        output_schema=None,
        blueprint=None,
        makefile=None,
        judges_dir=None,
        eval_orchestrator=None,
        prompts_dir=None,
        eval_strategy=None,
    )
    defaults.update(overrides)
    return ToolFiles(**defaults)


class TestJudgeBaseShared:
    def test_pass(self, tmp_path: Path) -> None:
        judges = tmp_path / "judges"
        judges.mkdir()
        base = judges / "base.py"
        base.write_text("from shared.evaluation.base_judge import BaseJudge\n")
        tf = _mock_tf(judges_dir=judges)
        findings = _check_judge_base_shared(tf)
        assert len(findings) == 0

    def test_fail_no_base(self, tmp_path: Path) -> None:
        judges = tmp_path / "judges"
        judges.mkdir()
        (judges / "judge1.py").write_text("class Judge1: pass\n")
        tf = _mock_tf(judges_dir=judges)
        findings = _check_judge_base_shared(tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "JUDGE_BASE_SHARED"

    def test_fail_no_dir(self) -> None:
        tf = _mock_tf(judges_dir=None)
        findings = _check_judge_base_shared(tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "JUDGE_DIR_MISSING"


class TestJudgeMin4:
    def test_enough(self, tmp_path: Path) -> None:
        judges = tmp_path / "judges"
        judges.mkdir()
        (judges / "__init__.py").write_text("")
        (judges / "base.py").write_text("")
        for i in range(4):
            (judges / f"judge{i}.py").write_text(f"class Judge{i}: pass\n")
        tf = _mock_tf(judges_dir=judges)
        findings = _check_judge_min_4(tf)
        assert len(findings) == 0

    def test_too_few(self, tmp_path: Path) -> None:
        judges = tmp_path / "judges"
        judges.mkdir()
        (judges / "__init__.py").write_text("")
        (judges / "base.py").write_text("")
        (judges / "judge1.py").write_text("class Judge1: pass\n")
        tf = _mock_tf(judges_dir=judges)
        findings = _check_judge_min_4(tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "JUDGE_MIN_4"


class TestPromptEvidence:
    def test_placeholder_present(self, tmp_path: Path) -> None:
        prompts = tmp_path / "prompts"
        prompts.mkdir()
        (prompts / "test.md").write_text("Review the {{ evidence }} below.\n")
        tf = _mock_tf(prompts_dir=prompts)
        findings = _check_prompt_evidence(tf)
        assert len(findings) == 0

    def test_placeholder_missing(self, tmp_path: Path) -> None:
        prompts = tmp_path / "prompts"
        prompts.mkdir()
        (prompts / "test.md").write_text("Review the data below.\n")
        tf = _mock_tf(prompts_dir=prompts)
        findings = _check_prompt_evidence(tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "PROMPT_EVIDENCE"


class TestObservabilityEnforced:
    def test_pass(self, tmp_path: Path) -> None:
        orch = tmp_path / "orchestrator.py"
        orch.write_text("from shared.observability import log_interaction\n")
        tf = _mock_tf(eval_orchestrator=orch)
        findings = _check_observability_enforced(tf)
        assert len(findings) == 0

    def test_fail(self, tmp_path: Path) -> None:
        orch = tmp_path / "orchestrator.py"
        orch.write_text("import json\n")
        tf = _mock_tf(eval_orchestrator=orch)
        findings = _check_observability_enforced(tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "OBSERVABILITY_ENFORCED"


class TestIntegration:
    def test_d4_against_real_lizard(self, project_root: Path) -> None:
        tf = discover_tool_files("lizard", project_root)
        findings = check_d4(tf)
        # lizard has judges, so shouldn't have errors
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"
