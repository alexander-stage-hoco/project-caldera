"""Coverage checks for dependensee.

Validates that the tool provides complete output:
- All projects analyzed
- Graph nodes and edges populated
- Summary statistics present
"""

from __future__ import annotations


def check_projects_analyzed(output: dict, ground_truth: dict | None) -> dict:
    """Check that projects were analyzed."""
    data = output.get("data", {})
    projects = data.get("projects", [])

    if not projects:
        return {
            "check_id": "coverage.projects_analyzed",
            "status": "warn",
            "message": "No .NET projects found in output",
        }

    return {
        "check_id": "coverage.projects_analyzed",
        "status": "pass",
        "message": f"{len(projects)} projects analyzed",
    }


def check_graph_populated(output: dict, ground_truth: dict | None) -> dict:
    """Check that dependency graph has nodes and edges."""
    data = output.get("data", {})
    graph = data.get("dependency_graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return {
            "check_id": "coverage.graph_populated",
            "status": "warn",
            "message": "Dependency graph has no nodes",
        }

    return {
        "check_id": "coverage.graph_populated",
        "status": "pass",
        "message": f"Graph has {len(nodes)} nodes and {len(edges)} edges",
    }


def check_summary_present(output: dict, ground_truth: dict | None) -> dict:
    """Check that summary statistics are present."""
    data = output.get("data", {})
    summary = data.get("summary", {})

    required_fields = ["project_count", "package_count", "reference_count", "circular_dependency_count"]
    missing = [f for f in required_fields if f not in summary]

    if missing:
        return {
            "check_id": "coverage.summary_present",
            "status": "fail",
            "message": f"Missing summary fields: {missing}",
        }

    return {
        "check_id": "coverage.summary_present",
        "status": "pass",
        "message": "All summary statistics present",
    }


def check_all_projects_have_path(output: dict, ground_truth: dict | None) -> dict:
    """Check that all projects have valid paths."""
    data = output.get("data", {})
    projects = data.get("projects", [])

    missing_paths = []
    for i, p in enumerate(projects):
        if not p.get("path"):
            missing_paths.append(f"project[{i}]")

    if missing_paths:
        return {
            "check_id": "coverage.project_paths_present",
            "status": "fail",
            "message": f"Projects missing paths: {missing_paths[:5]}",
        }

    if not projects:
        return {
            "check_id": "coverage.project_paths_present",
            "status": "pass",
            "message": "No projects to check",
        }

    return {
        "check_id": "coverage.project_paths_present",
        "status": "pass",
        "message": f"All {len(projects)} projects have valid paths",
    }
