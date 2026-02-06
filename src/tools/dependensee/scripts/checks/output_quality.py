"""Output quality checks for dependensee.

Validates the structure and format of the tool output:
- Envelope format compliance
- Schema validation
- Data consistency
"""

from __future__ import annotations


def check_envelope_present(output: dict, ground_truth: dict | None) -> dict:
    """Check that output has proper envelope structure."""
    if "metadata" not in output:
        return {
            "check_id": "output_quality.envelope_present",
            "status": "fail",
            "message": "Missing 'metadata' section in envelope",
        }

    if "data" not in output:
        return {
            "check_id": "output_quality.envelope_present",
            "status": "fail",
            "message": "Missing 'data' section in envelope",
        }

    return {
        "check_id": "output_quality.envelope_present",
        "status": "pass",
        "message": "Envelope structure is valid",
    }


def check_metadata_complete(output: dict, ground_truth: dict | None) -> dict:
    """Check that metadata has all required fields."""
    metadata = output.get("metadata", {})
    required_fields = [
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version",
    ]

    missing = [f for f in required_fields if f not in metadata]

    if missing:
        return {
            "check_id": "output_quality.metadata_complete",
            "status": "fail",
            "message": f"Missing metadata fields: {missing}",
        }

    return {
        "check_id": "output_quality.metadata_complete",
        "status": "pass",
        "message": "All required metadata fields present",
    }


def check_tool_name_correct(output: dict, ground_truth: dict | None) -> dict:
    """Check that tool_name is correct."""
    metadata = output.get("metadata", {})
    tool_name = metadata.get("tool_name", "")

    if tool_name != "dependensee":
        return {
            "check_id": "output_quality.tool_name_correct",
            "status": "fail",
            "message": f"tool_name should be 'dependensee', got '{tool_name}'",
        }

    return {
        "check_id": "output_quality.tool_name_correct",
        "status": "pass",
        "message": "Tool name is correct",
    }


def check_paths_repo_relative(output: dict, ground_truth: dict | None) -> dict:
    """Check that all paths are repo-relative (not absolute)."""
    data = output.get("data", {})
    projects = data.get("projects", [])

    absolute_paths = []
    for p in projects:
        path = p.get("path", "")
        if path.startswith("/") or path.startswith("./"):
            absolute_paths.append(path)

        for ref in p.get("project_references", []):
            if ref.startswith("/") or ref.startswith("./"):
                absolute_paths.append(ref)

    if absolute_paths:
        return {
            "check_id": "output_quality.paths_repo_relative",
            "status": "fail",
            "message": f"Found non-relative paths: {absolute_paths[:3]}",
        }

    return {
        "check_id": "output_quality.paths_repo_relative",
        "status": "pass",
        "message": "All paths are repo-relative",
    }


def check_graph_consistency(output: dict, ground_truth: dict | None) -> dict:
    """Check that dependency graph is internally consistent."""
    data = output.get("data", {})
    graph = data.get("dependency_graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_ids = {n.get("id") for n in nodes}

    # Check that all edge sources and targets reference existing nodes
    invalid_refs = []
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_ids:
            invalid_refs.append(f"source '{source}' not in nodes")
        # Target might reference external packages that aren't nodes (for package refs)
        # Only check for project references
        if edge.get("type") == "project_reference" and target not in node_ids:
            invalid_refs.append(f"target '{target}' not in nodes")

    if invalid_refs:
        return {
            "check_id": "output_quality.graph_consistency",
            "status": "fail",
            "message": f"Graph inconsistencies: {invalid_refs[:3]}",
        }

    return {
        "check_id": "output_quality.graph_consistency",
        "status": "pass",
        "message": "Dependency graph is internally consistent",
    }
