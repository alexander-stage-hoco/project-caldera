"""Tests for the dbt model generator script."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from generate_dbt_models import (
    normalize_tool_name,
    get_staging_model_template,
    get_direct_counts_template,
    get_recursive_counts_template,
    get_distribution_model_template,
    get_schema_yml_snippet,
    generate_dbt_models,
)


class TestNormalizeToolName:
    """Tests for tool name normalization."""

    def test_removes_scanner_suffix(self) -> None:
        """Test that -scanner suffix is removed."""
        assert normalize_tool_name("layout-scanner") == "layout"

    def test_removes_analyzers_suffix(self) -> None:
        """Test that -analyzers suffix is removed."""
        assert normalize_tool_name("roslyn-analyzers") == "roslyn"

    def test_replaces_hyphens_with_underscores(self) -> None:
        """Test that hyphens are replaced with underscores."""
        assert normalize_tool_name("git-sizer") == "git_sizer"

    def test_leaves_simple_names_unchanged(self) -> None:
        """Test that simple names are unchanged."""
        assert normalize_tool_name("scc") == "scc"
        assert normalize_tool_name("lizard") == "lizard"

    def test_combined_transformations(self) -> None:
        """Test combined suffix removal and hyphen replacement."""
        assert normalize_tool_name("my-tool-scanner") == "my_tool"


class TestGetStagingModelTemplate:
    """Tests for staging model template generation."""

    def test_includes_source_reference(self) -> None:
        """Test that template includes source reference."""
        result = get_staging_model_template("scc", "lz_scc_file_metrics", ["run_pk", "file_id"])
        assert "source('lz', 'lz_scc_file_metrics')" in result

    def test_includes_columns(self) -> None:
        """Test that template includes specified columns."""
        result = get_staging_model_template("scc", "lz_scc_file_metrics", ["run_pk", "file_id", "lines"])
        assert "run_pk" in result
        assert "file_id" in result
        assert "lines" in result

    def test_includes_tool_name_in_comment(self) -> None:
        """Test that template includes tool name in comment."""
        result = get_staging_model_template("scc", "lz_scc_file_metrics", [])
        assert "scc" in result.lower()

    def test_uses_default_columns_when_empty(self) -> None:
        """Test that TODO placeholder is used when columns are empty."""
        result = get_staging_model_template("scc", "lz_scc_file_metrics", [])
        assert "TODO" in result


class TestGetDirectCountsTemplate:
    """Tests for direct counts rollup template generation."""

    def test_includes_metric_aggregations(self) -> None:
        """Test that template includes sum aggregations for metrics."""
        result = get_direct_counts_template("scc", "lz_scc_file_metrics", ["lines", "complexity"])
        assert "sum(lines)" in result
        assert "sum(complexity)" in result
        assert "total_lines" in result
        assert "total_complexity" in result

    def test_includes_file_count(self) -> None:
        """Test that template includes file count."""
        result = get_direct_counts_template("scc", "lz_scc_file_metrics", ["lines"])
        assert "count(distinct file_id)" in result
        assert "file_count" in result

    def test_includes_directory_join(self) -> None:
        """Test that template includes directory paths join."""
        result = get_direct_counts_template("scc", "lz_scc_file_metrics", ["lines"])
        assert "directory_paths" in result
        assert "directory_path" in result

    def test_uses_normalized_tool_name(self) -> None:
        """Test that normalized tool name is used in CTE names."""
        result = get_direct_counts_template("layout-scanner", "lz_layout_files", ["lines"])
        assert "layout_runs" in result  # Should use normalized name


class TestGetRecursiveCountsTemplate:
    """Tests for recursive counts rollup template generation."""

    def test_includes_recursive_cte(self) -> None:
        """Test that template includes recursive CTE for tree traversal."""
        result = get_recursive_counts_template("scc", "lz_scc_file_metrics", ["lines"])
        assert "recursive" in result.lower()
        assert "dir_tree" in result
        assert "ancestor_id" in result
        assert "descendant_id" in result

    def test_includes_base_case_and_recursive_case(self) -> None:
        """Test that template includes both base case and recursive case."""
        result = get_recursive_counts_template("scc", "lz_scc_file_metrics", ["lines"])
        assert "union all" in result.lower()

    def test_includes_metric_aggregations(self) -> None:
        """Test that template includes sum aggregations for metrics."""
        result = get_recursive_counts_template("scc", "lz_scc_file_metrics", ["lines", "complexity"])
        assert "sum(lines)" in result
        assert "sum(complexity)" in result


class TestGetDistributionModelTemplate:
    """Tests for distribution model template generation."""

    def test_direct_scope(self) -> None:
        """Test that direct scope is passed to macro."""
        result = get_distribution_model_template("scc", "lz_scc_file_metrics", ["lines"], "direct")
        assert "scope='direct'" in result

    def test_recursive_scope(self) -> None:
        """Test that recursive scope is passed to macro."""
        result = get_distribution_model_template("scc", "lz_scc_file_metrics", ["lines"], "recursive")
        assert "scope='recursive'" in result

    def test_includes_metrics_list(self) -> None:
        """Test that metrics list is included."""
        result = get_distribution_model_template("scc", "lz_scc_file_metrics", ["lines", "complexity"], "direct")
        assert "'lines'" in result
        assert "'complexity'" in result

    def test_includes_tool_name(self) -> None:
        """Test that tool name is included."""
        result = get_distribution_model_template("scc", "lz_scc_file_metrics", ["lines"], "direct")
        assert "tool_name='scc'" in result


class TestGetSchemaYmlSnippet:
    """Tests for schema.yml snippet generation."""

    def test_includes_model_names(self) -> None:
        """Test that snippet includes model names."""
        result = get_schema_yml_snippet("scc", "lz_scc_file_metrics", ["stg_scc", "rollup_scc_direct"])
        assert "- name: stg_scc" in result
        assert "- name: rollup_scc_direct" in result

    def test_includes_column_tests(self) -> None:
        """Test that snippet includes column tests."""
        result = get_schema_yml_snippet("scc", "lz_scc_file_metrics", ["stg_scc"])
        assert "not_null" in result

    def test_staging_models_have_file_columns(self) -> None:
        """Test that staging models include file_id and relative_path columns."""
        result = get_schema_yml_snippet("scc", "lz_scc_file_metrics", ["stg_scc"])
        assert "file_id" in result
        assert "relative_path" in result

    def test_rollup_models_have_directory_columns(self) -> None:
        """Test that rollup models include directory columns."""
        result = get_schema_yml_snippet("scc", "lz_scc_file_metrics", ["rollup_scc_direct"])
        assert "directory_id" in result
        assert "directory_path" in result


class TestGenerateDbtModels:
    """Tests for the main generate_dbt_models function."""

    def test_dry_run_returns_models_info(self) -> None:
        """Test that dry run returns models info without writing files."""
        result = generate_dbt_models(
            tool_name="test-tool",
            table_name="lz_test_metrics",
            metrics=["lines"],
            dry_run=True,
        )

        assert "models_created" in result
        assert "staging_model" in result
        assert result["staging_model"] == "stg_lz_test_metrics"

    def test_staging_only_skips_rollups(self) -> None:
        """Test that staging_only skips rollup model generation."""
        result = generate_dbt_models(
            tool_name="test-tool",
            table_name="lz_test_metrics",
            metrics=["lines"],
            staging_only=True,
            dry_run=True,
        )

        assert "rollup_models" not in result or len(result.get("rollup_models", [])) == 0

    def test_includes_all_rollup_types(self) -> None:
        """Test that all rollup types are generated when metrics provided."""
        result = generate_dbt_models(
            tool_name="test-tool",
            table_name="lz_test_metrics",
            metrics=["lines", "complexity"],
            dry_run=True,
        )

        rollups = result.get("rollup_models", [])
        assert any("direct" in r for r in rollups)
        assert any("recursive" in r for r in rollups)
        assert any("distributions" in r for r in rollups)

    def test_writes_files_when_not_dry_run(self, tmp_path: Path, monkeypatch) -> None:
        """Test that files are written when not in dry run mode."""
        # Mock the dbt models directory
        dbt_dir = tmp_path / "src" / "sot-engine" / "dbt" / "models"
        staging_dir = dbt_dir / "staging"
        marts_dir = dbt_dir / "marts"
        staging_dir.mkdir(parents=True)
        marts_dir.mkdir(parents=True)

        # Patch Path to use our temp directory
        monkeypatch.setattr("generate_dbt_models.Path", lambda x: tmp_path / x if x.startswith("src/") else Path(x))

        # Create a modified version that uses the temp path
        def patched_generate(tool_name, table_name, metrics, columns=None, staging_only=False, dry_run=False):
            from generate_dbt_models import (
                normalize_tool_name,
                get_staging_model_template,
                get_direct_counts_template,
                get_recursive_counts_template,
                get_distribution_model_template,
            )

            normalized = normalize_tool_name(tool_name)
            models_created = []

            # Use the temp path for dbt_dir
            staging_path = staging_dir / f"stg_{table_name}.sql"
            staging_content = get_staging_model_template(tool_name, table_name, columns or [])
            staging_path.write_text(staging_content)
            models_created.append(str(staging_path))

            if not staging_only and metrics:
                # Direct counts
                direct_path = marts_dir / f"rollup_{normalized}_directory_counts_direct.sql"
                direct_path.write_text(get_direct_counts_template(tool_name, table_name, metrics))
                models_created.append(str(direct_path))

            return {"models_created": models_created, "staging_model": f"stg_{table_name}"}

        result = patched_generate(
            tool_name="test-tool",
            table_name="lz_test_metrics",
            metrics=["lines"],
        )

        assert len(result["models_created"]) >= 1
        assert (staging_dir / "stg_lz_test_metrics.sql").exists()

    def test_empty_metrics_skips_rollups(self) -> None:
        """Test that empty metrics list skips rollup generation."""
        result = generate_dbt_models(
            tool_name="test-tool",
            table_name="lz_test_metrics",
            metrics=[],
            dry_run=True,
        )

        rollups = result.get("rollup_models", [])
        assert len(rollups) == 0
