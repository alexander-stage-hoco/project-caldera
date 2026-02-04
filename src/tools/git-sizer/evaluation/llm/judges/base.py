"""Base judge class for LLM-as-a-Judge evaluation of git-sizer repository analysis.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides git-sizer-specific extensions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """Git-sizer-specific base judge for repository health analysis.

    Extends the shared BaseJudge with git-sizer-specific functionality:
    - Caldera envelope format handling
    - Multi-repo results support
    - Programmatic summary building
    """

    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the git-sizer judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Path to the git-sizer analysis JSON file
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        self.analysis_path = analysis_path or self.working_dir / "output" / "output.json"

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_analysis(self) -> dict[str, Any]:
        """Load analysis from Caldera envelope format.

        Returns a normalized structure compatible with evidence collection.
        Supports:
        - Single repo output file: { metadata: {...}, data: {...} }
        - Multi-repo results file: { repositories: [...] }
        - Directory with multiple repo subdirectories (auto-aggregates)
        """
        # Handle directory input - aggregate all repo outputs
        if self.analysis_path.is_dir():
            return self._load_from_directory(self.analysis_path)

        # Handle file input
        if not self.analysis_path.exists():
            return {"error": f"Analysis file not found: {self.analysis_path}"}

        raw = json.loads(self.analysis_path.read_text())

        # Check if this is Caldera envelope format (single repo)
        if "metadata" in raw and "data" in raw:
            # Convert envelope to repositories array format for compatibility
            metadata = raw["metadata"]
            data = raw["data"]
            return {
                "timestamp": metadata.get("timestamp", ""),
                "target_path": metadata.get("repo_id", ""),
                "repositories": [{
                    "repository": metadata.get("repo_name") or metadata.get("repo_id", "unknown"),
                    "health_grade": data.get("health_grade", ""),
                    "metrics": data.get("metrics", {}),
                    "violations": data.get("violations", []),
                    "lfs_candidates": data.get("lfs_candidates", []),
                    "raw_output": data.get("raw_output", {}),
                }],
                "summary": {
                    "total_duration_ms": data.get("duration_ms", 0),
                    "total_violations": len(data.get("violations", [])),
                },
            }

        # Already in multi-repo format (from evaluate.py aggregation)
        return raw

    def _load_from_directory(self, results_dir: Path) -> dict[str, Any]:
        """Aggregate all repo results from a directory structure.

        Looks for:
        - results_dir/*/output.json (subdirectory repos)
        - results_dir/output.json (root output, if valid non-placeholder)
        """
        repositories = []
        timestamps = []

        # Scan subdirectories for repo outputs
        for repo_dir in sorted(results_dir.iterdir()):
            if not repo_dir.is_dir():
                continue
            output_path = repo_dir / "output.json"
            if output_path.exists():
                try:
                    data = json.loads(output_path.read_text())
                except json.JSONDecodeError:
                    continue
                if "data" in data:
                    repo_data = data["data"].copy()
                    repo_name = data.get("metadata", {}).get("repo_name") or repo_dir.name
                    repo_data["repository"] = repo_name
                    repo_data["metrics"] = repo_data.get("metrics", {})
                    repositories.append(repo_data)
                    # Collect timestamp for aggregation
                    ts = data.get("metadata", {}).get("timestamp")
                    if ts:
                        timestamps.append(ts)

        if not repositories:
            # Fallback: try root output.json if no subdirectory results found
            root_output = results_dir / "output.json"
            if root_output.exists():
                # Re-run load_analysis on the file (not directory)
                original_path = self.analysis_path
                self.analysis_path = root_output
                try:
                    return self.load_analysis()
                finally:
                    self.analysis_path = original_path
            return {"error": f"No analysis results found in {results_dir}"}

        # Use latest timestamp from aggregated repos, or generate current time if none found
        latest_timestamp = max(timestamps) if timestamps else datetime.now(timezone.utc).isoformat()

        return {
            "timestamp": latest_timestamp,
            "target_path": str(results_dir),
            "repositories": repositories,
            "summary": {
                "total_repositories": len(repositories),
                "total_duration_ms": sum(r.get("duration_ms", 0) for r in repositories),
                "total_violations": sum(len(r.get("violations", [])) for r in repositories),
            },
        }

    def _build_programmatic_summary(self) -> str:
        """Build a short summary of programmatic checks and results."""
        candidates = []
        analysis_dir = self.analysis_path.parent
        candidates.append(analysis_dir / "evaluation_report.json")
        candidates.append(analysis_dir / "checks.json")
        candidates.append(self.working_dir / "evaluation" / "results" / "evaluation_report.json")
        candidates.append(self.working_dir / "evaluation" / "results" / "checks.json")

        report_path = next((p for p in candidates if p.exists()), None)
        if not report_path:
            return "Programmatic evaluation summary unavailable."

        try:
            report = json.loads(report_path.read_text())
        except Exception:
            return "Programmatic evaluation summary unavailable (invalid JSON)."

        summary = report.get("summary", {})
        score = summary.get("score", report.get("score", "n/a"))
        failed = summary.get("failed", report.get("failed", "n/a"))
        total = summary.get("total", report.get("total", "n/a"))

        lines = [
            "Programmatic Checks Summary:",
            f"- Score: {score} | Failed: {failed} | Total: {total}",
        ]

        checks = report.get("checks", [])
        if checks:
            for check in checks[:10]:
                check_id = check.get("check_id", "unknown")
                name = check.get("name", "check")
                message = check.get("message", "").strip()
                if message:
                    lines.append(f"- {check_id} {name}: {message}")
                else:
                    lines.append(f"- {check_id} {name}")
            if len(checks) > 10:
                lines.append(f"- … {len(checks) - 10} more checks")

        return "\n".join(lines)

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Overrides parent to support per-key placeholder replacement
        and programmatic summary injection.
        """
        template = self.load_prompt_template()

        # Replace placeholders in template
        prompt = template
        if "{{ programmatic_summary }}" in prompt and "programmatic_summary" not in evidence:
            evidence = {**evidence, "programmatic_summary": self._build_programmatic_summary()}
        for key, value in evidence.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            prompt = prompt.replace(placeholder, value_str)

        if "{{" in prompt or "}}" in prompt:
            raise ValueError("Unresolved prompt placeholders detected")
        if "Respond with ONLY a JSON object" not in prompt:
            prompt = (
                prompt
                + "\n\nRespond with ONLY a JSON object. Do not use markdown fences or extra text."
            )

        return prompt

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result.

        Overrides parent to handle empty responses gracefully.
        """
        if not response.strip():
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.0,
                reasoning="Empty response from Claude.",
                evidence_cited=[],
                recommendations=["LLM returned empty output; check Claude CLI logs and prompt."],
                raw_response=response,
            )
        return super().parse_response(response)

    def evaluate(self) -> JudgeResult:
        """Run the full evaluation pipeline.

        Overrides parent to handle error responses gracefully.
        """
        # Collect evidence
        evidence = self.collect_evidence()

        # Build prompt
        prompt = self.build_prompt(evidence)

        # Invoke Claude
        response = self.invoke_claude(prompt)

        if response.strip().startswith("Error:"):
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.0,
                reasoning=response.strip(),
                evidence_cited=[],
                recommendations=["LLM execution error; check Claude CLI availability and stderr"],
                raw_response=response,
            )

        # Parse response
        result = self.parse_response(response)

        return result
