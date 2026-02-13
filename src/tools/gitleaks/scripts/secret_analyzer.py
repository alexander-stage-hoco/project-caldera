#!/usr/bin/env python3
"""Secret analyzer using gitleaks for detection."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared.severity import PRODUCTION_PATH_PATTERNS, escalate_for_production_path


@dataclass
class SecretFinding:
    """A single secret finding from gitleaks."""

    file_path: str
    line_number: int
    rule_id: str
    secret_type: str
    description: str
    secret_preview: str  # Truncated/masked for safety
    entropy: float
    commit_hash: str
    commit_author: str
    commit_date: str
    fingerprint: str
    in_current_head: bool = True
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW


@dataclass
class FileSummary:
    """Summary of secrets in a single file."""

    file_path: str
    secret_count: int
    rule_ids: list[str]
    earliest_commit: str
    latest_commit: str


@dataclass
class DirectoryMetrics:
    """Metrics for a directory."""

    direct_secret_count: int
    recursive_secret_count: int
    direct_file_count: int
    recursive_file_count: int
    rule_id_counts: dict[str, int]


# Severity mappings by rule_id
RULE_SEVERITY_MAP = {
    # CRITICAL - Cloud infrastructure access
    "aws-access-token": "CRITICAL",
    "gcp-api-key": "CRITICAL",
    "azure-storage-key": "CRITICAL",
    "google-api-key": "CRITICAL",

    # HIGH - Payment, authentication, and private keys
    "stripe-access-token": "HIGH",
    "github-pat": "HIGH",
    "gitlab-pat": "HIGH",
    "slack-token": "HIGH",
    "slack-bot-token": "HIGH",
    "slack-webhook-url": "HIGH",
    "private-key": "HIGH",
    "rsa-private-key": "HIGH",
    "dsa-private-key": "HIGH",
    "openssh-private-key": "HIGH",
    "pgp-private-key": "HIGH",

    # MEDIUM - Generic patterns
    "generic-api-key": "MEDIUM",
    "jwt-token": "MEDIUM",
    "jwt": "MEDIUM",
    "password-in-url": "MEDIUM",
    "mongodb-connection-string": "MEDIUM",
    "postgresql-connection-string": "MEDIUM",
    "mysql-connection-string": "MEDIUM",

    # LOW - Potentially less sensitive
    "sendgrid-api-token": "LOW",
}

# NOTE: PRODUCTION_PATH_PATTERNS imported from shared.severity


def calculate_severity(rule_id: str, file_path: str, in_current_head: bool) -> str:
    """Calculate severity based on rule_id and context.

    Args:
        rule_id: The gitleaks rule ID for the finding
        file_path: Path to the file containing the secret
        in_current_head: Whether the secret is in the current HEAD

    Returns:
        Severity level: CRITICAL, HIGH, MEDIUM, or LOW
    """
    base_severity = RULE_SEVERITY_MAP.get(rule_id, "MEDIUM")

    # Escalate for production paths using shared utility
    escalated = escalate_for_production_path(base_severity, file_path, PRODUCTION_PATH_PATTERNS)

    # Reduce for historical-only secrets (not in current HEAD)
    if not in_current_head and escalated in ("MEDIUM", "LOW"):
        return "LOW"

    return escalated


@dataclass
class SecretAnalysis:
    """Complete analysis output."""

    schema_version: str = "1.0.0"
    generated_at: str = ""
    repo_name: str = ""
    repo_path: str = ""

    # Results (to be wrapped)
    tool_version: str = ""

    # Summary
    total_secrets: int = 0
    unique_secrets: int = 0
    secrets_in_head: int = 0
    secrets_in_history: int = 0
    files_with_secrets: int = 0
    commits_with_secrets: int = 0

    # By rule type
    secrets_by_rule: dict[str, int] = field(default_factory=dict)

    # By severity
    secrets_by_severity: dict[str, int] = field(default_factory=dict)

    # Detailed findings
    findings: list[SecretFinding] = field(default_factory=list)

    # File summaries
    files: dict[str, FileSummary] = field(default_factory=dict)

    # Directory rollups
    directories: dict[str, DirectoryMetrics] = field(default_factory=dict)

    # Timing
    scan_time_ms: float = 0.0


def to_output_format(
    analysis: SecretAnalysis,
    run_id: str = "00000000-0000-0000-0000-000000000000",
    repo_id: str = "00000000-0000-0000-0000-000000000000",
    branch: str = "main",
    commit: str = "0" * 40,
) -> dict:
    """Convert SecretAnalysis to Caldera envelope format with metadata + data.

    Args:
        analysis: The SecretAnalysis result to convert
        run_id: Unique run identifier (UUID)
        repo_id: Repository identifier (UUID)
        branch: Git branch analyzed
        commit: 40-character git commit SHA
    """
    return {
        "metadata": {
            "tool_name": "gitleaks",
            "tool_version": analysis.tool_version,
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": analysis.generated_at,
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "gitleaks",
            "tool_version": analysis.tool_version,
            "total_secrets": analysis.total_secrets,
            "unique_secrets": analysis.unique_secrets,
            "secrets_in_head": analysis.secrets_in_head,
            "secrets_in_history": analysis.secrets_in_history,
            "files_with_secrets": analysis.files_with_secrets,
            "commits_with_secrets": analysis.commits_with_secrets,
            "secrets_by_rule": analysis.secrets_by_rule,
            "secrets_by_severity": analysis.secrets_by_severity,
            "findings": [asdict(f) for f in analysis.findings],
            "files": {k: asdict(v) for k, v in analysis.files.items()},
            "directories": {k: asdict(v) for k, v in analysis.directories.items()},
            "scan_time_ms": analysis.scan_time_ms,
        },
    }


def get_gitleaks_version(gitleaks_path: Path) -> str:
    """Get gitleaks version string."""
    result = subprocess.run(
        [str(gitleaks_path), "version"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run_gitleaks(
    gitleaks_path: Path,
    repo_path: Path,
    config_path: Path | None = None,
    baseline_path: Path | None = None,
) -> tuple[list[dict], float]:
    """Run gitleaks on a repository and return findings.

    Args:
        gitleaks_path: Path to gitleaks binary
        repo_path: Path to repository to scan
        config_path: Optional custom config file (for entropy thresholds)
        baseline_path: Optional baseline report for comparison
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_path = Path(f.name)

    start_time = time.time()

    # Build command
    cmd = [
        str(gitleaks_path),
        "detect",
        "--source",
        str(repo_path),
        "--report-format",
        "json",
        "--report-path",
        str(report_path),
    ]

    # Add optional flags
    if config_path:
        cmd.extend(["--config", str(config_path)])
    if baseline_path:
        cmd.extend(["--baseline-path", str(baseline_path)])

    # Run gitleaks
    result = subprocess.run(cmd, capture_output=True, text=True)

    elapsed_ms = (time.time() - start_time) * 1000

    # Exit code 1 means leaks found, which is expected
    # Exit code 0 means no leaks
    # Other exit codes are errors
    if result.returncode not in (0, 1):
        raise RuntimeError(f"gitleaks failed: {result.stderr}")

    # Parse results
    if report_path.exists() and report_path.stat().st_size > 0:
        findings = json.loads(report_path.read_text())
    else:
        findings = []

    report_path.unlink()

    return findings, elapsed_ms


def get_head_commit(repo_path: Path) -> str:
    """Get the HEAD commit hash."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def get_head_files(repo_path: Path) -> set[str]:
    """Get set of files that exist in HEAD."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "ls-tree", "-r", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return set(result.stdout.strip().split("\n"))


def mask_secret(secret: str, visible_chars: int = 8) -> str:
    """Mask a secret for safe display."""
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    return secret[:visible_chars] + "*" * (len(secret) - visible_chars)


def analyze_repository(
    gitleaks_path: Path,
    repo_path: Path,
    config_path: Path | None = None,
    baseline_path: Path | None = None,
    repo_name_override: str | None = None,
) -> SecretAnalysis:
    """Analyze a repository for secrets."""
    repo_name = repo_name_override or repo_path.name
    head_commit = get_head_commit(repo_path)
    head_files = get_head_files(repo_path)

    # Run gitleaks
    raw_findings, scan_time = run_gitleaks(
        gitleaks_path, repo_path, config_path, baseline_path
    )

    # Build analysis
    analysis = SecretAnalysis(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        repo_name=repo_name,
        repo_path=str(repo_path.resolve()),
        tool_version=get_gitleaks_version(gitleaks_path),
        scan_time_ms=scan_time,
    )

    # Track unique secrets and commits
    unique_secrets: set[str] = set()
    commits_with_secrets: set[str] = set()
    files_with_secrets: set[str] = set()
    rule_counts: dict[str, int] = defaultdict(int)
    severity_counts: dict[str, int] = defaultdict(int)

    # Track file data for summaries
    file_findings: dict[str, list[dict]] = defaultdict(list)

    for raw in raw_findings:
        # Determine if secret is in HEAD (commit matches HEAD)
        file_path = raw.get("File", "")
        finding_commit = raw.get("Commit", "")
        # A secret is in HEAD if both: file exists in HEAD AND commit is HEAD
        # If the secret was in an old commit but file was changed/cleaned, it's historical
        in_head = file_path in head_files and finding_commit == head_commit

        rule_id = raw.get("RuleID", "unknown")
        severity = calculate_severity(rule_id, file_path, in_head)

        finding = SecretFinding(
            file_path=file_path,
            line_number=raw.get("StartLine", 0),
            rule_id=rule_id,
            secret_type=rule_id,
            description=raw.get("Description", ""),
            secret_preview=mask_secret(raw.get("Secret", "")),
            entropy=raw.get("Entropy", 0.0),
            commit_hash=raw.get("Commit", ""),
            commit_author=raw.get("Author", ""),
            commit_date=raw.get("Date", ""),
            fingerprint=raw.get("Fingerprint", ""),
            in_current_head=in_head,
            severity=severity,
        )

        analysis.findings.append(finding)

        # Track aggregates
        unique_secrets.add(raw.get("Fingerprint", ""))
        commits_with_secrets.add(raw.get("Commit", ""))
        files_with_secrets.add(file_path)
        rule_counts[finding.rule_id] += 1
        severity_counts[finding.severity] += 1
        file_findings[file_path].append(raw)

        if in_head:
            analysis.secrets_in_head += 1
        else:
            analysis.secrets_in_history += 1

    # Update summary counts
    analysis.total_secrets = len(raw_findings)
    analysis.unique_secrets = len(unique_secrets)
    analysis.commits_with_secrets = len(commits_with_secrets)
    analysis.files_with_secrets = len(files_with_secrets)
    analysis.secrets_by_rule = dict(rule_counts)
    analysis.secrets_by_severity = dict(severity_counts)

    # Build file summaries
    for file_path, findings_list in file_findings.items():
        commits = [f.get("Commit", "") for f in findings_list]
        dates = [f.get("Date", "") for f in findings_list]

        analysis.files[file_path] = FileSummary(
            file_path=file_path,
            secret_count=len(findings_list),
            rule_ids=list(set(f.get("RuleID", "unknown") for f in findings_list)),
            earliest_commit=min(commits) if commits else "",
            latest_commit=max(commits) if commits else "",
        )

    # Compute directory rollups
    dir_secrets_direct: dict[str, list[SecretFinding]] = defaultdict(list)
    dir_secrets_recursive: dict[str, list[SecretFinding]] = defaultdict(list)

    for finding in analysis.findings:
        file_path = Path(finding.file_path)
        parent = str(file_path.parent)
        if parent == ".":
            parent = "."

        dir_secrets_direct[parent].append(finding)

        # Add to all ancestors for recursive
        parts = file_path.parts
        for i in range(len(parts) - 1):
            ancestor = str(Path(*parts[: i + 1])) if i > 0 else parts[0]
            dir_secrets_recursive[ancestor].append(finding)

        # Root gets everything
        dir_secrets_recursive["."].append(finding)

    # Build directory metrics
    all_dirs = set(dir_secrets_direct.keys()) | set(dir_secrets_recursive.keys())
    for dir_path in all_dirs:
        direct_findings = dir_secrets_direct.get(dir_path, [])
        recursive_findings = dir_secrets_recursive.get(dir_path, [])

        direct_rules: dict[str, int] = defaultdict(int)
        for f in direct_findings:
            direct_rules[f.rule_id] += 1

        recursive_rules: dict[str, int] = defaultdict(int)
        for f in recursive_findings:
            recursive_rules[f.rule_id] += 1

        analysis.directories[dir_path] = DirectoryMetrics(
            direct_secret_count=len(direct_findings),
            recursive_secret_count=len(recursive_findings),
            direct_file_count=len(set(f.file_path for f in direct_findings)),
            recursive_file_count=len(set(f.file_path for f in recursive_findings)),
            rule_id_counts=dict(recursive_rules),
        )

    return analysis


def analyze_all_repos(
    gitleaks_path: Path,
    repos_dir: Path,
    output_dir: Path,
    config_path: Path | None = None,
    baseline_path: Path | None = None,
) -> dict[str, SecretAnalysis]:
    """Analyze all repositories in a directory."""
    results = {}

    for repo_path in sorted(repos_dir.iterdir()):
        if not repo_path.is_dir():
            continue
        if not (repo_path / ".git").exists():
            continue

        print(f"Analyzing: {repo_path.name}")
        analysis = analyze_repository(
            gitleaks_path, repo_path, config_path, baseline_path
        )
        results[repo_path.name] = analysis

        # Save individual result
        output_path = output_dir / f"{repo_path.name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(to_output_format(analysis), indent=2, default=str)
        )
        print(f"  Secrets found: {analysis.total_secrets}")
        print(f"  Output: {output_path}")

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze repositories for secrets")
    parser.add_argument(
        "path",
        type=Path,
        help="Repository or directory of repositories to analyze",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("output/runs"),
        help="Output path (file.json for single repo, or directory for multi-repo)",
    )
    parser.add_argument(
        "--gitleaks",
        type=Path,
        default=None,
        help="Path to gitleaks binary",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom gitleaks config file (for entropy thresholds, custom rules)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Path to baseline report for comparing against known issues",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        default=None,
        help="Repository name for output file naming (used by orchestrator)",
    )

    args = parser.parse_args()

    # Find gitleaks
    if args.gitleaks:
        gitleaks_path = args.gitleaks
    else:
        # Try common locations
        script_dir = Path(__file__).parent
        gitleaks_path = script_dir.parent / "bin" / "gitleaks"

    if not gitleaks_path.exists():
        raise FileNotFoundError(f"gitleaks not found at {gitleaks_path}")

    print(f"Using gitleaks: {gitleaks_path}")
    print(f"Gitleaks version: {get_gitleaks_version(gitleaks_path)}")
    print()

    # Determine if path is single repo or directory of repos
    if (args.path / ".git").exists():
        # Single repository
        print(f"Analyzing single repository: {args.path}")
        analysis = analyze_repository(
            gitleaks_path,
            args.path,
            args.config,
            args.baseline,
            repo_name_override=args.repo_name,
        )

        # Determine output path: if --output ends with .json, use it directly
        # Otherwise, construct filename from repo-name or path name
        if str(args.output).endswith(".json"):
            output_path = args.output
        else:
            output_name = args.repo_name if args.repo_name else args.path.name
            output_path = args.output / f"{output_name}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(to_output_format(analysis), indent=2, default=str))

        print(f"Secrets found: {analysis.total_secrets}")
        print(f"Output: {output_path}")
    else:
        # Directory of repositories
        print(f"Analyzing all repositories in: {args.path}")
        print()

        results = analyze_all_repos(
            gitleaks_path, args.path, args.output, args.config, args.baseline
        )

        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        total_secrets = sum(r.total_secrets for r in results.values())
        print(f"Repositories analyzed: {len(results)}")
        print(f"Total secrets found: {total_secrets}")


if __name__ == "__main__":
    main()
