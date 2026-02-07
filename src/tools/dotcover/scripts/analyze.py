"""Main analysis script for dotcover.

This script invokes the JetBrains dotCover CLI to collect code coverage metrics
and transforms the output to the Caldera envelope format.

dotCover reports coverage at assembly -> namespace -> type -> method hierarchy.
We flatten this to:
- Assembly-level coverage summary
- Type (class) level coverage with optional file mapping
- Method-level coverage detail

For implementation examples, see:
- src/tools/scc/scripts/analyze.py - File metrics (lines, complexity)
- src/tools/roslyn-analyzers/scripts/analyze.py - .NET tool invocation
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope
from common.path_normalization import normalize_file_path

TOOL_NAME = "dotcover"
SCHEMA_VERSION = "1.0.0"
DOCKER_IMAGE = "dotcover-runner"


@dataclass
class AssemblyCoverage:
    """Assembly-level coverage metrics."""
    name: str
    covered_statements: int
    total_statements: int
    coverage_pct: float


@dataclass
class TypeCoverage:
    """Type (class) level coverage metrics."""
    assembly: str
    namespace: str | None
    name: str
    file_path: str | None  # Source file if available
    covered_statements: int
    total_statements: int
    coverage_pct: float


@dataclass
class MethodCoverage:
    """Method-level coverage metrics."""
    assembly: str
    type_name: str
    name: str
    covered_statements: int
    total_statements: int
    coverage_pct: float


def get_dotcover_version() -> str:
    """Get dotCover version from CLI."""
    try:
        result = subprocess.run(
            ["dotCover", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse version from output like "JetBrains dotCover Command-Line Tools 2025.3.2"
        for line in result.stdout.strip().split("\n"):
            if "dotCover" in line:
                parts = line.split()
                for part in reversed(parts):
                    if part[0].isdigit():
                        return part
        return "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def find_test_project(repo_path: Path) -> Path | None:
    """Find a test project in the repository."""
    # Look for common test project patterns
    patterns = [
        "**/test*.csproj",
        "**/tests*.csproj",
        "**/*Test.csproj",
        "**/*Tests.csproj",
        "**/*.Tests.csproj",
        "**/*.Test.csproj",
    ]
    for pattern in patterns:
        matches = list(repo_path.glob(pattern))
        if matches:
            return matches[0]
    return None


def find_solution(repo_path: Path) -> Path | None:
    """Find a solution file in the repository."""
    slns = list(repo_path.glob("**/*.sln"))
    if slns:
        # Prefer solution at repo root
        for sln in slns:
            if sln.parent == repo_path:
                return sln
        return slns[0]
    return None


def run_dotcover(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
) -> tuple[dict | None, Path | None]:
    """Run dotCover coverage analysis.

    Uses a two-step approach:
    1. Run coverage collection (generates snapshot)
    2. Generate report from snapshot (with timeout for macOS ARM64 bug)

    Args:
        repo_path: Path to the repository to analyze
        output_dir: Directory for output files
        test_project: Optional specific test project to run

    Returns:
        Tuple of (parsed JSON report, detailed XML path if available)
    """
    # Ensure output_dir is absolute for dotCover
    output_dir = output_dir.resolve()
    json_report = output_dir / "coverage.json"
    xml_report = output_dir / "coverage.xml"
    snapshot = output_dir / "coverage.dcvr"

    # Determine what to test
    test_target = str(test_project) if test_project else str(repo_path)

    # Step 1: Run coverage collection (generates snapshot only)
    # Note: Inline report generation (--json-report-output with cover)
    # has issues on macOS ARM64, so we generate reports separately.
    # Also, dotCover requires space-separated options, not = syntax.
    cover_cmd = [
        "dotCover",
        "cover",
        "--snapshot-output", str(snapshot),
        "--target-working-directory", str(repo_path),
        "--",
        "dotnet", "test", test_target, "--no-build",
    ]

    print(f"Running: {' '.join(cover_cmd)}")

    try:
        result = subprocess.run(
            cover_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            print(f"dotCover coverage warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr)
            # Continue anyway - may have partial results

    except subprocess.TimeoutExpired:
        print("dotCover coverage collection timed out after 10 minutes")
        return None, None
    except FileNotFoundError:
        print("dotCover not found. Install with: dotnet tool install --global JetBrains.dotCover.CommandLineTools")
        return None, None

    if not snapshot.exists():
        print(f"No coverage snapshot generated at {snapshot}")
        return None, None

    # Step 2: Generate JSON and XML reports from snapshot
    # Note: dotCover report command may hang on macOS ARM64, use timeout.
    # Use space-separated options, not = syntax.
    report_cmd = [
        "dotCover",
        "report",
        "--snapshot-source", str(snapshot),
        "--json-report-output", str(json_report),
        "--xml-report-output", str(xml_report),
    ]

    print(f"Generating reports: {' '.join(report_cmd)}")

    try:
        result = subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for report generation
        )

        if result.returncode != 0:
            print(f"dotCover report warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr)

    except subprocess.TimeoutExpired:
        print("Warning: dotCover report generation timed out (known macOS ARM64 issue)")
        print(f"Coverage snapshot saved at {snapshot}")
        print("Reports can be generated manually on a supported platform with:")
        print(f"  dotCover report --snapshot-source {snapshot} --json-report-output report.json")
        # Return snapshot path so caller knows coverage was collected
        return {"_snapshot_only": True, "_snapshot_path": str(snapshot)}, None
    except FileNotFoundError:
        # Should not happen if cover worked
        return None, None

    # Parse JSON report
    if json_report.exists():
        try:
            with open(json_report) as f:
                report = json.load(f)
            return report, xml_report if xml_report.exists() else None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON report: {e}")

    return None, None


def run_dotcover_docker(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
) -> tuple[dict | None, Path | None]:
    """Run dotCover coverage analysis in Docker container.

    This bypasses the macOS ARM64 bug by running dotCover in a Linux x64 container.

    Args:
        repo_path: Path to the repository to analyze
        output_dir: Directory for output files
        test_project: Optional specific test project to run

    Returns:
        Tuple of (parsed JSON report, detailed XML path if available)
    """
    # Ensure paths are absolute for Docker volume mounts
    repo_path = repo_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    json_report = output_dir / "coverage.json"
    xml_report = output_dir / "coverage.xml"
    snapshot = output_dir / "coverage.dcvr"

    # Determine test target relative to repo root
    if test_project:
        # Make test project path relative to repo for container
        try:
            test_target = str(test_project.relative_to(repo_path))
        except ValueError:
            test_target = str(test_project)
    else:
        test_target = "."

    # Step 1: Build the solution in the container first
    # Use --platform linux/amd64 to force x64 execution (bypasses ARM64 bug)
    build_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",
        "-v", f"{repo_path}:/repo",
        "-w", "/repo",
        "--entrypoint", "dotnet",
        DOCKER_IMAGE,
        "build",
    ]

    print(f"Building project in Docker: {' '.join(build_cmd)}")

    try:
        result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute build timeout
        )
        if result.returncode != 0:
            print(f"Build warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr[:500])
    except subprocess.TimeoutExpired:
        print("Docker build timed out after 5 minutes")
        return None, None
    except FileNotFoundError:
        print("Docker not found. Install Docker to use --docker mode.")
        return None, None

    # Step 2: Run coverage collection in Docker
    # Use --platform linux/amd64 to force x64 execution (bypasses ARM64 bug)
    cover_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",
        "-v", f"{repo_path}:/repo",
        "-v", f"{output_dir}:/output",
        "-w", "/repo",
        DOCKER_IMAGE,
        "cover",
        "--snapshot-output", "/output/coverage.dcvr",
        "--target-working-directory", "/repo",
        "--",
        "dotnet", "test", test_target, "--no-build",
    ]

    print(f"Running dotCover in Docker: {' '.join(cover_cmd)}")

    try:
        result = subprocess.run(
            cover_cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            print(f"dotCover coverage warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr[:500])

    except subprocess.TimeoutExpired:
        print("dotCover coverage collection timed out after 10 minutes")
        return None, None
    except FileNotFoundError:
        print("Docker not found. Install Docker to use --docker mode.")
        return None, None

    if not snapshot.exists():
        print(f"No coverage snapshot generated at {snapshot}")
        return None, None

    # Step 3: Generate reports from snapshot in Docker
    # Use --platform linux/amd64 to force x64 execution (bypasses ARM64 bug)
    report_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",
        "-v", f"{output_dir}:/output",
        "-w", "/output",
        DOCKER_IMAGE,
        "report",
        "--snapshot-source", "/output/coverage.dcvr",
        "--json-report-output", "/output/coverage.json",
        "--xml-report-output", "/output/coverage.xml",
    ]

    print(f"Generating reports in Docker: {' '.join(report_cmd)}")

    try:
        result = subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for report generation
        )

        if result.returncode != 0:
            print(f"dotCover report warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr[:500])

    except subprocess.TimeoutExpired:
        print("dotCover report generation timed out")
        return {"_snapshot_only": True, "_snapshot_path": str(snapshot)}, None
    except FileNotFoundError:
        return None, None

    # Parse JSON report
    if json_report.exists():
        try:
            with open(json_report) as f:
                report = json.load(f)
            return report, xml_report if xml_report.exists() else None
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON report: {e}")

    return None, None


def parse_source_file_mapping(xml_path: Path, repo_path: Path) -> dict[str, str]:
    """Parse DetailedXML to extract type-to-file mappings.

    Args:
        xml_path: Path to DetailedXML report
        repo_path: Repository root for path normalization

    Returns:
        Dict mapping "Assembly.TypeName" to normalized file path
    """
    mapping: dict[str, str] = {}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # DetailedXML has structure: Root/Assembly/Namespace/Type with File attributes
        for assembly in root.findall(".//Assembly"):
            assembly_name = assembly.get("Name", "")
            for type_elem in assembly.findall(".//Type"):
                type_name = type_elem.get("Name", "")
                # Look for source file in various attributes/children
                file_path = type_elem.get("File") or type_elem.get("SourceFile")

                # Also check for File child elements
                if not file_path:
                    file_elem = type_elem.find(".//File")
                    if file_elem is not None:
                        file_path = file_elem.get("Path") or file_elem.text

                if file_path and type_name:
                    # Normalize the path
                    normalized = normalize_file_path(file_path, repo_path)
                    if normalized:
                        key = f"{assembly_name}.{type_name}"
                        mapping[key] = normalized

    except ET.ParseError as e:
        print(f"Warning: Failed to parse detailed XML: {e}")

    return mapping


def extract_coverage_data(
    report: dict,
    file_mapping: dict[str, str] | None = None,
) -> tuple[list[AssemblyCoverage], list[TypeCoverage], list[MethodCoverage]]:
    """Extract coverage data from dotCover JSON report.

    Args:
        report: Parsed dotCover JSON report
        file_mapping: Optional type-to-file mapping from DetailedXML

    Returns:
        Tuple of (assemblies, types, methods) coverage lists
    """
    assemblies: list[AssemblyCoverage] = []
    types: list[TypeCoverage] = []
    methods: list[MethodCoverage] = []

    file_mapping = file_mapping or {}

    def process_node(
        node: dict,
        assembly_name: str = "",
        namespace: str | None = None,
        type_name: str = "",
    ) -> None:
        """Recursively process coverage tree nodes."""
        kind = node.get("Kind", "")
        name = node.get("Name", "")
        covered = node.get("CoveredStatements", 0)
        total = node.get("TotalStatements", 0)
        pct = node.get("CoveragePercent", 0.0)

        if kind == "Assembly":
            assemblies.append(AssemblyCoverage(
                name=name,
                covered_statements=covered,
                total_statements=total,
                coverage_pct=pct,
            ))
            assembly_name = name

        elif kind == "Namespace":
            namespace = name

        elif kind == "Type":
            # Look up file path from mapping
            key = f"{assembly_name}.{name}"
            file_path = file_mapping.get(key)

            types.append(TypeCoverage(
                assembly=assembly_name,
                namespace=namespace,
                name=name,
                file_path=file_path,
                covered_statements=covered,
                total_statements=total,
                coverage_pct=pct,
            ))
            type_name = name

        elif kind == "Method":
            methods.append(MethodCoverage(
                assembly=assembly_name,
                type_name=type_name,
                name=name,
                covered_statements=covered,
                total_statements=total,
                coverage_pct=pct,
            ))

        # Process children
        for child in node.get("Children", []):
            process_node(child, assembly_name, namespace, type_name)

    # Process root children (assemblies)
    for child in report.get("Children", []):
        process_node(child)

    return assemblies, types, methods


def analyze_repo(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
    use_docker: bool = False,
) -> dict:
    """Run dotCover analysis on the repository.

    Args:
        repo_path: Path to repository
        output_dir: Directory for output files
        test_project: Optional specific test project
        use_docker: Use Docker container (bypasses macOS ARM64 bug)

    Returns:
        Analysis data dict for envelope
    """
    # Get tool version
    tool_version = get_dotcover_version()

    # Find test project if not specified
    if not test_project:
        test_project = find_test_project(repo_path)
        if test_project:
            print(f"Found test project: {test_project}")

    # Check if dotCover is available (skip check for Docker mode)
    if not use_docker and shutil.which("dotCover") is None:
        print("Warning: dotCover not found. Returning empty analysis.")
        print("Install with: dotnet tool install --global JetBrains.dotCover.CommandLineTools")
        print("Or use --docker mode to run in a container.")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "summary": {
                "total_assemblies": 0,
                "total_types": 0,
                "total_methods": 0,
                "covered_statements": 0,
                "total_statements": 0,
                "statement_coverage_pct": 0.0,
                "error": "dotCover not installed",
            },
            "assemblies": [],
            "types": [],
            "methods": [],
        }

    # Run dotCover (use Docker to bypass macOS ARM64 bug if requested)
    if use_docker:
        print("Running dotCover in Docker container (bypasses ARM64 bug)")
        report, xml_path = run_dotcover_docker(repo_path, output_dir, test_project)
    else:
        report, xml_path = run_dotcover(repo_path, output_dir, test_project)

    if not report:
        print("Warning: No coverage report generated")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "summary": {
                "total_assemblies": 0,
                "total_types": 0,
                "total_methods": 0,
                "covered_statements": 0,
                "total_statements": 0,
                "statement_coverage_pct": 0.0,
                "error": "No coverage data collected",
            },
            "assemblies": [],
            "types": [],
            "methods": [],
        }

    # Handle snapshot-only case (macOS ARM64 report generation bug)
    if report.get("_snapshot_only"):
        print("Warning: Coverage snapshot collected but report generation failed")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "summary": {
                "total_assemblies": 0,
                "total_types": 0,
                "total_methods": 0,
                "covered_statements": 0,
                "total_statements": 0,
                "statement_coverage_pct": 0.0,
                "snapshot_path": report.get("_snapshot_path"),
                "warning": "Report generation failed (macOS ARM64 bug), snapshot saved",
            },
            "assemblies": [],
            "types": [],
            "methods": [],
        }

    # Parse source file mapping if available
    file_mapping = None
    if xml_path:
        file_mapping = parse_source_file_mapping(xml_path, repo_path)
        print(f"Mapped {len(file_mapping)} types to source files")

    # Extract coverage data
    assemblies, types_cov, methods_cov = extract_coverage_data(report, file_mapping)

    # Get summary from report root
    covered = report.get("CoveredStatements", 0)
    total = report.get("TotalStatements", 0)
    pct = report.get("CoveragePercent", 0.0)

    return {
        "tool": TOOL_NAME,
        "tool_version": tool_version,
        "summary": {
            "total_assemblies": len(assemblies),
            "total_types": len(types_cov),
            "total_methods": len(methods_cov),
            "covered_statements": covered,
            "total_statements": total,
            "statement_coverage_pct": pct,
        },
        "assemblies": [
            {
                "name": a.name,
                "covered_statements": a.covered_statements,
                "total_statements": a.total_statements,
                "statement_coverage_pct": a.coverage_pct,
            }
            for a in assemblies
        ],
        "types": [
            {
                "assembly": t.assembly,
                "namespace": t.namespace,
                "name": t.name,
                "file_path": t.file_path,
                "covered_statements": t.covered_statements,
                "total_statements": t.total_statements,
                "statement_coverage_pct": t.coverage_pct,
            }
            for t in types_cov
        ],
        "methods": [
            {
                "assembly": m.assembly,
                "type_name": m.type_name,
                "name": m.name,
                "covered_statements": m.covered_statements,
                "total_statements": m.total_statements,
                "statement_coverage_pct": m.coverage_pct,
            }
            for m in methods_cov
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} analysis tool")
    add_common_args(parser, default_repo_path=None)

    # Tool-specific arguments
    parser.add_argument("--test-project", type=Path, default=None,
                        help="Path to test project (.csproj)")
    parser.add_argument("--docker", action="store_true",
                        help="Run dotCover in Docker container (bypasses macOS ARM64 bug)")
    args = parser.parse_args()

    # Validate common args (uses lenient commit mode for orchestrator trust)
    common = validate_common_args(args, commit_config=CommitResolutionConfig.lenient())

    # Run analysis
    print(f"Analyzing: {common.repo_path}")
    data = analyze_repo(
        common.repo_path.resolve(),
        common.output_dir,
        args.test_project,
        use_docker=args.docker,
    )

    # Create envelope using common formatter
    envelope = create_envelope(
        data,
        tool_name=TOOL_NAME,
        tool_version=data.get("tool_version", "unknown"),
        run_id=common.run_id,
        repo_id=common.repo_id,
        branch=common.branch,
        commit=common.commit,
        schema_version=SCHEMA_VERSION,
    )

    # Write output
    common.output_path.write_text(json.dumps(envelope, indent=2))

    # Print summary
    summary = data.get("summary", {})
    print(f"Assemblies: {summary.get('total_assemblies', 0)}")
    print(f"Types: {summary.get('total_types', 0)}")
    print(f"Methods: {summary.get('total_methods', 0)}")
    print(f"Coverage: {summary.get('statement_coverage_pct', 0):.1f}% ({summary.get('covered_statements', 0)}/{summary.get('total_statements', 0)} statements)")
    print(f"Output: {common.output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
