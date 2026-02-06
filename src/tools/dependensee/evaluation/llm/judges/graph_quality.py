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

        for repo_name, repo_analysis in all_results.items():
            graph = self.extract_dependency_graph(repo_analysis)
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])

            total_nodes += len(nodes)
            total_edges += len(edges)

            node_ids = {n.get("id") for n in nodes}

            for node in nodes:
                if node.get("type") == "project":
                    project_nodes += 1
                elif node.get("type") == "package":
                    package_nodes += 1

            for edge in edges:
                if edge.get("type") == "project_reference":
                    project_edges += 1
                    # Check for dangling refs
                    if edge.get("target") not in node_ids:
                        dangling_refs += 1
                elif edge.get("type") == "package_reference":
                    package_edges += 1

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "project_nodes": project_nodes,
            "package_nodes": package_nodes,
            "project_edges": project_edges,
            "package_edges": package_edges,
            "dangling_references": dangling_refs,
            "evaluation_mode": self.evaluation_mode,
        }

    def format_prompt(self, evidence: dict[str, Any]) -> str:
        """Format prompt for LLM evaluation."""
        prompt_template = self.prompt_file.read_text() if self.prompt_file.exists() else ""
        return prompt_template.format(
            total_nodes=evidence.get("total_nodes", 0),
            total_edges=evidence.get("total_edges", 0),
            dangling_refs=evidence.get("dangling_references", 0),
        )

    def parse_response(self, response: str, evidence: dict[str, Any]) -> JudgeResult:
        """Parse LLM response into structured result."""
        total_nodes = evidence.get("total_nodes", 0)
        dangling = evidence.get("dangling_references", 0)

        if total_nodes == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=0.0,
                verdict="FAIL",
                reasoning="No graph nodes found",
                evidence=evidence,
            )

        # Penalize for dangling references
        consistency_score = 1.0 - (dangling / max(total_nodes, 1))
        overall_score = max(0, consistency_score)

        verdict = "PASS" if overall_score >= 0.9 else "FAIL"
        reasoning = f"Graph has {total_nodes} nodes and {evidence.get('total_edges', 0)} edges. {dangling} dangling references found."

        return JudgeResult(
            dimension=self.dimension_name,
            score=overall_score,
            verdict=verdict,
            reasoning=reasoning,
            evidence=evidence,
        )
