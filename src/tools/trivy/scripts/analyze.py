#!/usr/bin/env python3
"""Main orchestrator for Trivy vulnerability analysis."""

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import click
import structlog

# Import ecosystem detection from common module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from common.ecosystem_detector import (
    detect_ecosystems_from_directory,
    format_ecosystem_completeness,
)

logger = structlog.get_logger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for the analysis workflow."""

    repo_path: Path
    repo_name: str
    output_dir: Path
    run_id: str
    repo_id: str
    branch: str
    commit: str
    timeout: int = 600


def get_trivy_version() -> str:
    """Get the installed trivy version."""
    try:
        result = subprocess.run(
            ["trivy", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse version from "Version: 0.58.0" format
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
        return "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_trivy_scan(repo_path: Path, timeout: int) -> dict:
    """Run trivy filesystem scan and return parsed JSON output.

    Args:
        repo_path: Path to repository to scan
        timeout: Scan timeout in seconds

    Returns:
        Parsed trivy JSON output
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        output_file = Path(f.name)

    try:
        cmd = [
            "trivy",
            "fs",
            "--format", "json",
            "--output", str(output_file),
            "--severity", "CRITICAL,HIGH,MEDIUM,LOW,UNKNOWN",
            "--scanners", "vuln,misconfig",
            "--timeout", f"{timeout}s",
            str(repo_path),
        ]

        logger.info("Running trivy scan", cmd=" ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 30,  # Allow extra time for cleanup
        )

        if result.returncode != 0:
            logger.warning(
                "Trivy returned non-zero exit code",
                returncode=result.returncode,
                stderr=result.stderr[:500] if result.stderr else None,
            )

        # Read and parse output
        if output_file.exists():
            raw_output = json.loads(output_file.read_text())
            return raw_output
        else:
            logger.error("Trivy output file not created")
            return {"Results": []}

    except subprocess.TimeoutExpired:
        logger.error("Trivy scan timed out", timeout=timeout)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse trivy JSON output", error=str(e))
        raise
    finally:
        if output_file.exists():
            output_file.unlink()


def discover_scannable_files(repo_path: Path) -> dict:
    """Pre-scan to discover dependency files and check ecosystem completeness.

    This function walks the repository before running trivy to identify
    all dependency files (manifests and lockfiles) and report on ecosystem
    completeness. This helps users understand why trivy might miss vulnerabilities.

    Args:
        repo_path: Path to repository to scan

    Returns:
        Dictionary with ecosystem_completeness data and warnings
    """
    logger.info("Discovering dependency files", repo_path=str(repo_path))

    # Run ecosystem detection
    result = detect_ecosystems_from_directory(repo_path)
    completeness = format_ecosystem_completeness(result)

    # Log warnings for incomplete ecosystems
    for warning in completeness.get("warnings", []):
        logger.warning(warning)

    logger.info(
        "Ecosystem discovery complete",
        ecosystems_found=len(completeness.get("ecosystems", {})),
        dependency_files=len(completeness.get("dependency_files", [])),
        incomplete_ecosystems=len(result.incomplete_ecosystems),
    )

    return completeness


def transform_trivy_output(
    raw_output: dict,
    config: AnalysisConfig,
    ecosystem_completeness: dict | None = None,
) -> dict:
    """Transform raw trivy JSON to envelope format.

    Args:
        raw_output: Raw trivy JSON output
        config: Analysis configuration
        ecosystem_completeness: Optional ecosystem completeness data from pre-scan

    Returns:
        Transformed envelope-format output
    """
    tool_version = get_trivy_version()
    results = raw_output.get("Results", [])

    targets = []
    vulnerabilities = []
    misconfigurations = []

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "UNKNOWN": 0,
    }
    fixable_count = 0

    for result in results:
        target_path = result.get("Target", "")
        target_type = result.get("Type", "unknown")
        target_class = result.get("Class", "")

        # Count vulnerabilities for this target
        vulns = result.get("Vulnerabilities", []) or []
        misconfigs = result.get("Misconfigurations", []) or []

        target_severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "UNKNOWN": 0,
        }

        # Process vulnerabilities
        for vuln in vulns:
            severity = vuln.get("Severity", "UNKNOWN")
            target_severity_counts[severity] = target_severity_counts.get(severity, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            fixed_version = vuln.get("FixedVersion")
            if fixed_version:
                fixable_count += 1

            # Extract CVSS score from nested structure
            cvss_score = None
            cvss_data = vuln.get("CVSS", {})
            if cvss_data:
                # Try NVD first, then other sources
                for source in ["nvd", "redhat", "ghsa"]:
                    if source in cvss_data:
                        cvss_score = cvss_data[source].get("V3Score")
                        if cvss_score:
                            break

            vulnerabilities.append({
                "id": vuln.get("VulnerabilityID", ""),
                "target": target_path,
                "target_type": target_type,
                "package": vuln.get("PkgName", ""),
                "installed_version": vuln.get("InstalledVersion"),
                "fixed_version": fixed_version,
                "severity": severity,
                "cvss_score": cvss_score,
                "title": vuln.get("Title"),
                "description": vuln.get("Description"),
                "published_date": vuln.get("PublishedDate"),
                "age_days": None,  # Could compute from published_date
                "fix_available": fixed_version is not None,
                "references": vuln.get("References", []),
            })

        # Process misconfigurations
        for misconfig in misconfigs:
            severity = misconfig.get("Severity", "UNKNOWN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            misconfigurations.append({
                "id": misconfig.get("ID", ""),
                "target": target_path,
                "target_type": target_type,
                "severity": severity,
                "title": misconfig.get("Title"),
                "description": misconfig.get("Description"),
                "resolution": misconfig.get("Resolution"),
                "start_line": misconfig.get("CauseMetadata", {}).get("StartLine"),
                "end_line": misconfig.get("CauseMetadata", {}).get("EndLine"),
            })

        # Add target with aggregated counts
        if vulns or misconfigs or target_class == "lang-pkgs":
            targets.append({
                "path": target_path,
                "type": target_type,
                "vulnerability_count": len(vulns),
                "critical_count": target_severity_counts["CRITICAL"],
                "high_count": target_severity_counts["HIGH"],
                "medium_count": target_severity_counts["MEDIUM"],
                "low_count": target_severity_counts["LOW"],
            })

    # Build envelope
    data = {
        "tool": "trivy",
        "tool_version": tool_version,
        "scan_type": "fs",
        "targets": targets,
        "vulnerabilities": vulnerabilities,
        "iac_misconfigurations": {
            "count": len(misconfigurations),
            "misconfigurations": misconfigurations,
        },
        "findings_summary": {
            "total_vulnerabilities": len(vulnerabilities),
            "total_misconfigurations": len(misconfigurations),
            "by_severity": severity_counts,
            "fixable_count": fixable_count,
        },
    }

    # Add ecosystem completeness data if available
    if ecosystem_completeness:
        data["ecosystem_completeness"] = ecosystem_completeness

    envelope = {
        "id": config.repo_name,  # Used for ground truth matching
        "metadata": {
            "tool_name": "trivy",
            "tool_version": tool_version,
            "run_id": config.run_id,
            "repo_id": config.repo_id,
            "repo_name": config.repo_name,
            "branch": config.branch,
            "commit": config.commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        },
        "data": data,
    }

    return envelope


def run_analysis(config: AnalysisConfig) -> dict:
    """Run the complete trivy analysis workflow.

    Args:
        config: Analysis configuration

    Returns:
        Analysis results as dictionary
    """
    logger.info(
        "Starting trivy analysis",
        repo_path=str(config.repo_path),
        repo_name=config.repo_name,
    )

    # Pre-scan: discover dependency files and check ecosystem completeness
    ecosystem_completeness = discover_scannable_files(config.repo_path)

    # Run trivy scan
    raw_output = run_trivy_scan(config.repo_path, config.timeout)

    # Transform to envelope format
    result = transform_trivy_output(raw_output, config, ecosystem_completeness)

    # Write output
    output_path = config.output_dir / "output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    logger.info(
        "Analysis complete",
        output=str(output_path),
        vulnerabilities=result["data"]["findings_summary"]["total_vulnerabilities"],
        misconfigurations=result["data"]["findings_summary"]["total_misconfigurations"],
    )

    return result


@click.command()
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Path to repository to analyze",
)
@click.option(
    "--repo-name",
    required=True,
    help="Repository name for output file",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory",
)
@click.option(
    "--run-id",
    required=True,
    help="Unique run identifier",
)
@click.option(
    "--repo-id",
    required=True,
    help="Repository identifier",
)
@click.option(
    "--branch",
    default="main",
    help="Git branch name",
)
@click.option(
    "--commit",
    required=True,
    help="Git commit SHA",
)
@click.option(
    "--timeout",
    default=600,
    help="Scan timeout in seconds",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def main(
    repo_path: Path,
    repo_name: str,
    output_dir: Path,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timeout: int,
    verbose: bool,
):
    """Run Trivy vulnerability analysis on a repository."""
    # Configure logging
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

    config = AnalysisConfig(
        repo_path=repo_path,
        repo_name=repo_name,
        output_dir=output_dir,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timeout=timeout,
    )

    try:
        result = run_analysis(config)
        click.echo(f"Analysis complete: {output_dir / 'output.json'}")
        click.echo(
            f"Vulnerabilities: {result['data']['findings_summary']['total_vulnerabilities']}"
        )
        click.echo(
            f"Misconfigurations: {result['data']['findings_summary']['total_misconfigurations']}"
        )
    except Exception as e:
        logger.error("Analysis failed", error=str(e))
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
