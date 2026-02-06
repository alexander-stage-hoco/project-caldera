"""Graph Quality Judge - Evaluates the dependency graph structure."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class GraphQualityJudge(BaseJudge):
    """Evaluates quality and consistency of the dependency graph.

    Validates that:
    - Graph nodes correctly represent projects and packages
    - Edges correctly represent dependencies
    - Graph is internally consistent (no dangling references)
    """

    @property
    def dimension_name(self) -> str:
        return "graph_quality"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess graph quality."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate from all repos
        total_nodes = 0
        total_edges = 0
        project_nodes = 0
        package_nodes = 0
        project_edges = 0
        package_edges = 0
        dangling_refs = 0
        orphan_nodes = 0
        graphs_analyzed = []

        for repo_name, repo_analysis in all_results.items():
            graph = self.extract_dependency_graph(repo_analysis)
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])

            total_nodes += len(nodes)
            total_edges += len(edges)

            node_ids = {n.get("id") for n in nodes}
            nodes_with_edges = set()

            for node in nodes:
                if node.get("type") == "project":
                    project_nodes += 1
                elif node.get("type") == "package":
                    package_nodes += 1

            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                nodes_with_edges.add(source)
                nodes_with_edges.add(target)

                if edge.get("type") == "project_reference":
                    project_edges += 1
                    if target not in node_ids:
                        dangling_refs += 1
                elif edge.get("type") == "package_reference":
                    package_edges += 1

            # Count orphan nodes (nodes with no edges)
            orphan_nodes += len(node_ids - nodes_with_edges)

            graphs_analyzed.append({
                "repo": repo_name,
                "nodes": len(nodes),
                "edges": len(edges),
            })

        # Calculate quality metrics
        consistency_score = 1.0 - (dangling_refs / max(total_edges, 1))
        connectivity_score = 1.0 - (orphan_nodes / max(total_nodes, 1))

        evidence = {
            "graphs_analyzed": graphs_analyzed,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_breakdown": {
                "project_nodes": project_nodes,
                "package_nodes": package_nodes,
            },
            "edge_breakdown": {
                "project_edges": project_edges,
                "package_edges": package_edges,
            },
            "quality_metrics": {
                "dangling_references": dangling_refs,
                "orphan_nodes": orphan_nodes,
                "consistency_pct": round(consistency_score * 100, 1),
                "connectivity_pct": round(connectivity_score * 100, 1),
            },
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                expected = gt.get("expected", {})
                expected_nodes = expected.get("graph_node_count", 0)
                expected_edges = expected.get("graph_edge_count", 0)

                # Find actual counts for this repo
                repo_graph = None
                for g in graphs_analyzed:
                    if g["repo"] == repo_name:
                        repo_graph = g
                        break

                if repo_graph:
                    gt_comparison.append({
                        "repo": repo_name,
                        "expected_nodes": expected_nodes,
                        "actual_nodes": repo_graph["nodes"],
                        "nodes_match": expected_nodes == repo_graph["nodes"],
                        "expected_edges": expected_edges,
                        "actual_edges": repo_graph["edges"],
                        "edges_match": expected_edges == repo_graph["edges"],
                    })
            evidence["ground_truth_comparison"] = gt_comparison

        # Add synthetic context (empty for synthetic mode, populated for real_world)
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available (synthetic evaluation mode)"
            evidence["interpretation_guidance"] = "Evaluate against ground truth expectations."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Graph Quality Evaluation

You are an expert graph theory analyst evaluating DependenSee's dependency graph construction.

## Task

Evaluate the quality and consistency of the generated dependency graph structure.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Structural Completeness** (35%): Does the graph contain all expected nodes and edges?
   - 5: All projects and packages represented as nodes with correct edges
   - 4: Minor missing elements (<5%)
   - 3: Some elements missing (5-15%)
   - 2: Significant gaps (15-30%)
   - 1: Graph is incomplete (>30% missing)

2. **Internal Consistency** (35%): Is the graph internally consistent?
   - 5: No dangling references, all edge targets exist as nodes
   - 4: Rare inconsistencies (<2%)
   - 3: Some inconsistencies (2-10%)
   - 2: Many inconsistencies (10-20%)
   - 1: Severely inconsistent (>20% dangling refs)

3. **Connectivity** (30%): Are all nodes appropriately connected?
   - 5: No orphan nodes (all nodes have at least one edge)
   - 4: Few orphan nodes (<5%)
   - 3: Some orphan nodes (5-15%)
   - 2: Many orphan nodes (15-30%)
   - 1: Most nodes are orphans (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "structural_completeness": <1-5>,
    "internal_consistency": <1-5>,
    "connectivity": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Checks that graph node/edge counts match expected values.
        """
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        for repo_name, gt in ground_truth.items():
            if repo_name not in all_results:
                continue

            expected = gt.get("expected", {})
            graph = self.extract_dependency_graph(all_results[repo_name])

            actual_nodes = len(graph.get("nodes", []))
            actual_edges = len(graph.get("edges", []))
            expected_nodes = expected.get("graph_node_count", 0)
            expected_edges = expected.get("graph_edge_count", 0)

            if actual_nodes != expected_nodes:
                failures.append(
                    f"{repo_name}: expected {expected_nodes} graph nodes, found {actual_nodes}"
                )

            if actual_edges != expected_edges:
                failures.append(
                    f"{repo_name}: expected {expected_edges} graph edges, found {actual_edges}"
                )

        return len(failures) == 0, failures
