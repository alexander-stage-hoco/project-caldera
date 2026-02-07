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

# Backend choices
BACKEND_DOTCOVER = "dotcover"
BACKEND_COVERLET = "coverlet"


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


def get_coverlet_version() -> str:
    """Get Coverlet version from dotnet SDK.

    Coverlet is included with the .NET SDK, so we report the SDK version.
    """
    try:
        result = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"coverlet (dotnet {result.stdout.strip()})"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "coverlet (unknown)"


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


def run_coverlet(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
) -> tuple[dict | None, Path | None]:
    """Run Coverlet coverage analysis using dotnet test.

    Coverlet is a cross-platform code coverage library for .NET that works
    natively on macOS ARM64 without Docker or QEMU emulation.

    Args:
        repo_path: Path to the repository to analyze
        output_dir: Directory for output files
        test_project: Optional specific test project to run

    Returns:
        Tuple of (parsed coverage data dict, cobertura xml path)
    """
    # Ensure output_dir is absolute
    output_dir = output_dir.resolve()
    results_dir = output_dir / "TestResults"

    # Determine what to test
    test_target = str(test_project) if test_project else str(repo_path)

    # Run dotnet test with Coverlet collector
    # XPlat Code Coverage is the built-in Coverlet data collector
    test_cmd = [
        "dotnet", "test", test_target,
        "--collect:XPlat Code Coverage",
        f"--results-directory={results_dir}",
    ]

    print(f"Running: {' '.join(test_cmd)}")

    try:
        result = subprocess.run(
            test_cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            print(f"dotnet test warning (exit {result.returncode}):")
            if result.stderr:
                print(result.stderr[:1000])
            # Continue anyway - may have partial results

    except subprocess.TimeoutExpired:
        print("dotnet test timed out after 10 minutes")
        return None, None
    except FileNotFoundError:
        print("dotnet not found. Install .NET SDK to use Coverlet backend.")
        return None, None

    # Find the generated coverage.cobertura.xml file
    # Coverlet creates: TestResults/<guid>/coverage.cobertura.xml
    cobertura_files = list(results_dir.glob("*/coverage.cobertura.xml"))
    if not cobertura_files:
        print(f"No Cobertura coverage file found in {results_dir}")
        return None, None

    # Use the most recent one if multiple exist
    cobertura_path = max(cobertura_files, key=lambda p: p.stat().st_mtime)
    print(f"Found coverage file: {cobertura_path}")

    # Parse Cobertura XML
    coverage_data = parse_cobertura_xml(cobertura_path, repo_path)

    return coverage_data, cobertura_path


def parse_cobertura_xml(xml_path: Path, repo_path: Path) -> dict | None:
    """Parse Cobertura XML coverage report.

    Cobertura XML structure:
    <coverage>
      <packages>
        <package name="AssemblyName">
          <classes>
            <class name="Namespace.ClassName" filename="path/to/file.cs">
              <methods>
                <method name="MethodName">
                  <lines>...</lines>
                </method>
              </methods>
              <lines>
                <line number="1" hits="1"/>
              </lines>
            </class>
          </classes>
        </package>
      </packages>
    </coverage>

    Args:
        xml_path: Path to Cobertura XML file
        repo_path: Repository root for path normalization

    Returns:
        Dict with coverage data in dotCover-compatible format, or None on error
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Failed to parse Cobertura XML: {e}")
        return None

    # Get overall coverage from root attributes
    line_rate = float(root.get("line-rate", "0"))
    branch_rate = float(root.get("branch-rate", "0"))
    lines_covered = int(root.get("lines-covered", "0"))
    lines_valid = int(root.get("lines-valid", "0"))

    # Build coverage data structures
    assemblies_dict: dict[str, dict] = {}
    types_list: list[dict] = []
    methods_list: list[dict] = []

    packages = root.find("packages")
    if packages is None:
        print("No packages found in Cobertura XML")
        return {
            "CoveredStatements": 0,
            "TotalStatements": 0,
            "CoveragePercent": 0.0,
            "Children": [],
        }

    for package in packages.findall("package"):
        package_name = package.get("name", "Unknown")
        pkg_line_rate = float(package.get("line-rate", "0"))
        pkg_complexity = float(package.get("complexity", "0"))

        # Track assembly-level stats
        if package_name not in assemblies_dict:
            assemblies_dict[package_name] = {
                "name": package_name,
                "covered_lines": 0,
                "total_lines": 0,
            }

        classes = package.find("classes")
        if classes is None:
            continue

        for cls in classes.findall("class"):
            class_name = cls.get("name", "Unknown")
            filename = cls.get("filename", "")
            cls_line_rate = float(cls.get("line-rate", "0"))
            cls_complexity = float(cls.get("complexity", "0"))

            # Extract namespace from class name
            namespace = None
            type_name = class_name
            if "." in class_name:
                parts = class_name.rsplit(".", 1)
                namespace = parts[0]
                type_name = parts[1]

            # Count lines in this class
            lines_elem = cls.find("lines")
            cls_covered = 0
            cls_total = 0
            if lines_elem is not None:
                for line in lines_elem.findall("line"):
                    cls_total += 1
                    if int(line.get("hits", "0")) > 0:
                        cls_covered += 1

            # Normalize file path
            normalized_path = None
            if filename:
                normalized_path = normalize_file_path(filename, repo_path)

            # Add type coverage
            types_list.append({
                "assembly": package_name,
                "namespace": namespace,
                "name": type_name,
                "file_path": normalized_path,
                "covered_statements": cls_covered,
                "total_statements": cls_total,
                "statement_coverage_pct": cls_line_rate * 100,
            })

            # Update assembly stats
            assemblies_dict[package_name]["covered_lines"] += cls_covered
            assemblies_dict[package_name]["total_lines"] += cls_total

            # Process methods
            methods_elem = cls.find("methods")
            if methods_elem is not None:
                for method in methods_elem.findall("method"):
                    method_name = method.get("name", "Unknown")
                    method_line_rate = float(method.get("line-rate", "0"))

                    # Count method lines
                    method_lines = method.find("lines")
                    method_covered = 0
                    method_total = 0
                    if method_lines is not None:
                        for line in method_lines.findall("line"):
                            method_total += 1
                            if int(line.get("hits", "0")) > 0:
                                method_covered += 1

                    methods_list.append({
                        "assembly": package_name,
                        "type_name": type_name,
                        "name": method_name,
                        "covered_statements": method_covered,
                        "total_statements": method_total,
                        "statement_coverage_pct": method_line_rate * 100,
                    })

    # Build dotCover-compatible structure for extract_coverage_data
    # We'll bypass that and return our pre-processed data
    return {
        "_coverlet_data": True,
        "line_rate": line_rate,
        "branch_rate": branch_rate,
        "lines_covered": lines_covered,
        "lines_valid": lines_valid,
        "assemblies": [
            {
                "name": asm["name"],
                "covered_statements": asm["covered_lines"],
                "total_statements": asm["total_lines"],
                "statement_coverage_pct": (asm["covered_lines"] / asm["total_lines"] * 100)
                    if asm["total_lines"] > 0 else 0.0,
            }
            for asm in assemblies_dict.values()
        ],
        "types": types_list,
        "methods": methods_list,
    }


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
    # Note: dotCover 2024.3.0 uses --TargetExecutable/--TargetArguments syntax
    cover_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",
        "-v", f"{repo_path}:/repo",
        "-v", f"{output_dir}:/output",
        "-w", "/repo",
        DOCKER_IMAGE,
        "cover",
        f"--TargetExecutable=/usr/share/dotnet/dotnet",
        f"--TargetArguments=test {test_target} --no-build",
        "--TargetWorkingDir=/repo",
        "--Output=/output/coverage.dcvr",
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
    # Note: dotCover 2024.3.0 uses --Source/--Output/--ReportType syntax
    report_cmd = [
        "docker", "run", "--rm",
        "--platform", "linux/amd64",
        "-v", f"{output_dir}:/output",
        "-w", "/output",
        DOCKER_IMAGE,
        "report",
        "--Source=/output/coverage.dcvr",
        "--Output=/output/coverage.json,/output/coverage.xml",
        "--ReportType=JSON,XML",
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
    backend: str = BACKEND_DOTCOVER,
) -> dict:
    """Run coverage analysis on the repository.

    Args:
        repo_path: Path to repository
        output_dir: Directory for output files
        test_project: Optional specific test project
        use_docker: Use Docker container (bypasses macOS ARM64 bug, dotcover only)
        backend: Coverage backend to use ("dotcover" or "coverlet")

    Returns:
        Analysis data dict for envelope
    """
    # Find test project if not specified
    if not test_project:
        test_project = find_test_project(repo_path)
        if test_project:
            print(f"Found test project: {test_project}")

    # Handle Coverlet backend
    if backend == BACKEND_COVERLET:
        return analyze_repo_coverlet(repo_path, output_dir, test_project)

    # Handle dotCover backend
    return analyze_repo_dotcover(repo_path, output_dir, test_project, use_docker)


def analyze_repo_coverlet(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
) -> dict:
    """Run Coverlet coverage analysis.

    Args:
        repo_path: Path to repository
        output_dir: Directory for output files
        test_project: Optional specific test project

    Returns:
        Analysis data dict for envelope
    """
    tool_version = get_coverlet_version()

    # Check if dotnet is available
    if shutil.which("dotnet") is None:
        print("Warning: dotnet not found. Install .NET SDK to use Coverlet backend.")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "backend": BACKEND_COVERLET,
            "summary": {
                "total_assemblies": 0,
                "total_types": 0,
                "total_methods": 0,
                "covered_statements": 0,
                "total_statements": 0,
                "statement_coverage_pct": 0.0,
                "error": "dotnet SDK not installed",
            },
            "assemblies": [],
            "types": [],
            "methods": [],
        }

    # Run Coverlet
    print(f"Running Coverlet coverage analysis (backend: {BACKEND_COVERLET})")
    result, cobertura_path = run_coverlet(repo_path, output_dir, test_project)

    if not result:
        print("Warning: No coverage report generated")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "backend": BACKEND_COVERLET,
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

    # Coverlet returns pre-processed data
    assemblies = result.get("assemblies", [])
    types = result.get("types", [])
    methods = result.get("methods", [])

    # Calculate totals from line counts
    total_covered = result.get("lines_covered", 0)
    total_lines = result.get("lines_valid", 0)
    line_rate = result.get("line_rate", 0.0)

    return {
        "tool": TOOL_NAME,
        "tool_version": tool_version,
        "backend": BACKEND_COVERLET,
        "summary": {
            "total_assemblies": len(assemblies),
            "total_types": len(types),
            "total_methods": len(methods),
            "covered_statements": total_covered,
            "total_statements": total_lines,
            "statement_coverage_pct": line_rate * 100,
        },
        "assemblies": assemblies,
        "types": types,
        "methods": methods,
    }


def analyze_repo_dotcover(
    repo_path: Path,
    output_dir: Path,
    test_project: Path | None = None,
    use_docker: bool = False,
) -> dict:
    """Run dotCover coverage analysis.

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

    # Check if dotCover is available (skip check for Docker mode)
    if not use_docker and shutil.which("dotCover") is None:
        print("Warning: dotCover not found. Returning empty analysis.")
        print("Install with: dotnet tool install --global JetBrains.dotCover.CommandLineTools")
        print("Or use --docker mode to run in a container.")
        print("Or use --backend coverlet for cross-platform support.")
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "backend": BACKEND_DOTCOVER,
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
            "backend": BACKEND_DOTCOVER,
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
            "backend": BACKEND_DOTCOVER,
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
        "backend": BACKEND_DOTCOVER,
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
    parser.add_argument("--backend", choices=[BACKEND_DOTCOVER, BACKEND_COVERLET],
                        default=BACKEND_DOTCOVER,
                        help="Coverage backend to use (default: dotcover)")
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
        backend=args.backend,
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
