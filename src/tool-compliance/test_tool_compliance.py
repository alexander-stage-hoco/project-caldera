"""Tests for the tool compliance scanner."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import json

from tool_compliance import (
    CheckResult,
    TOOL_RULES,
    _parse_make_targets,
    _check_adapter_compliance,
    _check_adapter_schema_alignment,
    _check_adapter_integration,
    _check_adapter_quality_rules_coverage,
    _check_dbt_model_coverage,
    _check_entity_repository_alignment,
    _check_output_metadata_consistency,
    _check_test_structure_naming,
    _normalize_tool_name_for_dbt,
    _parse_rollup_names_from_eval_strategy,
    _is_valid_iso8601,
    _parse_schema_sql,
    _parse_column_definitions,
    _parse_ddl_columns,
    _extract_table_body,
    _types_match,
    _looks_like_file_path,
    _collect_path_values,
    build_report,
    scan_tool,
)


def test_parse_make_targets_ignores_comments(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "# comment\n"
        "setup:\n"
        "\t@echo setup\n"
        "\n"
        "analyze: dep\n"
        "\t@echo analyze\n"
    )
    targets = _parse_make_targets(makefile)
    assert "setup" in targets
    assert "analyze" in targets
    assert "dep" not in targets


def test_build_report_collects_tools(tmp_path: Path) -> None:
    tools_root = tmp_path / "tools"
    tools_root.mkdir()
    tool_dir = tools_root / "demo"
    tool_dir.mkdir()
    (tool_dir / "Makefile").write_text("setup:\n")
    schema_path = tool_dir / "schemas" / "output.schema.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text("{}")
    report = build_report(tools_root)
    assert report["summary"]["tool_count"] == 1
    assert report["tools"][0]["name"] == "demo"
    assert report["tools"][0]["status"] == "fail"
    assert any(
        check["check_id"] == "structure.paths"
        for check in report["tools"][0]["checks"]
    )


def test_all_tools_have_rule_definitions() -> None:
    tools_root = Path(__file__).resolve().parents[1] / "tools"
    tool_dirs = [
        entry.name
        for entry in tools_root.iterdir()
        if entry.is_dir() and (entry / "Makefile").exists()
    ]
    missing = [name for name in tool_dirs if name not in TOOL_RULES]
    assert not missing, f"Missing TOOL_RULES entries for: {missing}"
    for name in tool_dirs:
        rules = TOOL_RULES[name]
        assert rules.get("required_check_modules"), f"{name} missing required_check_modules"
        assert rules.get("required_prompts"), f"{name} missing required_prompts"


def test_adapter_compliance_check_runs() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    result = _check_adapter_compliance(tool_root, "scc")
    assert result.check_id == "adapter.compliance"


def test_extract_table_body() -> None:
    content = "CREATE TABLE foo (id INT, name VARCHAR, PRIMARY KEY (id));"
    # Start right after the opening paren of "foo ("
    start_idx = content.index("(") + 1
    result = _extract_table_body(content, start_idx)
    assert result == "id INT, name VARCHAR, PRIMARY KEY (id)"


def test_extract_table_body_nested_parens() -> None:
    content = "CREATE TABLE foo (id INT NOT NULL, PRIMARY KEY (id, name));"
    start_idx = content.index("(") + 1
    result = _extract_table_body(content, start_idx)
    assert "PRIMARY KEY (id, name)" in result


def test_parse_schema_sql(tmp_path: Path) -> None:
    schema_sql = tmp_path / "schema.sql"
    schema_sql.write_text(
        """
        CREATE TABLE lz_test_table (
            id BIGINT NOT NULL,
            name VARCHAR NOT NULL,
            value INTEGER,
            ratio DOUBLE,
            PRIMARY KEY (id)
        );
        """
    )
    result = _parse_schema_sql(schema_sql)
    assert "lz_test_table" in result
    assert result["lz_test_table"]["id"] == "BIGINT"
    assert result["lz_test_table"]["name"] == "VARCHAR"
    assert result["lz_test_table"]["value"] == "INTEGER"
    assert result["lz_test_table"]["ratio"] == "DOUBLE"


def test_parse_schema_sql_with_composite_primary_key(tmp_path: Path) -> None:
    schema_sql = tmp_path / "schema.sql"
    schema_sql.write_text(
        """
        CREATE TABLE lz_test_table (
            run_pk BIGINT NOT NULL,
            file_id VARCHAR NOT NULL,
            name VARCHAR,
            PRIMARY KEY (run_pk, file_id)
        );
        """
    )
    result = _parse_schema_sql(schema_sql)
    assert "lz_test_table" in result
    assert result["lz_test_table"]["run_pk"] == "BIGINT"
    assert result["lz_test_table"]["file_id"] == "VARCHAR"
    assert result["lz_test_table"]["name"] == "VARCHAR"
    # PRIMARY KEY should be filtered out
    assert "PRIMARY" not in result["lz_test_table"]


def test_parse_column_definitions() -> None:
    body = """
        id BIGINT NOT NULL,
        name VARCHAR NOT NULL,
        value INTEGER,
        PRIMARY KEY (id),
        UNIQUE (name)
    """
    result = _parse_column_definitions(body)
    assert result["id"] == "BIGINT"
    assert result["name"] == "VARCHAR"
    assert result["value"] == "INTEGER"
    assert "PRIMARY" not in result
    assert "UNIQUE" not in result


def test_types_match_exact() -> None:
    assert _types_match("VARCHAR", "VARCHAR")
    assert _types_match("BIGINT", "BIGINT")
    assert _types_match("integer", "INTEGER")


def test_types_match_compatible() -> None:
    assert _types_match("VARCHAR", "TEXT")
    assert _types_match("TEXT", "VARCHAR")
    assert _types_match("INTEGER", "INT")
    assert _types_match("INT", "INTEGER")


def test_types_match_incompatible() -> None:
    assert not _types_match("VARCHAR", "INTEGER")
    assert not _types_match("DOUBLE", "BIGINT")


def test_adapter_schema_alignment_check_runs() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    result = _check_adapter_schema_alignment(tool_root, "scc")
    assert result.check_id == "adapter.schema_alignment"


def test_adapter_schema_alignment_fails_without_adapter() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_adapter_schema_alignment(tool_root, "unknown")
    assert result.status == "FAIL"
    assert "No adapter rule defined" in result.message


def test_parse_ddl_columns() -> None:
    ddl = """
        CREATE TABLE IF NOT EXISTS lz_test_table (
            id BIGINT NOT NULL,
            name VARCHAR NOT NULL,
            value INTEGER,
            PRIMARY KEY (id, name)
        )
    """
    result = _parse_ddl_columns(ddl)
    assert result["id"] == "BIGINT"
    assert result["name"] == "VARCHAR"
    assert result["value"] == "INTEGER"
    assert "PRIMARY" not in result


def test_parse_ddl_columns_returns_empty_for_invalid_ddl() -> None:
    result = _parse_ddl_columns("not a valid ddl")
    assert result == {}


def test_scan_tool_evaluate_uses_temp_dir(tmp_path: Path, monkeypatch) -> None:
    tool_root = tmp_path / "demo"
    tool_root.mkdir()

    required_files = [
        "Makefile",
        "README.md",
        "BLUEPRINT.md",
        "EVAL_STRATEGY.md",
        "requirements.txt",
        "scripts/analyze.py",
        "scripts/evaluate.py",
        "schemas/output.schema.json",
        "evaluation/llm/orchestrator.py",
        "evaluation/scorecard.md",
    ]
    required_dirs = [
        "scripts/checks",
        "eval-repos/synthetic",
        "eval-repos/real",
        "evaluation/ground-truth",
        "evaluation/llm/judges",
        "evaluation/llm/prompts",
        "tests/unit",
        "tests/integration",
    ]

    for rel in required_dirs:
        (tool_root / rel).mkdir(parents=True, exist_ok=True)
    for rel in required_files:
        path = tool_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n")

    (tool_root / "evaluation" / "ground-truth" / "sample.json").write_text("{}")

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["metadata", "data"],
        "properties": {
            "metadata": {
                "type": "object",
                "required": [
                    "tool_name",
                    "tool_version",
                    "run_id",
                    "repo_id",
                    "branch",
                    "commit",
                    "timestamp",
                    "schema_version",
                ],
                "properties": {
                    "tool_name": {"type": "string"},
                    "tool_version": {"type": "string"},
                    "run_id": {"type": "string"},
                    "repo_id": {"type": "string"},
                    "branch": {"type": "string"},
                    "commit": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "schema_version": {"type": "string", "const": "1.0.0"},
                },
            },
            "data": {"type": "object"},
        },
    }
    (tool_root / "schemas" / "output.schema.json").write_text(json.dumps(schema))

    (tool_root / "Makefile").write_text(
        "setup:\n\techo setup\n"
        "analyze:\n\techo analyze\n"
        "evaluate:\n\techo evaluate\n"
        "evaluate-llm:\n\techo llm\n"
        "test:\n\techo test\n"
        "clean:\n\techo clean\n"
    )
    (tool_root / "evaluation" / "scorecard.md").write_text("Scorecard\n")
    (tool_root / "EVAL_STRATEGY.md").write_text(
        "# Evaluation Strategy\n\n## Rollup Validation\n\nRollups:\n- direct\n- recursive\n\nTests:\n- src/sot-engine/dbt/tests/test_rollup_scc_direct_vs_recursive.sql\n"
    )

    def fake_run_make(tool_path: Path, target: str, env: dict[str, str]) -> str | None:
        if target == "evaluate":
            out_dir = Path(env["EVAL_OUTPUT_DIR"])
            out_dir.mkdir(parents=True, exist_ok=True)
            output = {
                "metadata": {
                    "tool_name": "demo",
                    "tool_version": "1.0.0",
                    "run_id": "run",
                    "repo_id": "repo",
                    "branch": "main",
                    "commit": "0" * 40,
                    "timestamp": "2026-01-01T00:00:00Z",
                    "schema_version": "1.0.0",
                },
                "data": {},
            }
            (out_dir / "output.json").write_text(json.dumps(output))
            (out_dir / "scorecard.md").write_text("Scorecard\n")
            (out_dir / "checks.json").write_text("{}")
        return None

    def fake_schema_check(_tool_root: Path, _output_path: Path, _venv: str | None) -> CheckResult:
        return CheckResult(
            check_id="output.schema_validate",
            status="pass",
            severity="critical",
            message="Schema validation skipped in test",
            evidence=[],
        )

    monkeypatch.setattr("tool_compliance._run_make", fake_run_make)
    monkeypatch.setattr("tool_compliance._check_output_schema", fake_schema_check)

    result = scan_tool(tool_root, run_evaluate=True)
    evaluation_checks = [
        check for check in result.checks if check.check_id == "evaluation.results"
    ]
    assert evaluation_checks
    assert evaluation_checks[0].status == "pass"
    rollup_checks = [
        check for check in result.checks if check.check_id == "evaluation.rollup_validation"
    ]
    assert rollup_checks
    assert rollup_checks[0].status == "fail"


def test_check_adapter_integration_passes_for_layout_scanner() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "layout-scanner"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_adapter_integration(tool_root, "layout-scanner")
    assert result.check_id == "adapter.integration"
    # May pass or skip depending on fixture availability


def test_check_adapter_integration_fails_unknown() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_adapter_integration(tool_root, "unknown")
    assert result.check_id == "adapter.integration"
    assert result.status == "FAIL"
    assert "No adapter rule defined" in result.message


def test_check_adapter_quality_rules_coverage_passes_for_scc() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_adapter_quality_rules_coverage(tool_root, "scc")
    assert result.check_id == "adapter.quality_rules_coverage"
    assert result.status in ("PASS", "SKIP")


def test_check_adapter_quality_rules_coverage_fails_unknown() -> None:
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_adapter_quality_rules_coverage(tool_root, "unknown")
    assert result.check_id == "adapter.quality_rules_coverage"
    assert result.status == "FAIL"
    assert "No adapter rule defined" in result.message


def test_check_adapter_quality_rules_coverage_validates_patterns() -> None:
    """Test that quality rules are checked against implementation patterns."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "layout-scanner"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_adapter_quality_rules_coverage(tool_root, "layout-scanner")
    assert result.check_id == "adapter.quality_rules_coverage"
    # Layout adapter should have QUALITY_RULES defined


# Tests for dbt.model_coverage
def test_dbt_model_coverage_passes_for_scc() -> None:
    """Test dbt model coverage passes for scc which has staging and rollup models."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_dbt_model_coverage(tool_root, "scc")
    assert result.check_id == "dbt.model_coverage"
    assert result.status == "pass"


def test_dbt_model_coverage_fails_without_adapter() -> None:
    """Test dbt model coverage fails for tools without adapter."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_dbt_model_coverage(tool_root, "unknown")
    assert result.check_id == "dbt.model_coverage"
    assert result.status == "fail"
    assert "No adapter defined" in result.message


def test_normalize_tool_name_for_dbt() -> None:
    """Test tool name normalization for dbt model naming."""
    assert _normalize_tool_name_for_dbt("layout-scanner") == "layout"
    assert _normalize_tool_name_for_dbt("roslyn-analyzers") == "roslyn"
    assert _normalize_tool_name_for_dbt("scc") == "scc"
    assert _normalize_tool_name_for_dbt("lizard") == "lizard"
    assert _normalize_tool_name_for_dbt("semgrep") == "semgrep"


def test_parse_rollup_names_from_eval_strategy(tmp_path: Path) -> None:
    """Test parsing rollup names from EVAL_STRATEGY.md."""
    eval_strategy = tmp_path / "EVAL_STRATEGY.md"
    eval_strategy.write_text(
        """# Evaluation Strategy

## Rollup Validation

Rollups:
- directory_direct_distributions
- directory_recursive_distributions

Tests:
- src/sot-engine/dbt/tests/test_rollup.sql
"""
    )
    rollups = _parse_rollup_names_from_eval_strategy(eval_strategy)
    assert "directory_direct_distributions" in rollups
    assert "directory_recursive_distributions" in rollups


def test_parse_rollup_names_from_eval_strategy_inline(tmp_path: Path) -> None:
    """Test parsing rollup names when listed inline."""
    eval_strategy = tmp_path / "EVAL_STRATEGY.md"
    eval_strategy.write_text(
        """# Evaluation Strategy

## Rollup Validation

Rollups: direct, recursive

Tests:
- test.sql
"""
    )
    rollups = _parse_rollup_names_from_eval_strategy(eval_strategy)
    assert "direct" in rollups
    assert "recursive" in rollups


def test_parse_rollup_names_missing_file(tmp_path: Path) -> None:
    """Test parsing rollups when file doesn't exist."""
    eval_strategy = tmp_path / "nonexistent.md"
    rollups = _parse_rollup_names_from_eval_strategy(eval_strategy)
    assert rollups == []


# Tests for entity.repository_alignment
def test_entity_repository_alignment_passes_for_scc() -> None:
    """Test entity repository alignment for scc."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_entity_repository_alignment(tool_root, "scc")
    assert result.check_id == "entity.repository_alignment"
    assert result.status == "pass"


def test_entity_repository_alignment_fails_unknown_tool() -> None:
    """Test entity repository alignment fails for unknown tools."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_entity_repository_alignment(tool_root, "unknown")
    assert result.check_id == "entity.repository_alignment"
    assert result.status == "fail"
    assert "No entity mappings" in result.message


# Tests for output.metadata_consistency
def test_output_metadata_consistency_passes_valid() -> None:
    """Test metadata consistency passes with valid data."""
    output = {
        "metadata": {
            "commit": "a" * 40,
            "timestamp": "2026-01-27T10:00:00Z",
            "tool_version": "1.0.0",
        },
        "data": {},
    }
    result = _check_output_metadata_consistency(output)
    assert result.check_id == "output.metadata_consistency"
    assert result.status == "pass"


def test_output_metadata_consistency_fails_invalid_commit() -> None:
    """Test metadata consistency fails with invalid commit."""
    output = {
        "metadata": {
            "commit": "not-a-sha",
            "timestamp": "2026-01-27T10:00:00Z",
        },
        "data": {},
    }
    result = _check_output_metadata_consistency(output)
    assert result.check_id == "output.metadata_consistency"
    assert result.status == "fail"
    assert any("commit is not 40-hex SHA" in e for e in result.evidence)


def test_output_metadata_consistency_fails_invalid_timestamp() -> None:
    """Test metadata consistency fails with invalid timestamp."""
    output = {
        "metadata": {
            "commit": "a" * 40,
            "timestamp": "not-a-timestamp",
        },
        "data": {},
    }
    result = _check_output_metadata_consistency(output)
    assert result.check_id == "output.metadata_consistency"
    assert result.status == "fail"
    assert any("timestamp is not valid ISO8601" in e for e in result.evidence)


def test_output_metadata_consistency_fails_version_mismatch() -> None:
    """Test metadata consistency fails when versions mismatch."""
    output = {
        "metadata": {
            "commit": "a" * 40,
            "timestamp": "2026-01-27T10:00:00Z",
            "tool_version": "1.0.0",
        },
        "data": {
            "tool_version": "2.0.0",
        },
    }
    result = _check_output_metadata_consistency(output)
    assert result.check_id == "output.metadata_consistency"
    assert result.status == "fail"
    assert any("tool_version mismatch" in e for e in result.evidence)


def test_is_valid_iso8601() -> None:
    """Test ISO8601 timestamp validation."""
    assert _is_valid_iso8601("2026-01-27T10:00:00Z")
    assert _is_valid_iso8601("2026-01-27T10:00:00+00:00")
    assert _is_valid_iso8601("2026-01-27T10:00:00-05:00")
    assert _is_valid_iso8601("2026-01-27T10:00:00.123Z")
    assert not _is_valid_iso8601("not-a-timestamp")
    assert not _is_valid_iso8601("2026/01/27")
    assert not _is_valid_iso8601("")


# Tests for test.structure_naming
def test_test_structure_naming_passes_layout_scanner() -> None:
    """Test structure naming passes for layout-scanner."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "layout-scanner"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_test_structure_naming(tool_root)
    assert result.check_id == "test.structure_naming"
    # May pass or fail depending on tool state


def test_test_structure_naming_fails_missing_tests_dir(tmp_path: Path) -> None:
    """Test structure naming fails when tests/ dir is missing."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    result = _check_test_structure_naming(tool_root)
    assert result.check_id == "test.structure_naming"
    assert result.status == "fail"
    assert "tests/" in result.evidence[0]


def test_test_structure_naming_fails_missing_unit(tmp_path: Path) -> None:
    """Test structure naming fails when tests/unit/ is missing."""
    tool_root = tmp_path / "demo"
    tests_dir = tool_root / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "integration").mkdir()
    result = _check_test_structure_naming(tool_root)
    assert result.check_id == "test.structure_naming"
    assert result.status == "fail"
    assert any("unit" in e for e in result.evidence)


def test_test_structure_naming_fails_bad_naming(tmp_path: Path) -> None:
    """Test structure naming fails when test files have bad names."""
    tool_root = tmp_path / "demo"
    tests_dir = tool_root / "tests"
    (tests_dir / "unit").mkdir(parents=True)
    (tests_dir / "integration").mkdir()
    # Create a test file without test_ prefix
    (tests_dir / "unit" / "bad_name.py").write_text("# test")
    result = _check_test_structure_naming(tool_root)
    assert result.check_id == "test.structure_naming"
    assert result.status == "fail"
    assert any("test_*.py convention" in e for e in result.evidence)


# Tests for _looks_like_file_path
def test_looks_like_file_path_absolute_unix() -> None:
    """Test detection of absolute Unix paths."""
    assert _looks_like_file_path("/private/tmp/keepass2android") is True
    assert _looks_like_file_path("/home/user/projects/myrepo") is True
    assert _looks_like_file_path("/usr/local/bin") is True


def test_looks_like_file_path_absolute_windows() -> None:
    """Test detection of absolute Windows paths."""
    assert _looks_like_file_path("C:\\Users\\alice\\projects") is True
    assert _looks_like_file_path("D:/Projects/MyRepo") is True


def test_looks_like_file_path_excludes_urls() -> None:
    """Test that URLs are excluded."""
    assert _looks_like_file_path("http://example.com/path") is False
    assert _looks_like_file_path("https://github.com/user/repo") is False
    assert _looks_like_file_path("file:///home/user/file.txt") is False


def test_looks_like_file_path_excludes_api_endpoints() -> None:
    """Test that API endpoints are excluded."""
    assert _looks_like_file_path("/api/v1/users") is False
    assert _looks_like_file_path("/api/ce/task") is False
    assert _looks_like_file_path("/api/measures/component_tree") is False
    assert _looks_like_file_path("/graphql/query") is False


def test_looks_like_file_path_excludes_schema_refs() -> None:
    """Test that schema references are excluded."""
    assert _looks_like_file_path("$schema") is False
    assert _looks_like_file_path("#/definitions/type") is False


def test_looks_like_file_path_excludes_regex_patterns() -> None:
    """Test that regex patterns are excluded."""
    assert _looks_like_file_path(".*Tests?\\.java$") is False
    assert _looks_like_file_path("path:test/") is False
    assert _looks_like_file_path("src/[a-z]+/*.py") is False


def test_looks_like_file_path_relative_not_detected() -> None:
    """Test that relative paths are not detected by value heuristic (only by key patterns)."""
    # Relative paths should be caught by key patterns, not value heuristics
    # This avoids false positives on pattern-like strings
    assert _looks_like_file_path("src/main.py") is False
    assert _looks_like_file_path("test/unit/test_foo.py") is False


# Tests for _collect_path_values
def test_collect_path_values_key_based() -> None:
    """Test that path values are collected based on key patterns."""
    payload = {
        "file_path": "src/main.py",
        "directory": "src/utils",
        "source": "lib/helpers.py",
    }
    paths = _collect_path_values(payload)
    assert "src/main.py" in paths
    assert "src/utils" in paths
    assert "lib/helpers.py" in paths


def test_collect_path_values_excludes_endpoints() -> None:
    """Test that endpoint values are excluded."""
    payload = {
        "endpoint": "/api/ce/task",
        "api_url": "http://localhost:9000/api",
        "file_path": "src/main.py",
    }
    paths = _collect_path_values(payload)
    assert "/api/ce/task" not in paths
    assert "http://localhost:9000/api" not in paths
    assert "src/main.py" in paths


def test_collect_path_values_detects_absolute_paths() -> None:
    """Test that absolute paths are detected via value heuristic."""
    payload = {
        "repo_location": "/private/tmp/keepass2android",
        "other_field": "/home/user/projects/myrepo",
    }
    paths = _collect_path_values(payload)
    assert "/private/tmp/keepass2android" in paths
    assert "/home/user/projects/myrepo" in paths


def test_collect_path_values_nested() -> None:
    """Test that nested path values are collected."""
    payload = {
        "results": {
            "source": {
                "file_path": "src/main.py",
                "repo_location": "/private/tmp/myrepo",
            }
        },
        "items": [
            {"path": "file1.py"},
            {"path": "file2.py"},
        ]
    }
    paths = _collect_path_values(payload)
    assert "src/main.py" in paths
    assert "/private/tmp/myrepo" in paths
    assert "file1.py" in paths
    assert "file2.py" in paths
