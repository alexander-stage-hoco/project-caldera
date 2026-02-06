"""Performance checks for dependensee.

Validates performance characteristics of the analysis.
"""

from __future__ import annotations


def check_reasonable_output_size(output: dict, ground_truth: dict | None) -> dict:
    """Check that output size is reasonable for the number of projects."""
    data = output.get("data", {})
    projects = data.get("projects", [])
    graph = data.get("dependency_graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # Basic sanity check: nodes should >= projects
    if len(nodes) < len(projects):
        return {
            "check_id": "performance.output_size_reasonable",
            "status": "warn",
            "message": f"Graph has fewer nodes ({len(nodes)}) than projects ({len(projects)})",
        }

    return {
        "check_id": "performance.output_size_reasonable",
        "status": "pass",
        "message": f"Output size is reasonable: {len(projects)} projects, {len(nodes)} nodes, {len(edges)} edges",
    }
