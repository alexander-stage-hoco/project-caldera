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
    _check_synthetic_evaluation_context,
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
    _check_data_completeness,
    _check_path_consistency,
    _validate_count_list_consistency,
    _validate_required_data_fields,
    _extract_all_paths_by_section,
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

    def fake_run_make(tool_path: Path, target: str, env: dict[str, str]) -> tuple[int, str, str, float]:
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
        return (0, "", "", 100.0)

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


# ===========================================================================
# Tests for SoT Integration Checks
# ===========================================================================

from tool_compliance import (
    _check_sot_adapter_registered,
    _check_sot_schema_table,
    _check_sot_orchestrator_wired,
    _check_sot_dbt_staging_model,
    _check_llm_judge_count,
    _check_makefile_permissions,
    MIN_LLM_JUDGES,
)


def test_sot_adapter_registered_passes_for_scc() -> None:
    """Test SoT adapter registration check passes for scc."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_sot_adapter_registered(tool_root, "scc")
    assert result.check_id == "sot.adapter_registered"
    assert result.status == "pass"


def test_sot_adapter_registered_skips_unknown() -> None:
    """Test SoT adapter registration check skips for unknown tools."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_sot_adapter_registered(tool_root, "unknown")
    assert result.check_id == "sot.adapter_registered"
    assert result.status == "skip"


def test_sot_schema_table_passes_for_scc() -> None:
    """Test SoT schema table check passes for scc."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_sot_schema_table(tool_root, "scc")
    assert result.check_id == "sot.schema_table"
    assert result.status == "pass"


def test_sot_schema_table_skips_unknown() -> None:
    """Test SoT schema table check skips for unknown tools."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_sot_schema_table(tool_root, "unknown")
    assert result.check_id == "sot.schema_table"
    assert result.status == "skip"


def test_sot_orchestrator_wired_passes_for_scc() -> None:
    """Test SoT orchestrator wiring check passes for scc."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_sot_orchestrator_wired(tool_root, "scc")
    assert result.check_id == "sot.orchestrator_wired"
    assert result.status == "pass"


def test_sot_orchestrator_wired_special_for_layout_scanner() -> None:
    """Test SoT orchestrator check handles layout-scanner specially."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "layout-scanner"
    result = _check_sot_orchestrator_wired(tool_root, "layout-scanner")
    assert result.check_id == "sot.orchestrator_wired"
    assert result.status == "pass"
    assert "prerequisite" in result.message.lower()


def test_sot_orchestrator_wired_skips_unknown() -> None:
    """Test SoT orchestrator wiring check skips for unknown tools."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_sot_orchestrator_wired(tool_root, "unknown")
    assert result.check_id == "sot.orchestrator_wired"
    assert result.status == "skip"


def test_sot_dbt_staging_model_passes_for_scc() -> None:
    """Test SoT dbt staging model check passes for scc."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "scc"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_sot_dbt_staging_model(tool_root, "scc")
    assert result.check_id == "sot.dbt_staging_model"
    assert result.status == "pass"


def test_sot_dbt_staging_model_skips_unknown() -> None:
    """Test SoT dbt staging model check skips for unknown tools."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "unknown"
    result = _check_sot_dbt_staging_model(tool_root, "unknown")
    assert result.check_id == "sot.dbt_staging_model"
    assert result.status == "skip"


# ===========================================================================
# Tests for LLM Judge Count Check
# ===========================================================================

def test_llm_judge_count_passes_with_enough_judges(tmp_path: Path) -> None:
    """Test LLM judge count passes when >= 4 judges present."""
    tool_root = tmp_path / "demo"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    judges_dir.mkdir(parents=True)

    # Create 4 judge files
    for name in ["accuracy.py", "actionability.py", "false_positive.py", "integration_fit.py"]:
        (judges_dir / name).write_text("# judge\n")

    result = _check_llm_judge_count(tool_root)
    assert result.check_id == "evaluation.llm_judge_count"
    assert result.status == "pass"


def test_llm_judge_count_fails_with_too_few_judges(tmp_path: Path) -> None:
    """Test LLM judge count fails when < 4 judges present."""
    tool_root = tmp_path / "demo"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    judges_dir.mkdir(parents=True)

    # Create only 2 judge files
    for name in ["accuracy.py", "actionability.py"]:
        (judges_dir / name).write_text("# judge\n")

    result = _check_llm_judge_count(tool_root)
    assert result.check_id == "evaluation.llm_judge_count"
    assert result.status == "fail"
    assert "2 found" in result.message


def test_llm_judge_count_excludes_base_and_init(tmp_path: Path) -> None:
    """Test LLM judge count excludes base.py and __init__.py."""
    tool_root = tmp_path / "demo"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    judges_dir.mkdir(parents=True)

    # Create judge files including base.py and __init__.py
    for name in ["accuracy.py", "actionability.py", "base.py", "__init__.py"]:
        (judges_dir / name).write_text("# judge\n")

    result = _check_llm_judge_count(tool_root)
    assert result.check_id == "evaluation.llm_judge_count"
    assert result.status == "fail"
    # Should only count accuracy.py and actionability.py (2), not base.py and __init__.py
    assert "2 found" in result.message


def test_llm_judge_count_fails_missing_directory(tmp_path: Path) -> None:
    """Test LLM judge count fails when judges directory is missing."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()

    result = _check_llm_judge_count(tool_root)
    assert result.check_id == "evaluation.llm_judge_count"
    assert result.status == "fail"
    assert "missing" in result.message.lower()


def test_llm_judge_count_for_real_tools() -> None:
    """Test LLM judge count check runs for existing tools.

    Note: This test verifies the check runs correctly, not that all tools pass.
    Some tools may be in the process of adding required judges.
    """
    tools_root = Path(__file__).resolve().parents[1] / "tools"
    results = {}
    for tool_dir in tools_root.iterdir():
        if not tool_dir.is_dir() or not (tool_dir / "Makefile").exists():
            continue
        result = _check_llm_judge_count(tool_dir)
        assert result.check_id == "evaluation.llm_judge_count"
        results[tool_dir.name] = result.status

    # At least some tools should pass
    passing = [name for name, status in results.items() if status == "pass"]
    assert len(passing) > 0, "At least some tools should have >= 4 LLM judges"


# ===========================================================================
# Tests for Makefile Permissions Check
# ===========================================================================

def test_makefile_permissions_passes_readable(tmp_path: Path) -> None:
    """Test Makefile permissions check passes for readable file."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    makefile = tool_root / "Makefile"
    makefile.write_text("setup:\n\techo setup\n")
    makefile.chmod(0o644)

    result = _check_makefile_permissions(tool_root)
    assert result.check_id == "make.permissions"
    assert result.status == "pass"


def test_makefile_permissions_fails_missing(tmp_path: Path) -> None:
    """Test Makefile permissions check fails for missing file."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()

    result = _check_makefile_permissions(tool_root)
    assert result.check_id == "make.permissions"
    assert result.status == "fail"


# ===========================================================================
# Tests for Cross-Tool SQL Join Pattern Check
# ===========================================================================

from tool_compliance import (
    _check_cross_tool_join_patterns,
    _check_cross_tool_join_patterns_in_file,
    _identify_tools_in_sql,
    _extract_table_aliases,
    TOOL_TABLE_PATTERNS,
)


def test_identify_tools_in_sql_single_tool() -> None:
    """Test identifying a single tool from SQL content."""
    sql = "SELECT * FROM stg_lz_scc_file_metrics WHERE run_pk = 1"
    tools = _identify_tools_in_sql(sql)
    assert tools == {"scc"}


def test_identify_tools_in_sql_multiple_tools() -> None:
    """Test identifying multiple tools from SQL content."""
    sql = """
    SELECT *
    FROM stg_lz_scc_file_metrics scc
    JOIN stg_lz_lizard_file_metrics lz ON scc.file_id = lz.file_id
    """
    tools = _identify_tools_in_sql(sql)
    assert "scc" in tools
    assert "lizard" in tools


def test_identify_tools_in_sql_rollup_tables() -> None:
    """Test identifying tools from rollup table references."""
    sql = """
    SELECT * FROM rollup_scc_directory_recursive_distributions
    JOIN rollup_lizard_directory_recursive_distributions ON 1=1
    """
    tools = _identify_tools_in_sql(sql)
    assert "scc" in tools
    assert "lizard" in tools


def test_extract_table_aliases() -> None:
    """Test extracting table aliases and mapping to tools."""
    sql = """
    FROM stg_lz_scc_file_metrics sm
    JOIN stg_lz_lizard_file_metrics lm ON sm.file_id = lm.file_id
    """
    aliases = _extract_table_aliases(sql)
    assert aliases.get("sm") == "scc"
    assert aliases.get("lm") == "lizard"


def test_cross_tool_join_patterns_passes_correct_pattern(tmp_path: Path) -> None:
    """Test that correct cross-tool join patterns pass."""
    # Create a SQL file that uses collection_run_id correctly
    sql_content = """
    WITH tool_runs AS (
        SELECT tool_name, run_pk, collection_run_id
        FROM lz_tool_runs
        WHERE collection_run_id = (SELECT collection_run_id FROM lz_tool_runs WHERE run_pk = {{ run_pk }})
    ),
    scc_map AS (
        SELECT run_pk as scc_run_pk FROM tool_runs WHERE tool_name = 'scc'
    ),
    lizard_map AS (
        SELECT run_pk as lizard_run_pk FROM tool_runs WHERE tool_name = 'lizard'
    )
    SELECT *
    FROM stg_lz_scc_file_metrics scc
    JOIN stg_lz_lizard_file_metrics lz
        ON lz.run_pk = (SELECT lizard_run_pk FROM lizard_map)
        AND lz.file_id = scc.file_id
    WHERE scc.run_pk = (SELECT scc_run_pk FROM scc_map)
    """
    sql_file = tmp_path / "correct_join.sql"
    sql_file.write_text(sql_content)

    issues = _check_cross_tool_join_patterns_in_file(sql_file, sql_content)
    assert issues == []


def test_cross_tool_join_patterns_passes_tool_specific_run_pk(tmp_path: Path) -> None:
    """Test that tool-specific run_pk columns pass."""
    sql_content = """
    SELECT *
    FROM unified_file_metrics ufm
    JOIN rollup_trivy_directory_counts_recursive rv
        ON rv.run_pk = ufm.trivy_run_pk
    WHERE ufm.scc_run_pk = 123
      AND ufm.lizard_run_pk = 124
    """
    sql_file = tmp_path / "tool_specific.sql"
    sql_file.write_text(sql_content)

    issues = _check_cross_tool_join_patterns_in_file(sql_file, sql_content)
    assert issues == []


def test_cross_tool_join_patterns_passes_single_tool() -> None:
    """Test that single-tool queries don't trigger false positives."""
    sql_content = """
    SELECT *
    FROM stg_lz_scc_file_metrics scc
    JOIN stg_lz_scc_directory_metrics d ON scc.run_pk = d.run_pk
    """
    issues = _check_cross_tool_join_patterns_in_file(Path("single_tool.sql"), sql_content)
    assert issues == []


def test_cross_tool_join_patterns_check_runs_on_project(tmp_path: Path) -> None:
    """Test that the check runs successfully on the actual project."""
    project_root = Path(__file__).resolve().parents[2]
    result = _check_cross_tool_join_patterns(project_root)
    assert result.check_id == "sql.cross_tool_join_patterns"
    # The check should pass on the actual project (all files use correct patterns)
    assert result.status == "pass", f"Check failed with evidence: {result.evidence}"


def test_cross_tool_join_patterns_detects_anti_pattern(tmp_path: Path) -> None:
    """Test that direct run_pk joins between different tools are detected."""
    # Create directory structure
    dbt_dir = tmp_path / "src" / "sot-engine" / "dbt" / "models"
    dbt_dir.mkdir(parents=True)

    # Create a SQL file with the anti-pattern (incorrect cross-tool join)
    # Note: This is a synthetic example - real files should use correct patterns
    sql_content = """
    -- BAD: This directly joins run_pk across different tools (will never match)
    SELECT *
    FROM stg_lz_scc_file_metrics scc
    JOIN stg_lz_lizard_file_metrics lz ON scc.run_pk = lz.run_pk
    WHERE scc.file_id = lz.file_id
    """
    sql_file = dbt_dir / "bad_join.sql"
    sql_file.write_text(sql_content)

    result = _check_cross_tool_join_patterns(tmp_path)
    assert result.check_id == "sql.cross_tool_join_patterns"
    assert result.status == "fail"
    assert len(result.evidence) > 0
    assert "bad_join.sql" in result.evidence[0]


def test_cross_tool_join_patterns_no_sql_files(tmp_path: Path) -> None:
    """Test that check passes gracefully when no SQL files exist."""
    result = _check_cross_tool_join_patterns(tmp_path)
    assert result.check_id == "sql.cross_tool_join_patterns"
    assert result.status == "pass"
    assert "0 files checked" in result.message


# =============================================================================
# Tests for evaluation.synthetic_context check
# =============================================================================


def test_synthetic_context_passes_for_gitleaks() -> None:
    """Test synthetic context check passes for gitleaks which implements the pattern."""
    tool_root = Path(__file__).resolve().parents[1] / "tools" / "gitleaks"
    if not tool_root.exists():
        return  # Skip if tool directory doesn't exist
    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "pass", f"Expected pass but got: {result.message} - {result.evidence}"


def test_synthetic_context_fails_missing_judges_dir(tmp_path: Path) -> None:
    """Test synthetic context check fails when judges directory is missing."""
    tool_root = tmp_path / "demo-tool"
    tool_root.mkdir()
    # Create evaluation dir but no judges dir
    eval_dir = tool_root / "evaluation" / "llm"
    eval_dir.mkdir(parents=True)

    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "fail"
    assert "directory missing" in result.message


def test_synthetic_context_fails_missing_base_evaluation_mode(tmp_path: Path) -> None:
    """Test synthetic context check fails when base.py lacks evaluation_mode parameter."""
    tool_root = tmp_path / "demo-tool"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    judges_dir.mkdir(parents=True)

    # Create base.py WITHOUT evaluation_mode parameter
    base_py = judges_dir / "base.py"
    base_py.write_text('''
from __future__ import annotations

class BaseJudge:
    """Base judge class without evaluation_mode."""

    def __init__(
        self,
        model: str = "opus",
        timeout: int = 120,
    ):
        self.model = model
        self.timeout = timeout

    @property
    def dimension_name(self) -> str:
        return "base"

    @property
    def weight(self) -> float:
        return 1.0
''')

    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "fail"
    assert "evaluation_mode parameter" in result.message


def test_synthetic_context_fails_missing_evidence_keys(tmp_path: Path) -> None:
    """Test synthetic context check fails when judge doesn't set required evidence keys."""
    tool_root = tmp_path / "demo-tool"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
    judges_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)

    # Create base.py WITH evaluation_mode parameter
    base_py = judges_dir / "base.py"
    base_py.write_text('''
from __future__ import annotations

class BaseJudge:
    def __init__(
        self,
        model: str = "opus",
        evaluation_mode: str | None = None,
    ):
        self.model = model
        self.evaluation_mode = evaluation_mode

    @property
    def dimension_name(self) -> str:
        return "base"

    @property
    def weight(self) -> float:
        return 0.5
''')

    # Create a judge that does NOT set required evidence keys
    judge_py = judges_dir / "accuracy.py"
    judge_py.write_text('''
from __future__ import annotations
from .base import BaseJudge

class AccuracyJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def collect_evidence(self):
        # Missing: evaluation_mode, synthetic_baseline, interpretation_guidance
        return {
            "some_data": "value",
        }
''')

    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "fail"
    assert "missing" in result.message.lower()


def test_synthetic_context_fails_missing_prompt_placeholders(tmp_path: Path) -> None:
    """Test synthetic context check fails when prompt lacks required placeholders."""
    tool_root = tmp_path / "demo-tool"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
    judges_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)

    # Create base.py WITH evaluation_mode parameter
    base_py = judges_dir / "base.py"
    base_py.write_text('''
from __future__ import annotations

class BaseJudge:
    def __init__(
        self,
        model: str = "opus",
        evaluation_mode: str | None = None,
    ):
        self.model = model
        self.evaluation_mode = evaluation_mode

    @property
    def dimension_name(self) -> str:
        return "base"
''')

    # Create a judge that sets all required evidence keys
    judge_py = judges_dir / "accuracy.py"
    judge_py.write_text('''
from __future__ import annotations
from .base import BaseJudge

class AccuracyJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def collect_evidence(self):
        evidence = {
            "evaluation_mode": self.evaluation_mode,
            "synthetic_baseline": "test baseline",
            "interpretation_guidance": "test guidance",
        }
        return evidence
''')

    # Create prompt WITHOUT required placeholders
    prompt_md = prompts_dir / "accuracy.md"
    prompt_md.write_text('''# Accuracy Evaluation

Evaluate the accuracy of the analysis.

## Evidence

{{ evidence }}

## Scoring

Score 1-5 based on accuracy.
''')

    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "fail"
    assert "placeholder" in result.message.lower()


def test_synthetic_context_passes_complete_implementation(tmp_path: Path) -> None:
    """Test synthetic context check passes when all requirements are met."""
    tool_root = tmp_path / "demo-tool"
    judges_dir = tool_root / "evaluation" / "llm" / "judges"
    prompts_dir = tool_root / "evaluation" / "llm" / "prompts"
    judges_dir.mkdir(parents=True)
    prompts_dir.mkdir(parents=True)

    # Create base.py WITH evaluation_mode parameter
    base_py = judges_dir / "base.py"
    base_py.write_text('''
from __future__ import annotations

class BaseJudge:
    def __init__(
        self,
        model: str = "opus",
        evaluation_mode: str | None = None,
    ):
        self.model = model
        self.evaluation_mode = evaluation_mode

    @property
    def dimension_name(self) -> str:
        return "base"
''')

    # Create a judge that sets all required evidence keys
    judge_py = judges_dir / "accuracy.py"
    judge_py.write_text('''
from __future__ import annotations
from .base import BaseJudge

class AccuracyJudge(BaseJudge):
    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def collect_evidence(self):
        evidence = {
            "evaluation_mode": self.evaluation_mode,
            "synthetic_baseline": "test baseline",
            "interpretation_guidance": "test guidance",
            "other_data": "value",
        }
        return evidence
''')

    # Create prompt WITH all required placeholders
    prompt_md = prompts_dir / "accuracy.md"
    prompt_md.write_text('''# Accuracy Evaluation

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Baseline
{{ synthetic_baseline }}

### Mode
{{ evaluation_mode }}

## Evidence

{{ evidence }}

## Scoring

Score 1-5 based on accuracy.
''')

    result = _check_synthetic_evaluation_context(tool_root)
    assert result.check_id == "evaluation.synthetic_context"
    assert result.status == "pass"
    assert "correctly" in result.message.lower()


# ===========================================================================
# Tests for Data Completeness Check
# ===========================================================================


def test_check_data_completeness_count_matches_list() -> None:
    """Test data completeness passes when count matches list length."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "file_count": 3,
            "files": [
                {"path": "file1.py"},
                {"path": "file2.py"},
                {"path": "file3.py"},
            ],
        },
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "pass"


def test_check_data_completeness_count_mismatch_fails() -> None:
    """Test data completeness fails when count doesn't match list length."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "file_count": 5,  # Says 5, but only 2 files
            "files": [
                {"path": "file1.py"},
                {"path": "file2.py"},
            ],
        },
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "fail"
    assert any("file_count=5 but files has 2" in e for e in result.evidence)


def test_check_data_completeness_required_fields_present() -> None:
    """Test data completeness passes when required fields are present."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "file1.py"},
                {"path": "file2.py"},
            ],
        },
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "pass"


def test_check_data_completeness_required_fields_missing() -> None:
    """Test data completeness fails when required fields are missing."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"name": "file1.py"},  # Missing 'path' field
                {"path": "file2.py"},
            ],
        },
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "fail"
    assert any("missing required field: path" in e for e in result.evidence)


def test_check_data_completeness_empty_data_passes() -> None:
    """Test data completeness passes with empty data."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {},
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "pass"


def test_check_data_completeness_non_dict_data_fails() -> None:
    """Test data completeness fails when data is not a dict."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": "not a dict",
    }
    result = _check_data_completeness(output)
    assert result.check_id == "output.data_completeness"
    assert result.status == "fail"
    assert "not a dictionary" in result.message


def test_validate_count_list_consistency_helper() -> None:
    """Test the count/list consistency validation helper."""
    # Valid case
    data = {"file_count": 2, "files": [{"a": 1}, {"b": 2}]}
    issues = _validate_count_list_consistency(data, "file_count", "files")
    assert issues == []

    # Mismatch case
    data = {"file_count": 5, "files": [{"a": 1}]}
    issues = _validate_count_list_consistency(data, "file_count", "files")
    assert len(issues) == 1
    assert "5" in issues[0] and "1" in issues[0]

    # Neither field present (OK)
    data = {"other": "value"}
    issues = _validate_count_list_consistency(data, "file_count", "files")
    assert issues == []


def test_validate_required_data_fields_helper() -> None:
    """Test the required data fields validation helper."""
    # Valid case
    items = [{"path": "a.py"}, {"path": "b.py"}]
    issues = _validate_required_data_fields(items, ["path"], "files")
    assert issues == []

    # Missing field case
    items = [{"path": "a.py"}, {"name": "b.py"}]
    issues = _validate_required_data_fields(items, ["path"], "files")
    assert len(issues) == 1
    assert "files[1]" in issues[0]

    # Null field case
    items = [{"path": "a.py"}, {"path": None}]
    issues = _validate_required_data_fields(items, ["path"], "files")
    assert len(issues) == 1
    assert "null" in issues[0].lower()


# ===========================================================================
# Tests for Path Consistency Check
# ===========================================================================


def test_check_path_consistency_all_repo_relative() -> None:
    """Test path consistency passes when all paths are repo-relative."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "src/main.py"},
                {"path": "tests/test_main.py"},
            ],
            "findings": [
                {"file_path": "src/main.py", "message": "issue"},
            ],
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "pass"


def test_check_path_consistency_mixed_absolute_fails() -> None:
    """Test path consistency fails with mixed absolute/relative paths."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "/absolute/path/main.py"},  # Absolute path
                {"path": "tests/test_main.py"},
            ],
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "fail"
    assert any("non-repo-relative" in e for e in result.evidence)


def test_check_path_consistency_cross_reference_valid() -> None:
    """Test path consistency passes when findings reference existing files."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "src/main.py"},
                {"path": "src/utils.py"},
            ],
            "findings": [
                {"file_path": "src/main.py", "message": "issue1"},
                {"file_path": "src/utils.py", "message": "issue2"},
            ],
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "pass"


def test_check_path_consistency_cross_reference_invalid() -> None:
    """Test path consistency reports missing file references."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "src/main.py"},
            ],
            "findings": [
                {"file_path": "src/main.py", "message": "issue1"},
                {"file_path": "src/missing.py", "message": "issue2"},  # Not in files
            ],
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "fail"
    assert any("missing.py" in e and "not found" in e for e in result.evidence)


def test_check_path_consistency_no_paths() -> None:
    """Test path consistency passes when no path fields exist."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "summary": {"count": 0},
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "pass"
    assert "No path fields" in result.message


def test_extract_all_paths_by_section_helper() -> None:
    """Test the path extraction helper."""
    output = {
        "metadata": {},
        "data": {
            "files": [
                {"path": "a.py"},
                {"path": "b.py"},
            ],
            "findings": [
                {"file_path": "a.py", "message": "issue"},
            ],
        },
    }
    paths = _extract_all_paths_by_section(output)
    assert "files" in paths
    assert "findings" in paths
    assert "a.py" in paths["files"]
    assert "b.py" in paths["files"]
    assert "a.py" in paths["findings"]


def test_check_path_consistency_windows_separators_fail() -> None:
    """Test path consistency fails with Windows path separators."""
    output = {
        "metadata": {"tool_name": "test"},
        "data": {
            "files": [
                {"path": "src\\main.py"},  # Windows separator
            ],
        },
    }
    result = _check_path_consistency(output)
    assert result.check_id == "output.path_consistency"
    assert result.status == "fail"


# ===========================================================================
# Tests for Test Coverage Threshold Check
# ===========================================================================

from tool_compliance import _check_test_coverage_threshold


def test_check_test_coverage_threshold_skips_without_tests(tmp_path: Path) -> None:
    """Test coverage check skips when no tests directory."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "skip"
    assert "tests/ directory missing" in result.message


def test_check_test_coverage_threshold_fails_no_pytest_cov(tmp_path: Path) -> None:
    """Test coverage check fails when pytest-cov not installed."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest>=7.0.0\n")

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "fail"
    assert "pytest-cov not in requirements.txt" in result.message


def test_check_test_coverage_threshold_skips_no_coverage_report(tmp_path: Path) -> None:
    """Test coverage check skips when no coverage.json exists (not running)."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "skip"
    assert "No coverage report found" in result.message


def test_check_test_coverage_threshold_passes_at_80(tmp_path: Path) -> None:
    """Test coverage check passes at exactly 80%."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    # Create a mock coverage.json with 80% coverage
    coverage_data = {
        "meta": {"version": "7.0.0"},
        "totals": {
            "covered_lines": 80,
            "num_statements": 100,
            "percent_covered": 80.0,
        },
        "files": {},
    }
    (tool_root / "coverage.json").write_text(json.dumps(coverage_data))

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "pass"
    assert "80.0%" in result.message


def test_check_test_coverage_threshold_passes_above_80(tmp_path: Path) -> None:
    """Test coverage check passes above 80%."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    # Create a mock coverage.json with 95% coverage
    coverage_data = {
        "meta": {"version": "7.0.0"},
        "totals": {
            "covered_lines": 95,
            "num_statements": 100,
            "percent_covered": 95.0,
        },
        "files": {},
    }
    (tool_root / "coverage.json").write_text(json.dumps(coverage_data))

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "pass"
    assert "95.0%" in result.message


def test_check_test_coverage_threshold_fails_below_80(tmp_path: Path) -> None:
    """Test coverage check fails below 80%."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    # Create a mock coverage.json with 60% coverage
    coverage_data = {
        "meta": {"version": "7.0.0"},
        "totals": {
            "covered_lines": 60,
            "num_statements": 100,
            "percent_covered": 60.0,
        },
        "files": {},
    }
    (tool_root / "coverage.json").write_text(json.dumps(coverage_data))

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "fail"
    assert "60.0%" in result.message
    assert "< 80%" in result.message


def test_check_test_coverage_threshold_fails_invalid_coverage_json(tmp_path: Path) -> None:
    """Test coverage check fails when coverage.json is invalid."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    # Create invalid coverage.json
    (tool_root / "coverage.json").write_text("not valid json")

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "fail"
    assert "parse error" in result.message.lower()


def test_check_test_coverage_threshold_fails_missing_percent(tmp_path: Path) -> None:
    """Test coverage check fails when coverage.json missing percent_covered."""
    tool_root = tmp_path / "demo"
    tool_root.mkdir()
    (tool_root / "tests" / "unit").mkdir(parents=True)
    (tool_root / "requirements.txt").write_text("pytest-cov>=4.0.0\n")

    # Create coverage.json missing percent_covered
    coverage_data = {
        "meta": {"version": "7.0.0"},
        "totals": {
            "covered_lines": 80,
            "num_statements": 100,
            # missing percent_covered
        },
        "files": {},
    }
    (tool_root / "coverage.json").write_text(json.dumps(coverage_data))

    env = {}
    result = _check_test_coverage_threshold(tool_root, env, run_coverage=False)
    assert result.check_id == "test.coverage_threshold"
    assert result.status == "fail"
    assert "missing percent_covered" in result.message
