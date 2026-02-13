"""Tests for D3: Code Conventions checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from checks.d3_code_conventions import (
    _check_future_annotations,
    _check_makefile_common,
    _check_makefile_venv_ready,
    _check_pep604_unions,
    check_d3,
)
from discovery import discover_tool_files


class TestFutureAnnotations:
    def test_present(self, tmp_path: Path) -> None:
        content = "from __future__ import annotations\nimport json\n"
        findings = _check_future_annotations(content, tmp_path / "test.py")
        assert len(findings) == 0

    def test_missing(self, tmp_path: Path) -> None:
        content = "import json\nimport sys\n"
        findings = _check_future_annotations(content, tmp_path / "test.py")
        assert len(findings) == 1
        assert findings[0].rule_id == "FUTURE_ANNOTATIONS"


class TestPep604:
    def test_no_optional(self, tmp_path: Path) -> None:
        content = "def foo(x: str | None) -> int:\n    pass\n"
        findings = _check_pep604_unions(content, tmp_path / "test.py")
        assert len(findings) == 0

    def test_has_optional(self, tmp_path: Path) -> None:
        content = "from typing import Optional\ndef foo(x: Optional[str]) -> int:\n    pass\n"
        findings = _check_pep604_unions(content, tmp_path / "test.py")
        assert len(findings) == 1
        assert findings[0].rule_id == "PEP604_UNIONS"


class TestMakefileCommon:
    def test_present(self) -> None:
        from discovery import ToolFiles
        content = "include ../../Makefile.common\n\nsetup:\n\t@echo setup\n"
        tf = ToolFiles(
            tool_name="test", tool_dir=Path("/tmp"), adapter_file=None,
            entity_names=[], adapter_class=None, repo_class=None,
            entities_file=Path("/tmp/e"), repositories_file=Path("/tmp/r"),
            schema_sql=Path("/tmp/s"), orchestrator_file=Path("/tmp/o"),
            adapter_init=Path("/tmp/i"), analyze_py=None, output_schema=None,
            blueprint=None, makefile=Path("/tmp/Makefile"), judges_dir=None,
            eval_orchestrator=None, prompts_dir=None, eval_strategy=None,
        )
        findings = _check_makefile_common(content, tf)
        assert len(findings) == 0

    def test_missing(self) -> None:
        from discovery import ToolFiles
        content = "setup:\n\t@echo setup\n"
        tf = ToolFiles(
            tool_name="test", tool_dir=Path("/tmp"), adapter_file=None,
            entity_names=[], adapter_class=None, repo_class=None,
            entities_file=Path("/tmp/e"), repositories_file=Path("/tmp/r"),
            schema_sql=Path("/tmp/s"), orchestrator_file=Path("/tmp/o"),
            adapter_init=Path("/tmp/i"), analyze_py=None, output_schema=None,
            blueprint=None, makefile=Path("/tmp/Makefile"), judges_dir=None,
            eval_orchestrator=None, prompts_dir=None, eval_strategy=None,
        )
        findings = _check_makefile_common(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "MAKEFILE_COMMON"


class TestMakefileVenvReady:
    def test_present(self) -> None:
        from discovery import ToolFiles
        content = "VENV ?= .venv\n$(VENV)/bin/python script.py\n"
        tf = ToolFiles(
            tool_name="test", tool_dir=Path("/tmp"), adapter_file=None,
            entity_names=[], adapter_class=None, repo_class=None,
            entities_file=Path("/tmp/e"), repositories_file=Path("/tmp/r"),
            schema_sql=Path("/tmp/s"), orchestrator_file=Path("/tmp/o"),
            adapter_init=Path("/tmp/i"), analyze_py=None, output_schema=None,
            blueprint=None, makefile=Path("/tmp/Makefile"), judges_dir=None,
            eval_orchestrator=None, prompts_dir=None, eval_strategy=None,
        )
        findings = _check_makefile_venv_ready(content, tf)
        assert len(findings) == 0

    def test_missing(self) -> None:
        from discovery import ToolFiles
        content = "setup:\n\tpython script.py\n"
        tf = ToolFiles(
            tool_name="test", tool_dir=Path("/tmp"), adapter_file=None,
            entity_names=[], adapter_class=None, repo_class=None,
            entities_file=Path("/tmp/e"), repositories_file=Path("/tmp/r"),
            schema_sql=Path("/tmp/s"), orchestrator_file=Path("/tmp/o"),
            adapter_init=Path("/tmp/i"), analyze_py=None, output_schema=None,
            blueprint=None, makefile=Path("/tmp/Makefile"), judges_dir=None,
            eval_orchestrator=None, prompts_dir=None, eval_strategy=None,
        )
        findings = _check_makefile_venv_ready(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "MAKEFILE_VENV_READY"


class TestIntegration:
    def test_d3_against_real_scc(self, project_root: Path) -> None:
        tf = discover_tool_files("scc", project_root)
        findings = check_d3(tf)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"
