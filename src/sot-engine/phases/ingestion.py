from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from persistence.adapters import (
    CoverageIngestAdapter, DependenseeAdapter, DevskimAdapter, DotcoverAdapter,
    GitBlameScannerAdapter, GitFameAdapter, GitSizerAdapter, GitleaksAdapter,
    LayoutScannerAdapter, LizardAdapter, PmdCpdAdapter, RoslynAnalyzersAdapter,
    ScancodeAdapter, SccAdapter, SemgrepAdapter, SonarqubeAdapter,
    SymbolScannerAdapter, TrivyAdapter,
)
from persistence.adapters.base_adapter import BaseAdapter
from persistence.quality import DataQualityChecker
from persistence.repositories import (
    BaseRepository,
    CoverageRepository,
    DependenseeRepository,
    DevskimRepository,
    DotcoverRepository,
    GitBlameRepository,
    GitFameRepository,
    GitSizerRepository,
    GitleaksRepository,
    LayoutRepository,
    LizardRepository,
    PmdCpdRepository,
    RoslynRepository,
    ScancodeRepository,
    SccRepository,
    SemgrepRepository,
    SonarqubeRepository,
    SymbolScannerRepository,
    ToolRunRepository,
    TrivyRepository,
)
from tool_registry import get_ingestion_tools

from phases.schema import ensure_schema
from phases.utilities import OrchestratorLogger
from phases.validation import load_payload, validate_payload


@dataclass
class ToolIngestionConfig:
    """Configuration for ingesting a tool's output."""
    name: str
    adapter_class: type[BaseAdapter]
    repo_class: type[BaseRepository] | None  # None for layout adapter
    validate_metadata: bool = True  # Whether to validate standard metadata structure


# Adapter/repository class lookup tables for registry-driven ingestion config
_ADAPTER_CLASSES: dict[str, type[BaseAdapter]] = {
    cls.__name__: cls
    for cls in [
        SccAdapter, LizardAdapter, RoslynAnalyzersAdapter, SemgrepAdapter,
        SonarqubeAdapter, TrivyAdapter, GitleaksAdapter, SymbolScannerAdapter,
        ScancodeAdapter, PmdCpdAdapter, DevskimAdapter, DotcoverAdapter,
        GitFameAdapter, GitSizerAdapter, GitBlameScannerAdapter,
        DependenseeAdapter, CoverageIngestAdapter,
    ]
}

_REPO_CLASSES: dict[str, type[BaseRepository]] = {
    cls.__name__: cls
    for cls in [
        SccRepository, LizardRepository, RoslynRepository, SemgrepRepository,
        SonarqubeRepository, TrivyRepository, GitleaksRepository,
        SymbolScannerRepository, ScancodeRepository, PmdCpdRepository,
        DevskimRepository, DotcoverRepository, GitFameRepository,
        GitSizerRepository, GitBlameRepository, DependenseeRepository,
        CoverageRepository,
    ]
}

# Ingestion configurations derived from the unified tool registry
TOOL_INGESTION_CONFIGS = [
    ToolIngestionConfig(
        name=t.name,
        adapter_class=_ADAPTER_CLASSES[t.adapter_class],
        repo_class=_REPO_CLASSES.get(t.repo_class) if t.repo_class else None,
        validate_metadata=t.validate_metadata,
    )
    for t in get_ingestion_tools()
]


def ingest_outputs(
    conn: duckdb.DuckDBPyConnection,
    repo_id: str,
    collection_run_id: str,
    run_id: str,
    branch: str,
    commit: str,
    repo_path: Path,
    layout_output: Path | None,
    scc_output: Path | None,
    lizard_output: Path | None,
    roslyn_output: Path | None,
    semgrep_output: Path | None = None,
    sonarqube_output: Path | None = None,
    trivy_output: Path | None = None,
    gitleaks_output: Path | None = None,
    symbol_scanner_output: Path | None = None,
    scancode_output: Path | None = None,
    pmd_cpd_output: Path | None = None,
    devskim_output: Path | None = None,
    dotcover_output: Path | None = None,
    git_fame_output: Path | None = None,
    git_sizer_output: Path | None = None,
    git_blame_scanner_output: Path | None = None,
    dependensee_output: Path | None = None,
    coverage_output: Path | None = None,
    schema_path: Path = None,
    logger: OrchestratorLogger | None = None,
    continue_on_failure: bool = False,
) -> None:
    ensure_schema(conn, schema_path)
    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    log_fn = logger.info if logger else None
    quality_checker = DataQualityChecker(conn, logger=log_fn)

    # Layout must be ingested first (other tools depend on it)
    if not layout_output:
        raise ValueError("layout output is required for ingestion")
    payload = load_payload(layout_output)
    validate_payload(
        payload.get("metadata", {}), repo_id, run_id,
        expected_commit=commit,
    )
    LayoutScannerAdapter(run_repo, layout_repo, repo_path, log_fn).persist(payload)

    # Map tool names to output paths
    tool_outputs: dict[str, Path | None] = {
        "scc": scc_output,
        "lizard": lizard_output,
        "roslyn-analyzers": roslyn_output,
        "semgrep": semgrep_output,
        "sonarqube": sonarqube_output,
        "trivy": trivy_output,
        "gitleaks": gitleaks_output,
        "symbol-scanner": symbol_scanner_output,
        "scancode": scancode_output,
        "pmd-cpd": pmd_cpd_output,
        "devskim": devskim_output,
        "dotcover": dotcover_output,
        "git-fame": git_fame_output,
        "git-blame-scanner": git_blame_scanner_output,
        "dependensee": dependensee_output,
        "git-sizer": git_sizer_output,
        "coverage-ingest": coverage_output,
    }

    # Ingest each tool using its configuration
    ingest_errors: list[str] = []
    for config in TOOL_INGESTION_CONFIGS:
        output_path = tool_outputs.get(config.name)
        if not output_path:
            continue

        try:
            payload = load_payload(output_path)
            if config.validate_metadata:
                validate_payload(
                    payload.get("metadata", {}),
                    repo_id,
                    run_id,
                    expected_commit=commit,
                    expected_tool=config.name,
                )
            else:
                # Best-effort validation: do not fail the run, but surface contract drift.
                try:
                    validate_payload(
                        payload.get("metadata", {}),
                        repo_id,
                        run_id,
                        expected_commit=commit,
                        expected_tool=config.name,
                    )
                except Exception as exc:
                    if log_fn:
                        log_fn(f"WARNING: metadata validation skipped for {config.name}: {exc}")

            # Create adapter with appropriate repository
            tool_repo = config.repo_class(conn) if config.repo_class else None
            adapter = config.adapter_class(
                run_repo,
                layout_repo,
                tool_repo,
                repo_path,
                log_fn,
            )
            adapter._quality_checker = quality_checker
            adapter.persist(payload)
        except Exception as exc:
            if continue_on_failure:
                msg = f"WARNING: {config.name} ingestion failed: {exc}"
                if log_fn:
                    log_fn(msg)
                ingest_errors.append(config.name)
            else:
                raise

    if ingest_errors and log_fn:
        log_fn(f"Ingestion completed with {len(ingest_errors)} error(s): {', '.join(ingest_errors)}")
