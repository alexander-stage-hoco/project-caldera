#!/usr/bin/env python3
"""Main orchestrator for SonarQube analysis.

Adapted for Caldera envelope output format.
"""

from __future__ import annotations

import json
import signal
import subprocess
import sys
import time
import resource
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import click
import structlog

from .api import SonarQubeClient, ApiConfig
from .api.module_a_task import wait_for_analysis_complete, AnalysisTimeoutError, AnalysisFailedError
from .api.module_b_components import get_component_tree
from .api.module_c_catalog import discover_all_metrics
from .api.module_d_measures import extract_measures_chunked
from .api.module_e_issues import extract_issues
from .api.module_f_rules import hydrate_rules_for_project
from .api.module_g_duplications import extract_duplications
from .api.module_h_quality_gate import get_quality_gate_status
from .api.module_i_history import get_analysis_history
from .docker_lifecycle import (
    DockerConfig,
    SonarQubeContainer,
    cleanup_on_error,
    is_container_running,
)
from .scanner import ScannerConfig, run_sonar_scanner, create_scanner_config
from .export import build_export_data, validate_export

# Add shared src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.git_utilities import resolve_commit
from common.envelope_formatter import create_envelope, get_current_timestamp
from common.path_normalization import normalize_file_path

logger = structlog.get_logger(__name__)

# Tool and schema version
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.2.0"


@dataclass
class AnalysisConfig:
    """Configuration for the full analysis workflow."""

    repo_path: Path
    project_key: str
    output_path: Path
    sonarqube_url: str = "http://localhost:9000"
    token: str | None = None
    keep_container: bool = False
    container_already_running: bool = False
    use_docker_scanner: bool = True
    analysis_timeout: int = 600
    skip_scan: bool = False
    # Caldera orchestrator fields
    run_id: str = ""
    repo_id: str = ""
    branch: str = "main"
    commit: str = ""




def setup_signal_handlers(docker_config: DockerConfig) -> None:
    """Set up signal handlers for graceful cleanup."""

    def handler(signum, frame):
        logger.warning("Received signal, cleaning up", signal=signum)
        cleanup_on_error(docker_config)
        sys.exit(1)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def to_envelope_format(
    data: dict,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
    tool_version: str,
) -> dict:
    """Convert analysis data to Caldera envelope output format."""
    return create_envelope(
        data,
        tool_name="sonarqube",
        tool_version=tool_version,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        schema_version=SCHEMA_VERSION,
    )


def run_analysis(config: AnalysisConfig) -> dict:
    """Run the complete SonarQube analysis workflow.

    Steps:
    1. Start SonarQube container (if needed)
    2. Run sonar-scanner
    3. Wait for CE task completion
    4. Extract all data via API
    5. Export in Caldera envelope format
    6. Stop container (if needed)

    Args:
        config: Analysis configuration

    Returns:
        Analysis results as dictionary in Caldera envelope format
    """
    docker_config = DockerConfig(base_url=config.sonarqube_url)
    start_time = datetime.now(timezone.utc)
    start_perf = time.perf_counter()
    setup_signal_handlers(docker_config)

    was_running = is_container_running(docker_config)
    if was_running:
        logger.info("SonarQube container already running")
        config.container_already_running = True

    with SonarQubeContainer(
        config=docker_config,
        keep_running=config.keep_container or config.container_already_running,
    ) as container:
        token = config.token or container.admin_token
        api_config = ApiConfig(base_url=config.sonarqube_url, token=token)
        with SonarQubeClient(api_config) as client:
            analysis_id = None
            revision = None

            if not config.skip_scan:
                scanner_config = create_scanner_config(
                    project_key=config.project_key,
                    repo_path=config.repo_path,
                    sonarqube_url=config.sonarqube_url,
                    token=token,
                    use_docker=config.use_docker_scanner,
                )

                logger.info("Running sonar-scanner", project_key=config.project_key)
                task_id = run_sonar_scanner(config.repo_path, scanner_config)

                logger.info("Waiting for analysis to complete")
                try:
                    task_result = wait_for_analysis_complete(
                        client,
                        config.project_key,
                        timeout=config.analysis_timeout,
                        task_id=task_id or None,
                    )
                    analysis_id = task_result.analysis_id
                except AnalysisTimeoutError as e:
                    logger.error("Analysis timed out", error=str(e))
                    raise
                except AnalysisFailedError as e:
                    logger.error("Analysis failed", error=str(e))
                    raise

            # Extract all data
            logger.info("Extracting data from SonarQube API")

            logger.info("Extracting component tree")
            components = get_component_tree(client, config.project_key)

            logger.info("Discovering metrics")
            metric_catalog = discover_all_metrics(client)

            logger.info("Extracting measures")
            measures = extract_measures_chunked(client, config.project_key)

            logger.info("Extracting issues")
            issues = extract_issues(client, config.project_key)

            logger.info("Hydrating rule metadata")
            rules = hydrate_rules_for_project(client, config.project_key)

            logger.info("Extracting duplications")
            duplications = extract_duplications(client, config.project_key)

            logger.info("Getting quality gate status")
            quality_gate = get_quality_gate_status(client, config.project_key, analysis_id)

            logger.info("Getting analysis history")
            history = get_analysis_history(client, config.project_key)

            if history.latest:
                revision = history.latest.revision

            sonarqube_version = "unknown"
            try:
                status = client.get_system_status()
                sonarqube_version = status.get("version") or "unknown"
            except Exception as exc:
                logger.warning("Failed to read SonarQube version", error=str(exc))

            # Build source metadata
            # Use repo name only (not absolute path) for Caldera compliance
            source = {
                "sonarqube_url": config.sonarqube_url,
                "project_key": config.project_key,
                "analysis_id": analysis_id,
                "revision": revision,
                "repo_name": config.repo_path.name,
                "repo_path": config.repo_path.name,
            }

            # Compute timing and performance metadata
            end_time = datetime.now(timezone.utc)
            duration_ms = (time.perf_counter() - start_perf) * 1000
            peak_memory_mb = _get_peak_memory_mb()
            api_calls = list(client.api_calls)
            total_api_time_ms = sum(call.get("duration_ms", 0) for call in api_calls)

            internal_metadata = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": round(duration_ms, 2),
                "peak_memory_mb": peak_memory_mb,
                "api_calls": api_calls,
                "total_api_time_ms": round(total_api_time_ms, 2),
            }

            # Build the inner data structure
            inner_data = build_export_data(
                source=source,
                metric_catalog=metric_catalog,
                components=components,
                measures=measures,
                issues=issues,
                rules=rules,
                duplications=duplications,
                quality_gate=quality_gate,
                analyses=history,
                tool_version=sonarqube_version,
                metadata=internal_metadata,
            )

            # Resolve commit
            commit = resolve_commit(config.repo_path.resolve(), config.commit or None, strict=False)

            # Wrap in Caldera envelope format
            timestamp = get_current_timestamp()
            envelope = to_envelope_format(
                data=inner_data,
                run_id=config.run_id,
                repo_id=config.repo_id,
                branch=config.branch,
                commit=commit,
                timestamp=timestamp,
                tool_version=sonarqube_version,
            )

            # Write output
            config.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config.output_path, "w") as f:
                json.dump(envelope, f, indent=2, default=str)

            logger.info(
                "Analysis complete",
                output=str(config.output_path),
                issues=issues.rollups.total,
                components=len(components.by_key),
            )

            return envelope


def _get_peak_memory_mb() -> float:
    """Return peak RSS memory in MB for the current process."""
    try:
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except Exception:
        return 0.0

    if sys.platform == "darwin":
        return round(peak / (1024 * 1024), 2)
    return round(peak / 1024, 2)


@click.command()
@click.argument("repo_path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--project-key",
    "-p",
    required=True,
    help="SonarQube project key",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output JSON file path",
)
@click.option(
    "--sonarqube-url",
    default="http://localhost:9000",
    help="SonarQube server URL",
)
@click.option(
    "--token",
    "-t",
    envvar="SONAR_TOKEN",
    help="SonarQube authentication token",
)
@click.option(
    "--keep-container",
    is_flag=True,
    help="Keep SonarQube container running after analysis",
)
@click.option(
    "--skip-scan",
    is_flag=True,
    help="Skip scanning, extract from existing project",
)
@click.option(
    "--native-scanner",
    is_flag=True,
    help="Use native sonar-scanner instead of Docker",
)
@click.option(
    "--timeout",
    default=600,
    help="Analysis timeout in seconds",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
# Caldera orchestrator options
@click.option(
    "--run-id",
    default="",
    help="Run identifier (required for orchestrator)",
)
@click.option(
    "--repo-id",
    default="",
    help="Repository identifier (required for orchestrator)",
)
@click.option(
    "--branch",
    default="main",
    help="Branch being analyzed",
)
@click.option(
    "--commit",
    default="",
    help="Commit SHA (auto-detected if not provided)",
)
def main(
    repo_path: Path,
    project_key: str,
    output: Path | None,
    sonarqube_url: str,
    token: str | None,
    keep_container: bool,
    skip_scan: bool,
    native_scanner: bool,
    timeout: int,
    verbose: bool,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
):
    """Run SonarQube analysis on a repository.

    REPO_PATH is the path to the repository to analyze.
    """
    log_level = "DEBUG" if verbose else "INFO"
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    if output is None:
        output = Path("outputs") / run_id / "output.json" if run_id else Path("outputs/runs") / f"{project_key}.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    # Generate run_id if not provided
    if not run_id:
        import uuid
        run_id = str(uuid.uuid4())
    if not repo_id:
        import uuid
        repo_id = str(uuid.uuid4())

    config = AnalysisConfig(
        repo_path=repo_path,
        project_key=project_key,
        output_path=output,
        sonarqube_url=sonarqube_url,
        token=token,
        keep_container=keep_container,
        use_docker_scanner=not native_scanner,
        analysis_timeout=timeout,
        skip_scan=skip_scan,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
    )

    try:
        result = run_analysis(config)
        click.echo(f"Analysis complete: {output}")

        # Extract summary from envelope format
        data = result.get("data", {})
        results = data.get("results", {})
        issues_total = results.get("issues", {}).get("rollups", {}).get("total", 0)
        qg_status = results.get("quality_gate", {}).get("status", "UNKNOWN")

        click.echo(f"Issues found: {issues_total}")
        click.echo(f"Quality gate: {qg_status}")
    except Exception as e:
        logger.error("Analysis failed", error=str(e))
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
