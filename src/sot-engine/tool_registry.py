"""Unified tool registry — single source of truth for all tool metadata.

Every tool in the Caldera pipeline is registered here.  The orchestrator,
docker runner, CI, and tests all derive their tool lists from this module.

Usage::

    from tool_registry import TOOL_REGISTRY, get_tool_configs, get_ingestion_configs
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolRegistryEntry:
    """Metadata for a single tool in the Caldera pipeline."""

    name: str
    path: str
    adapter_module: str | None = None       # e.g. "scc_adapter"
    adapter_class: str | None = None        # e.g. "SccAdapter"
    repo_class: str | None = None           # e.g. "SccRepository"
    docker_image: str | None = None         # e.g. "caldera-tool-scc"
    validate_metadata: bool = True
    extra_env: dict[str, str] = field(default_factory=dict)
    table_prefix: str | None = None         # e.g. "lz_scc_"
    ci_skip: bool = False                   # True if skipped in CI by default


# fmt: off
TOOL_REGISTRY: tuple[ToolRegistryEntry, ...] = (
    ToolRegistryEntry(
        name="layout-scanner",
        path="src/tools/layout-scanner",
        adapter_class="LayoutScannerAdapter",
        repo_class="LayoutRepository",
        docker_image="caldera-tool-layout-scanner",
        extra_env={"NO_GITIGNORE": "1"},
        table_prefix="lz_layout_",
    ),
    ToolRegistryEntry(
        name="scc",
        path="src/tools/scc",
        adapter_class="SccAdapter",
        repo_class="SccRepository",
        docker_image="caldera-tool-scc",
        table_prefix="lz_scc_",
    ),
    ToolRegistryEntry(
        name="lizard",
        path="src/tools/lizard",
        adapter_class="LizardAdapter",
        repo_class="LizardRepository",
        docker_image="caldera-tool-lizard",
        table_prefix="lz_lizard_",
    ),
    ToolRegistryEntry(
        name="roslyn-analyzers",
        path="src/tools/roslyn-analyzers",
        adapter_class="RoslynAnalyzersAdapter",
        repo_class="RoslynRepository",
        docker_image="caldera-tool-roslyn-analyzers",
        table_prefix="lz_roslyn_",
    ),
    ToolRegistryEntry(
        name="semgrep",
        path="src/tools/semgrep",
        adapter_class="SemgrepAdapter",
        repo_class="SemgrepRepository",
        docker_image="caldera-tool-semgrep",
        table_prefix="lz_semgrep_",
    ),
    ToolRegistryEntry(
        name="sonarqube",
        path="src/tools/sonarqube",
        adapter_class="SonarqubeAdapter",
        repo_class="SonarqubeRepository",
        docker_image=None,  # requires external SonarQube server, not dockerized
        validate_metadata=False,
        table_prefix="lz_sonarqube_",
    ),
    ToolRegistryEntry(
        name="trivy",
        path="src/tools/trivy",
        adapter_class="TrivyAdapter",
        repo_class="TrivyRepository",
        docker_image="caldera-tool-trivy",
        table_prefix="lz_trivy_",
    ),
    ToolRegistryEntry(
        name="gitleaks",
        path="src/tools/gitleaks",
        adapter_class="GitleaksAdapter",
        repo_class="GitleaksRepository",
        docker_image="caldera-tool-gitleaks",
        table_prefix="lz_gitleaks_",
    ),
    ToolRegistryEntry(
        name="symbol-scanner",
        path="src/tools/symbol-scanner",
        adapter_class="SymbolScannerAdapter",
        repo_class="SymbolScannerRepository",
        docker_image="caldera-tool-symbol-scanner",
        table_prefix="lz_code_symbols",
    ),
    ToolRegistryEntry(
        name="scancode",
        path="src/tools/scancode",
        adapter_class="ScancodeAdapter",
        repo_class="ScancodeRepository",
        docker_image="caldera-tool-scancode",
        table_prefix="lz_scancode_",
    ),
    ToolRegistryEntry(
        name="pmd-cpd",
        path="src/tools/pmd-cpd",
        adapter_class="PmdCpdAdapter",
        repo_class="PmdCpdRepository",
        docker_image="caldera-tool-pmd-cpd",
        table_prefix="lz_pmd_cpd_",
    ),
    ToolRegistryEntry(
        name="devskim",
        path="src/tools/devskim",
        adapter_class="DevskimAdapter",
        repo_class="DevskimRepository",
        docker_image="caldera-tool-devskim",
        table_prefix="lz_devskim_",
    ),
    ToolRegistryEntry(
        name="dotcover",
        path="src/tools/dotcover",
        adapter_class="DotcoverAdapter",
        repo_class="DotcoverRepository",
        docker_image="caldera-tool-dotcover",
        table_prefix="lz_dotcover_",
    ),
    ToolRegistryEntry(
        name="git-fame",
        path="src/tools/git-fame",
        adapter_class="GitFameAdapter",
        repo_class="GitFameRepository",
        docker_image="caldera-tool-git-fame",
        table_prefix="lz_git_fame_",
    ),
    ToolRegistryEntry(
        name="git-sizer",
        path="src/tools/git-sizer",
        adapter_class="GitSizerAdapter",
        repo_class="GitSizerRepository",
        docker_image="caldera-tool-git-sizer",
        table_prefix="lz_git_sizer_",
    ),
    ToolRegistryEntry(
        name="git-blame-scanner",
        path="src/tools/git-blame-scanner",
        adapter_class="GitBlameScannerAdapter",
        repo_class="GitBlameRepository",
        docker_image="caldera-tool-git-blame-scanner",
        table_prefix="lz_git_blame_",
    ),
    ToolRegistryEntry(
        name="dependensee",
        path="src/tools/dependensee",
        adapter_class="DependenseeAdapter",
        repo_class="DependenseeRepository",
        docker_image="caldera-tool-dependensee",
        table_prefix="lz_dependensee_",
    ),
    ToolRegistryEntry(
        name="coverage-ingest",
        path="src/tools/coverage-ingest",
        adapter_class="CoverageIngestAdapter",
        repo_class="CoverageRepository",
        docker_image="caldera-tool-coverage-ingest",
        table_prefix="lz_coverage_",
    ),
)
# fmt: on


def get_tool_names() -> list[str]:
    """
    Get the names of all tools registered in TOOL_REGISTRY.
    
    Returns:
        list[str]: List of tool name strings in registry order.
    """
    return [t.name for t in TOOL_REGISTRY]


def get_execution_tools() -> list[ToolRegistryEntry]:
    """
    List tools that are executed by the pipeline.
    
    Returns:
        list[ToolRegistryEntry]: ToolRegistryEntry objects for all registered tools except the ingestion-only tool named "coverage-ingest".
    """
    return [t for t in TOOL_REGISTRY if t.name != "coverage-ingest"]


def get_docker_tool_names() -> list[str]:
    """
    List tool names that provide a Docker image.
    
    Returns:
        list[str]: Tool names whose registry entries specify a non-None `docker_image`.
    """
    return [t.name for t in TOOL_REGISTRY if t.docker_image]


def get_ingestion_tools() -> list[ToolRegistryEntry]:
    """
    List registered tools that provide ingestion adapters.
    
    This excludes the tool named "layout-scanner", which does not expose an ingestion adapter.
    
    Returns:
        list[ToolRegistryEntry]: ToolRegistryEntry objects that have an `adapter_class` defined.
    """
    return [t for t in TOOL_REGISTRY if t.name != "layout-scanner" and t.adapter_class]
