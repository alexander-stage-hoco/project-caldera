"""Cross-check tool registration across TOOL_CONFIGS, TOOL_INGESTION_CONFIGS, adapters, schema, and registry."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import TOOL_CONFIGS, TOOL_INGESTION_CONFIGS
from persistence import adapters
from tool_registry import (
    TOOL_REGISTRY,
    get_docker_tool_names,
    get_execution_tools,
    get_ingestion_tools,
    get_tool_names,
)


def test_all_tool_configs_have_ingestion_config() -> None:
    """Every TOOL_CONFIGS entry (except layout-scanner) has a matching TOOL_INGESTION_CONFIGS entry."""
    ingestion_names = {cfg.name for cfg in TOOL_INGESTION_CONFIGS}
    for tool in TOOL_CONFIGS:
        if tool.name == "layout-scanner":
            continue  # layout is handled specially
        assert tool.name in ingestion_names, (
            f"Tool '{tool.name}' is in TOOL_CONFIGS but has no TOOL_INGESTION_CONFIGS entry"
        )


def test_all_ingestion_configs_have_adapter_export() -> None:
    """Every adapter class in TOOL_INGESTION_CONFIGS is exported from adapters.__all__."""
    exported = set(adapters.__all__)
    for cfg in TOOL_INGESTION_CONFIGS:
        class_name = cfg.adapter_class.__name__
        assert class_name in exported, (
            f"Adapter class '{class_name}' for tool '{cfg.name}' "
            f"is not in adapters.__all__"
        )


def test_all_ingestion_configs_have_schema_tables() -> None:
    """Every tool in TOOL_INGESTION_CONFIGS has at least one lz_* table in schema.sql."""
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    schema_text = schema_path.read_text()
    table_names = set(re.findall(r"CREATE TABLE\s+(lz_\w+)", schema_text))

    # Map tool names to expected table prefixes
    tool_table_prefixes = {
        "scc": "lz_scc_",
        "lizard": "lz_lizard_",
        "roslyn-analyzers": "lz_roslyn_",
        "semgrep": "lz_semgrep_",
        "sonarqube": "lz_sonarqube_",
        "trivy": "lz_trivy_",
        "gitleaks": "lz_gitleaks_",
        "symbol-scanner": "lz_code_symbols",  # special case
        "scancode": "lz_scancode_",
        "pmd-cpd": "lz_pmd_cpd_",
        "devskim": "lz_devskim_",
        "dotcover": "lz_dotcover_",
        "git-fame": "lz_git_fame_",
        "git-sizer": "lz_git_sizer_",
        "git-blame-scanner": "lz_git_blame_",
        "dependensee": "lz_dependensee_",
        "coverage-ingest": "lz_coverage_",
    }

    for cfg in TOOL_INGESTION_CONFIGS:
        prefix = tool_table_prefixes.get(cfg.name)
        assert prefix is not None, (
            f"No table prefix mapping for tool '{cfg.name}' — add one to this test"
        )
        matching_tables = [t for t in table_names if t.startswith(prefix)]
        assert matching_tables, (
            f"Tool '{cfg.name}' has no lz_* tables starting with '{prefix}' in schema.sql"
        )


def test_tool_config_paths_exist() -> None:
    """Every path in TOOL_CONFIGS is a real directory."""
    repo_root = Path(__file__).resolve().parents[3]
    for tool in TOOL_CONFIGS:
        tool_dir = repo_root / tool.path
        assert tool_dir.is_dir(), (
            f"Tool '{tool.name}' path '{tool.path}' does not exist at {tool_dir}"
        )


# -- Tool registry cross-validation tests -----------------------------------


def test_registry_covers_all_tool_configs() -> None:
    """TOOL_REGISTRY contains every tool from TOOL_CONFIGS."""
    registry_names = {t.name for t in TOOL_REGISTRY}
    for tool in TOOL_CONFIGS:
        assert tool.name in registry_names, (
            f"TOOL_CONFIGS tool '{tool.name}' is missing from TOOL_REGISTRY"
        )


def test_registry_covers_all_ingestion_configs() -> None:
    """TOOL_REGISTRY contains every tool from TOOL_INGESTION_CONFIGS."""
    registry_names = {t.name for t in TOOL_REGISTRY}
    for cfg in TOOL_INGESTION_CONFIGS:
        assert cfg.name in registry_names, (
            f"TOOL_INGESTION_CONFIGS tool '{cfg.name}' is missing from TOOL_REGISTRY"
        )


def test_registry_paths_exist() -> None:
    """Every path in TOOL_REGISTRY is a real directory."""
    repo_root = Path(__file__).resolve().parents[3]
    for entry in TOOL_REGISTRY:
        tool_dir = repo_root / entry.path
        assert tool_dir.is_dir(), (
            f"Registry tool '{entry.name}' path '{entry.path}' does not exist at {tool_dir}"
        )


def test_registry_table_prefixes_match_schema() -> None:
    """Every tool with a table_prefix in the registry has matching tables in schema.sql."""
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    schema_text = schema_path.read_text()
    table_names = set(re.findall(r"CREATE TABLE\s+(lz_\w+)", schema_text))

    for entry in TOOL_REGISTRY:
        if not entry.table_prefix:
            continue
        matching = [t for t in table_names if t.startswith(entry.table_prefix)]
        assert matching, (
            f"Registry tool '{entry.name}' has table_prefix '{entry.table_prefix}' "
            f"but no matching tables in schema.sql"
        )


def test_registry_docker_tools_match_docker_runner() -> None:
    """Docker tool list from registry matches docker_runner.py DOCKER_TOOLS.

    Since docker_runner.py now derives DOCKER_TOOLS from get_docker_tool_names(),
    we verify the import path works and the runner uses the registry.
    """
    runner_path = Path(__file__).resolve().parents[3] / "scripts" / "docker_runner.py"
    if not runner_path.exists():
        pytest.skip("docker_runner.py not found")

    runner_text = runner_path.read_text()
    # Verify docker_runner.py imports from tool_registry
    assert "from tool_registry import" in runner_text, (
        "docker_runner.py should import from tool_registry"
    )
    assert "get_docker_tool_names" in runner_text, (
        "docker_runner.py should use get_docker_tool_names()"
    )
    # Verify DOCKER_TOOLS is assigned from the registry function
    assert "DOCKER_TOOLS" in runner_text, (
        "docker_runner.py should define DOCKER_TOOLS"
    )


def test_registry_validate_metadata_matches_ingestion() -> None:
    """validate_metadata in registry matches TOOL_INGESTION_CONFIGS."""
    registry_by_name = {t.name: t for t in TOOL_REGISTRY}
    for cfg in TOOL_INGESTION_CONFIGS:
        entry = registry_by_name.get(cfg.name)
        if entry is None:
            continue
        assert entry.validate_metadata == cfg.validate_metadata, (
            f"Tool '{cfg.name}': registry validate_metadata={entry.validate_metadata} "
            f"but TOOL_INGESTION_CONFIGS has {cfg.validate_metadata}"
        )
