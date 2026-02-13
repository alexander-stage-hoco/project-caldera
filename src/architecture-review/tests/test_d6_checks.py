"""Tests for D6: BLUEPRINT Alignment checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from checks.d6_blueprint import (
    _check_blueprint_has_eval_data,
    _check_blueprint_no_placeholders,
    _check_blueprint_sections,
    _check_blueprint_tool_referenced,
    check_d6,
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


class TestBlueprintSections:
    def test_all_present(self) -> None:
        content = (
            "# Executive Summary\nfoo\n"
            "# Architecture\nbar\n"
            "# Implementation Plan\nbaz\n"
            "# Configuration\nqux\n"
            "# Performance\nperf\n"
            "# Evaluation\neval\n"
            "# Risk\nrisk\n"
        )
        tf = _mock_tf()
        findings = _check_blueprint_sections(content, tf)
        assert len(findings) == 0

    def test_missing_some(self) -> None:
        content = (
            "# Executive Summary\nfoo\n"
            "# Architecture\nbar\n"
            "# Implementation Plan\nbaz\n"
            "# Configuration\nqux\n"
        )
        tf = _mock_tf()
        findings = _check_blueprint_sections(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "BLUEPRINT_SECTIONS"
        assert "Performance" in findings[0].message


class TestBlueprintNoPlaceholders:
    def test_clean(self) -> None:
        content = "# Architecture\nThis is a real description.\n"
        tf = _mock_tf()
        findings = _check_blueprint_no_placeholders(content, tf)
        assert len(findings) == 0

    def test_has_todo(self) -> None:
        content = "# Architecture\nTODO: fill this in\n"
        tf = _mock_tf()
        findings = _check_blueprint_no_placeholders(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "BLUEPRINT_NO_PLACEHOLDERS"

    def test_has_tbd(self) -> None:
        content = "# Architecture\nThis is TBD\n"
        tf = _mock_tf()
        findings = _check_blueprint_no_placeholders(content, tf)
        assert len(findings) == 1


class TestBlueprintHasEvalData:
    def test_with_numbers(self) -> None:
        content = "# Evaluation\nAccuracy: 4.84 out of 5\nReliability: 98%\n"
        tf = _mock_tf()
        findings = _check_blueprint_has_eval_data(content, tf)
        assert len(findings) == 0

    def test_empty_section(self) -> None:
        content = "# Evaluation\nNo data yet.\n# Risk\nSomething\n"
        tf = _mock_tf()
        findings = _check_blueprint_has_eval_data(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "BLUEPRINT_HAS_EVAL_DATA"


class TestBlueprintToolReferenced:
    def test_present(self) -> None:
        content = "# Executive Summary\nThe test tool analyzes code.\n"
        tf = _mock_tf()
        findings = _check_blueprint_tool_referenced(content, tf)
        assert len(findings) == 0

    def test_missing(self) -> None:
        content = "# Executive Summary\nThis tool analyzes code.\n"
        tf = _mock_tf(tool_name="xyzzy")
        findings = _check_blueprint_tool_referenced(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "BLUEPRINT_TOOL_REFERENCED"


class TestIntegration:
    def test_d6_against_real_lizard(self, project_root: Path) -> None:
        tf = discover_tool_files("lizard", project_root)
        findings = check_d6(tf)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"
