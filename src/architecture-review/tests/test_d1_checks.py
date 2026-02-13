"""Tests for D1: Entity & Persistence Pattern checks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from checks.d1_entity_persistence import (
    _check_adapter_constants,
    _check_adapter_exported,
    _check_adapter_schema_sql,
    _check_entity_frozen,
    _check_entity_post_init,
    _check_orchestrator_registered,
    check_d1,
)
from discovery import ToolFiles, discover_tool_files


def _mock_tf(**overrides) -> ToolFiles:
    defaults = dict(
        tool_name="test",
        tool_dir=Path("/tmp/test"),
        adapter_file=None,
        entity_names=["TestEntity"],
        adapter_class="TestAdapter",
        repo_class="TestRepository",
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


class TestEntityFrozen:
    def test_pass(self) -> None:
        content = "@dataclass(frozen=True)\nclass TestEntity:\n    run_pk: int\n"
        tf = _mock_tf()
        findings = _check_entity_frozen(content, ["TestEntity"], tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = "@dataclass\nclass TestEntity:\n    run_pk: int\n"
        tf = _mock_tf()
        findings = _check_entity_frozen(content, ["TestEntity"], tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ENTITY_FROZEN"
        assert findings[0].severity == "error"


class TestEntityPostInit:
    def test_pass(self) -> None:
        content = "class TestEntity:\n    run_pk: int\n\n    def __post_init__(self):\n        pass\n"
        tf = _mock_tf()
        findings = _check_entity_post_init(content, ["TestEntity"], tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = "class TestEntity:\n    run_pk: int\n"
        tf = _mock_tf()
        findings = _check_entity_post_init(content, ["TestEntity"], tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ENTITY_POST_INIT"


class TestAdapterConstants:
    def test_all_present(self) -> None:
        content = (
            "SCHEMA_PATH = Path('...')\n"
            "LZ_TABLES = {}\n"
            "TABLE_DDL = {}\n"
            "QUALITY_RULES = []\n"
        )
        tf = _mock_tf()
        findings = _check_adapter_constants(content, tf)
        assert len(findings) == 0

    def test_missing_one(self) -> None:
        content = (
            "SCHEMA_PATH = Path('...')\n"
            "LZ_TABLES = {}\n"
            "TABLE_DDL = {}\n"
        )
        tf = _mock_tf()
        findings = _check_adapter_constants(content, tf)
        assert len(findings) == 1
        assert "QUALITY_RULES" in findings[0].message


class TestAdapterSchemaSQL:
    def test_match(self) -> None:
        adapter = '"lz_test_metrics": {"run_pk": "BIGINT"}'
        schema_sql = "CREATE TABLE IF NOT EXISTS lz_test_metrics"
        tf = _mock_tf()
        findings = _check_adapter_schema_sql(adapter, schema_sql, tf)
        assert len(findings) == 0

    def test_missing_table(self) -> None:
        adapter = '"lz_test_metrics": {"run_pk": "BIGINT"}'
        schema_sql = "CREATE TABLE IF NOT EXISTS lz_other_table"
        tf = _mock_tf()
        findings = _check_adapter_schema_sql(adapter, schema_sql, tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ADAPTER_SCHEMA_SQL"


class TestAdapterExported:
    def test_pass(self) -> None:
        content = "from .test_adapter import TestAdapter\n__all__ = ['TestAdapter']"
        tf = _mock_tf()
        findings = _check_adapter_exported(content, "TestAdapter", tf)
        assert len(findings) == 0

    def test_fail(self) -> None:
        content = "from .other import OtherAdapter\n"
        tf = _mock_tf()
        findings = _check_adapter_exported(content, "TestAdapter", tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ADAPTER_EXPORTED"


class TestOrchestratorRegistered:
    def test_pass(self) -> None:
        content = 'ToolIngestionConfig("test", TestAdapter, TestRepository)'
        tf = _mock_tf()
        findings = _check_orchestrator_registered(content, "test", "TestAdapter", tf)
        assert len(findings) == 0

    def test_missing(self) -> None:
        content = 'ToolIngestionConfig("other", OtherAdapter, OtherRepository)'
        tf = _mock_tf()
        findings = _check_orchestrator_registered(content, "test", "TestAdapter", tf)
        assert len(findings) == 1
        assert findings[0].rule_id == "ORCHESTRATOR_REGISTERED"


class TestIntegration:
    def test_d1_against_real_scc(self, project_root: Path) -> None:
        tf = discover_tool_files("scc", project_root)
        findings = check_d1(tf, project_root)
        # scc is a well-implemented tool, should have few/no errors
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) == 0, f"Unexpected errors: {[f.message for f in errors]}"
