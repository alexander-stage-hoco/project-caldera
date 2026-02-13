"""Cross-check tool registration across TOOL_CONFIGS, TOOL_INGESTION_CONFIGS, adapters, and schema."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import TOOL_CONFIGS, TOOL_INGESTION_CONFIGS
from persistence import adapters


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
