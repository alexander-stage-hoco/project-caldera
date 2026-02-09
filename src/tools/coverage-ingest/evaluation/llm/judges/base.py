"""Base judge class for LLM-as-a-Judge evaluation of coverage-ingest analysis.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides coverage-ingest-specific extensions.
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
    """Coverage-ingest-specific base judge for coverage analysis evaluation.

    Extends the shared BaseJudge with coverage-ingest-specific functionality:
    - Multi-format coverage data handling (LCOV, Cobertura, JaCoCo, Istanbul)
    - Cross-format consistency evaluation
    - Risk tier classification support
    """

    # Coverage-specific synthetic patterns
    SYNTHETIC_PATTERNS = SharedBaseJudge.SYNTHETIC_PATTERNS | {
        "simple", "multi-file", "multi-package", "multi-module",
        "branches", "edge-cases", "counters", "equivalence",
    }

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the coverage-ingest judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing coverage analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        # Set default working dir to coverage-ingest tool directory
        if working_dir is None:
            working_dir = Path(__file__).parent.parent.parent.parent

        # Set default ground truth directory
        if ground_truth_dir is None:
            ground_truth_dir = working_dir / "evaluation" / "ground-truth"

        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            ground_truth_dir=ground_truth_dir,
            use_llm=use_llm,
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_coverage_results(self) -> dict[str, Any]:
        """Load coverage analysis results from output directory.

        Returns:
            Dictionary with format -> list of analysis results.
        """
        results: dict[str, list[dict[str, Any]]] = {
            "lcov": [],
            "cobertura": [],
            "jacoco": [],
            "istanbul": [],
        }

        if not self.output_dir or not self.output_dir.exists():
            return {"error": f"Output directory not found: {self.output_dir}"}

        # Look for output files in the output directory
        for json_file in sorted(self.output_dir.glob("**/*.json")):
            if json_file.name.startswith("."):
                continue
            try:
                data = json.loads(json_file.read_text())
                # Extract format from envelope or data
                source_format = None
                if "data" in data:
                    source_format = data.get("data", {}).get("source_format")
                elif "source_format" in data:
                    source_format = data.get("source_format")

                if source_format and source_format in results:
                    results[source_format].append(data)
            except json.JSONDecodeError:
                continue

        return results

    def load_ground_truth_by_format(self) -> dict[str, dict[str, Any]]:
        """Load all ground truth files organized by format.

        Returns:
            Dictionary with format -> scenario -> ground truth data.
        """
        results: dict[str, dict[str, Any]] = {
            "lcov": {},
            "cobertura": {},
            "jacoco": {},
            "istanbul": {},
            "cross-format": {},
        }

        if not self.ground_truth_dir.exists():
            return results

        # Load format-specific ground truth
        for format_dir in self.ground_truth_dir.iterdir():
            if not format_dir.is_dir():
                continue
            format_name = format_dir.name
            if format_name not in results:
                continue

            for gt_file in sorted(format_dir.glob("*.json")):
                if gt_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(gt_file.read_text())
                    scenario = gt_file.stem
                    results[format_name][scenario] = data
                except json.JSONDecodeError:
                    continue

        return results

    def load_programmatic_results(self) -> dict[str, Any] | None:
        """Load programmatic evaluation results.

        Returns:
            Evaluation results dictionary or None if not found.
        """
        candidates = [
            self.working_dir / "evaluation" / "results" / "evaluation_results.json",
            self.working_dir / "evaluation" / "results" / "evaluation_report.json",
        ]

        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text())
                except json.JSONDecodeError:
                    continue

        return None

    def _build_programmatic_summary(self) -> str:
        """Build a short summary of programmatic checks and results."""
        prog_results = self.load_programmatic_results()
        if not prog_results:
            return "Programmatic evaluation summary unavailable."

        score = prog_results.get("score", "n/a")
        passed = prog_results.get("passed", 0)
        total = prog_results.get("total", 0)
        decision = prog_results.get("decision", "UNKNOWN")

        lines = [
            "Programmatic Checks Summary:",
            f"- Score: {score}% | Passed: {passed}/{total} | Decision: {decision}",
        ]

        checks = prog_results.get("checks", [])
        if checks:
            # Group by category prefix
            categories: dict[str, list[dict[str, Any]]] = {}
            for check in checks:
                check_id = check.get("id", "XX-0")
                prefix = check_id.split("-")[0] if "-" in check_id else "XX"
                categories.setdefault(prefix, []).append(check)

            for prefix, cat_checks in categories.items():
                passed_count = sum(1 for c in cat_checks if c.get("passed"))
                lines.append(f"- {prefix}: {passed_count}/{len(cat_checks)} passed")

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

        if "{{" in prompt and "}}" in prompt:
            import re
            unresolved = re.findall(r"\{\{\s*\w+\s*\}\}", prompt)
            raise ValueError(f"Unresolved prompt placeholders: {unresolved}")

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

        # Check if we should use heuristic evaluation
        if not self.use_llm:
            return self.run_heuristic_evaluation(evidence)

        # Build prompt
        try:
            prompt = self.build_prompt(evidence)
        except ValueError as exc:
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.0,
                reasoning=str(exc),
                evidence_cited=[],
                recommendations=["Fix prompt placeholders before evaluation"],
                raw_response="",
            )

        # Invoke Claude
        response = self.invoke_claude(prompt)

        if response.strip().startswith("Error"):
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
