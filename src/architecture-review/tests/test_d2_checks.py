"""Tests for D2: Output Schema & Envelope checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from checks.d2_output_schema import (
    _check_analyze_cli_args,
    _check_analyze_envelope,
    _check_analyze_path_norm,
    _check_envelope_8_fields,
    _check_schema_draft_2020,
    _check_schema_version_const,
    check_d2,
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


class TestSchemaDraft2020:
    def test_pass(self) -> None:
        content = json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema"})
        tf = _mock_tf()
        findings = _check_schema_draft_2020(content, tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#"})
        tf = _mock_tf()
        findings = _check_schema_draft_2020(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "SCHEMA_DRAFT_2020"


class TestSchemaVersionConst:
    def test_pass_nested(self) -> None:
        """schema_version with const inside metadata properties (standard envelope)."""
        content = json.dumps({
            "properties": {
                "metadata": {
                    "properties": {"schema_version": {"const": "1.0.0"}}
                }
            }
        })
        tf = _mock_tf()
        findings = _check_schema_version_const(content, tf)
        assert len(findings) == 0

    def test_pass_flat(self) -> None:
        """schema_version with const at top level (flat schema fallback)."""
        content = json.dumps({
            "properties": {"schema_version": {"const": "1.0.0"}}
        })
        tf = _mock_tf()
        findings = _check_schema_version_const(content, tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = json.dumps({
            "properties": {
                "metadata": {
                    "properties": {"schema_version": {"pattern": "^\\d+\\.\\d+\\.\\d+$"}}
                }
            }
        })
        tf = _mock_tf()
        findings = _check_schema_version_const(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "SCHEMA_VERSION_CONST"


class TestEnvelope8Fields:
    def test_pass(self) -> None:
        """All 8 fields present inside metadata (standard envelope)."""
        content = json.dumps({
            "properties": {
                "metadata": {
                    "required": ["schema_version", "tool_name", "tool_version", "repo_id",
                                 "run_id", "branch", "commit", "timestamp"],
                    "properties": {},
                }
            }
        })
        tf = _mock_tf()
        findings = _check_envelope_8_fields(content, tf)
        assert len(findings) == 0

    def test_missing_some(self) -> None:
        content = json.dumps({
            "properties": {
                "metadata": {
                    "required": ["schema_version", "tool_name", "tool_version"],
                    "properties": {"repo_id": {}, "run_id": {}},
                }
            }
        })
        tf = _mock_tf()
        findings = _check_envelope_8_fields(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ENVELOPE_8_FIELDS"


class TestAnalyzePathNorm:
    def test_shared_import(self) -> None:
        content = "from shared.path_utils import normalize_file_path\n"
        tf = _mock_tf()
        findings = _check_analyze_path_norm(content, tf)
        assert len(findings) == 0

    def test_common_import(self) -> None:
        content = "from common.path_normalization import normalize\n"
        tf = _mock_tf()
        findings = _check_analyze_path_norm(content, tf)
        assert len(findings) == 0

    def test_missing(self) -> None:
        content = "import json\nimport sys\n"
        tf = _mock_tf()
        findings = _check_analyze_path_norm(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ANALYZE_PATH_NORM"


class TestAnalyzeCliArgs:
    def test_pattern_a(self) -> None:
        content = "add_common_args(parser)\n"
        tf = _mock_tf()
        findings = _check_analyze_cli_args(content, tf)
        assert len(findings) == 0

    def test_pattern_b(self) -> None:
        content = "\n".join([f"parser.add_argument('--arg{i}')" for i in range(7)])
        tf = _mock_tf()
        findings = _check_analyze_cli_args(content, tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = "parser.add_argument('--one')\n"
        tf = _mock_tf()
        findings = _check_analyze_cli_args(content, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ANALYZE_CLI_ARGS"


class TestIntegration:
    def test_d2_against_real_lizard(self, project_root: Path) -> None:
        tf = discover_tool_files("lizard", project_root)
        findings = check_d2(tf)
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"
