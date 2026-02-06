#!/usr/bin/env python3
"""CLI entry point for DependenSee .NET dependency analysis.

DependenSee analyzes .NET solutions and projects to extract:
- Project-to-project references
- NuGet package dependencies
- Dependency graph structure
- Circular dependency detection

Installation: dotnet tool install -g DependenSee
GitHub: https://github.com/madushans/DependenSee
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

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from common.path_normalization import normalize_file_path
from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope, get_current_timestamp

TOOL_NAME = "dependensee"
SCHEMA_VERSION = "1.0.0"


@dataclass
class ProjectInfo:
    """Information about a .NET project."""
    name: str
    path: str
    target_framework: str | None
    project_references: list[str]
    package_references: list[dict[str, str]]


@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    id: str
    name: str
    type: str  # "project" or "package"
    version: str | None = None


@dataclass
class DependencyEdge:
    """An edge in the dependency graph."""
    source: str
    target: str
    type: str  # "project_reference" or "package_reference"


def check_dotnet_available() -> bool:
    """Check if dotnet CLI is available."""
    return shutil.which("dotnet") is not None


def check_dependensee_installed() -> bool:
    """Check if DependenSee is installed as a dotnet tool."""
    try:
        result = subprocess.run(
            ["dotnet", "tool", "list", "-g"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "dependensee" in result.stdout.lower()
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_dependensee() -> bool:
    """Install DependenSee as a global dotnet tool."""
    try:
        result = subprocess.run(
            ["dotnet", "tool", "install", "-g", "DependenSee"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def get_dependensee_version() -> str:
    """Get the installed DependenSee version."""
    try:
        result = subprocess.run(
            ["dependensee", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Parse version from output
            version_line = result.stdout.strip().split("\n")[0]
            # Try to extract version number
            parts = version_line.split()
            for part in parts:
                if any(c.isdigit() for c in part):
                    return part.strip()
            return version_line
    except subprocess.SubprocessError:
        pass
    return "unknown"


def find_solution_files(repo_path: Path) -> list[Path]:
    """Find all .sln files in the repository."""
    return sorted(repo_path.rglob("*.sln"))


def find_project_files(repo_path: Path) -> list[Path]:
    """Find all .csproj and .fsproj files in the repository."""
    csproj_files = list(repo_path.rglob("*.csproj"))
    fsproj_files = list(repo_path.rglob("*.fsproj"))
    vbproj_files = list(repo_path.rglob("*.vbproj"))
    return sorted(csproj_files + fsproj_files + vbproj_files)


def run_dependensee(target_path: Path, output_path: Path) -> dict | None:
    """Run DependenSee and return parsed JSON output."""
    try:
        # DependenSee command for JSON output
        cmd = [
            "dependensee",
            "--path", str(target_path),
            "--output", str(output_path),
            "--format", "json",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        if result.returncode == 0 and output_path.exists():
            return json.loads(output_path.read_text())

        # If DependenSee failed, return None
        return None
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return None


def parse_project_file(project_path: Path, repo_path: Path) -> ProjectInfo | None:
    """Parse a .csproj/.fsproj file to extract dependency information."""
    try:
        tree = ET.parse(project_path)
        root = tree.getroot()

        # Handle both old-style and SDK-style projects
        ns = {"": "http://schemas.microsoft.com/developer/msbuild/2003"}

        # Try to find TargetFramework(s)
        target_framework = None
        for tf_elem in root.iter():
            if tf_elem.tag.endswith("TargetFramework") or tf_elem.tag.endswith("TargetFrameworks"):
                target_framework = tf_elem.text
                break

        # Find project references
        project_references = []
        for pr in root.iter():
            if pr.tag.endswith("ProjectReference"):
                include = pr.get("Include")
                if include:
                    # Normalize path separators (csproj may use Windows backslashes)
                    include_normalized = include.replace("\\", "/")
                    # Resolve the reference path relative to the project file location
                    # This handles relative paths like "../MyApp.Core/MyApp.Core.csproj"
                    ref_path = (project_path.parent / include_normalized).resolve()
                    try:
                        if ref_path.is_relative_to(repo_path):
                            # Use relative_to for clean path without ".." components
                            rel_path = ref_path.relative_to(repo_path).as_posix()
                            project_references.append(rel_path)
                        else:
                            project_references.append(include_normalized)
                    except ValueError:
                        # Path is outside repo - keep original
                        project_references.append(include_normalized)

        # Find package references
        package_references = []
        for pr in root.iter():
            if pr.tag.endswith("PackageReference"):
                name = pr.get("Include")
                version = pr.get("Version")
                if name:
                    pkg = {"name": name}
                    if version:
                        pkg["version"] = version
                    package_references.append(pkg)

        # Get project name from file
        project_name = project_path.stem
        rel_path = normalize_file_path(str(project_path), repo_path)

        return ProjectInfo(
            name=project_name,
            path=rel_path,
            target_framework=target_framework,
            project_references=project_references,
            package_references=package_references,
        )
    except ET.ParseError:
        return None


def detect_circular_dependencies(projects: list[ProjectInfo]) -> list[list[str]]:
    """Detect circular dependencies in the project graph.

    Returns a list of cycles, where each cycle is a list of project paths.
    """
    # Build adjacency list
    path_to_project = {p.path: p for p in projects}
    adjacency: dict[str, set[str]] = {p.path: set(p.project_references) for p in projects}

    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> None:
        if node in rec_stack:
            # Found a cycle - extract it
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adjacency.get(node, set()):
            if neighbor in path_to_project:  # Only follow known projects
                dfs(neighbor)

        path.pop()
        rec_stack.remove(node)

    for project_path in adjacency:
        visited.clear()
        rec_stack.clear()
        path.clear()
        dfs(project_path)

    # Deduplicate cycles (same cycle can be found from different starting points)
    unique_cycles = []
    seen_cycle_sets = set()
    for cycle in cycles:
        cycle_set = frozenset(cycle)
        if cycle_set not in seen_cycle_sets:
            seen_cycle_sets.add(cycle_set)
            unique_cycles.append(cycle)

    return unique_cycles


def build_dependency_graph(projects: list[ProjectInfo]) -> dict:
    """Build a dependency graph from project information."""
    nodes = []
    edges = []
    seen_packages = set()

    # Add project nodes
    for project in projects:
        nodes.append({
            "id": project.path,
            "name": project.name,
            "type": "project",
            "target_framework": project.target_framework,
        })

        # Add edges for project references
        for ref in project.project_references:
            edges.append({
                "source": project.path,
                "target": ref,
                "type": "project_reference",
            })

        # Add package nodes and edges
        for pkg in project.package_references:
            pkg_id = f"nuget:{pkg['name']}"
            if pkg_id not in seen_packages:
                nodes.append({
                    "id": pkg_id,
                    "name": pkg["name"],
                    "type": "package",
                    "version": pkg.get("version"),
                })
                seen_packages.add(pkg_id)

            edges.append({
                "source": project.path,
                "target": pkg_id,
                "type": "package_reference",
            })

    return {
        "nodes": nodes,
        "edges": edges,
    }


def analyze_repo(repo_path: Path, temp_dir: Path) -> dict:
    """Analyze the repository for .NET dependencies.

    Uses DependenSee if available, otherwise falls back to direct parsing.
    """
    projects = []
    dependensee_output = None
    tool_version = "fallback-parser"

    # Find project files
    project_files = find_project_files(repo_path)

    if not project_files:
        # No .NET projects found
        return {
            "tool": TOOL_NAME,
            "tool_version": tool_version,
            "projects": [],
            "dependency_graph": {"nodes": [], "edges": []},
            "circular_dependencies": [],
            "summary": {
                "project_count": 0,
                "package_count": 0,
                "reference_count": 0,
                "circular_dependency_count": 0,
            },
        }

    # Try to use DependenSee if available
    if check_dotnet_available():
        if not check_dependensee_installed():
            print("DependenSee not installed. Attempting to install...")
            if install_dependensee():
                print("DependenSee installed successfully.")
            else:
                print("Failed to install DependenSee. Using fallback parser.")

        if check_dependensee_installed():
            tool_version = get_dependensee_version()

            # Try solutions first, then individual projects
            solutions = find_solution_files(repo_path)
            if solutions:
                output_path = temp_dir / "dependensee_output.json"
                dependensee_output = run_dependensee(solutions[0], output_path)

    # Parse project files directly (fallback or supplement)
    for proj_file in project_files:
        proj_info = parse_project_file(proj_file, repo_path)
        if proj_info:
            projects.append(proj_info)

    # Build dependency graph
    dependency_graph = build_dependency_graph(projects)

    # Detect circular dependencies
    circular_deps = detect_circular_dependencies(projects)

    # Calculate summary statistics
    total_packages = set()
    total_references = 0
    for project in projects:
        total_references += len(project.project_references)
        for pkg in project.package_references:
            total_packages.add(pkg["name"])

    # Format projects for output
    projects_output = []
    for project in projects:
        projects_output.append({
            "name": project.name,
            "path": project.path,
            "target_framework": project.target_framework,
            "project_references": project.project_references,
            "package_references": project.package_references,
        })

    return {
        "tool": TOOL_NAME,
        "tool_version": tool_version,
        "projects": projects_output,
        "dependency_graph": dependency_graph,
        "circular_dependencies": circular_deps,
        "summary": {
            "project_count": len(projects),
            "package_count": len(total_packages),
            "reference_count": total_references,
            "circular_dependency_count": len(circular_deps),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze .NET project dependencies using DependenSee"
    )
    add_common_args(parser)
    args = parser.parse_args()

    commit_config = CommitResolutionConfig.strict_with_fallback(
        Path(__file__).parent.parent
    )
    common = validate_common_args(args, commit_config=commit_config)

    print(f"Analyzing: {common.repo_path}")

    # Create temp directory for DependenSee output
    temp_dir = common.output_dir / ".temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Run analysis
        data = analyze_repo(common.repo_path.resolve(), temp_dir)

        # Create envelope
        timestamp = get_current_timestamp()
        output = create_envelope(
            data,
            tool_name=TOOL_NAME,
            tool_version=data.get("tool_version", "unknown"),
            run_id=common.run_id,
            repo_id=common.repo_id,
            branch=common.branch,
            commit=common.commit,
            timestamp=timestamp,
        )

        # Write output
        common.output_path.write_text(json.dumps(output, indent=2))

        # Print summary
        summary = data.get("summary", {})
        print(f"Projects found: {summary.get('project_count', 0)}")
        print(f"Package dependencies: {summary.get('package_count', 0)}")
        print(f"Project references: {summary.get('reference_count', 0)}")
        print(f"Circular dependencies: {summary.get('circular_dependency_count', 0)}")
        print(f"Output: {common.output_path}")

        return 0
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
