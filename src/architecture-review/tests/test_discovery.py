"""Tests for file discovery protocol."""

from __future__ import annotations

from pathlib import Path

import pytest

from discovery import ToolFiles, discover_tool_files, list_all_tools


class TestDiscoverToolFiles:
    def test_discover_scc_files(self, project_root: Path) -> None:
        tf = discover_tool_files("scc", project_root)
        assert tf.tool_name == "scc"
        assert tf.tool_dir == project_root / "src" / "tools" / "scc"
        assert tf.adapter_file is not None
        assert tf.adapter_file.exists()
        assert tf.adapter_class == "SccAdapter"
        assert "SccFileMetric" in tf.entity_names
        assert tf.analyze_py is not None
        assert tf.output_schema is not None
        assert tf.blueprint is not None

    def test_discover_lizard_files(self, project_root: Path) -> None:
        tf = discover_tool_files("lizard", project_root)
        assert tf.tool_name == "lizard"
        assert tf.adapter_class == "LizardAdapter"
        assert "LizardFileMetric" in tf.entity_names
        assert "LizardFunctionMetric" in tf.entity_names

    def test_discover_nonexistent_tool(self, project_root: Path) -> None:
        tf = discover_tool_files("nonexistent-tool", project_root)
        assert tf.adapter_file is None
        assert tf.adapter_class is None
        assert tf.entity_names == []
        assert tf.analyze_py is None

    def test_tool_files_paths_exist(self, project_root: Path) -> None:
        tf = discover_tool_files("scc", project_root)
        # Core SoT files always exist
        assert tf.entities_file.exists()
        assert tf.repositories_file.exists()
        assert tf.schema_sql.exists()
        assert tf.orchestrator_file.exists()
        assert tf.adapter_init.exists()

    def test_discover_pmd_cpd(self, project_root: Path) -> None:
        tf = discover_tool_files("pmd-cpd", project_root)
        assert tf.tool_name == "pmd-cpd"
        assert tf.adapter_class == "PmdCpdAdapter"
        assert tf.adapter_file is not None
        assert tf.repo_class == "PmdCpdRepository"


class TestListAllTools:
    def test_returns_known_tools(self, project_root: Path) -> None:
        tools = list_all_tools(project_root)
        assert "scc" in tools
        assert "lizard" in tools
        assert "semgrep" in tools
        assert len(tools) >= 10

    def test_returns_sorted(self, project_root: Path) -> None:
        tools = list_all_tools(project_root)
        assert tools == sorted(tools)
