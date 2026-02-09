"""Base judge class for LLM-as-a-Judge evaluation of git-fame authorship analysis.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides git-fame-specific extensions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult
from shared.output_management import unwrap_envelope

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """Git-fame-specific base judge for authorship analysis evaluation.

    Extends the shared BaseJudge with git-fame-specific functionality:
    - Caldera envelope format handling
    - Author metrics extraction
    - Concentration index calculations
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the git-fame judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir or (working_dir or Path.cwd()) / "outputs",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            json_files = list(self.output_dir.glob("*.json"))
            # Also check for output.json in subdirectories
            if not json_files:
                json_files = list(self.output_dir.rglob("output.json"))

            for json_file in sorted(json_files):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    # Use 'id' field from envelope for ground truth matching,
                    # fall back to parent dir name or filename stem
                    if json_file.name == "output.json":
                        repo_name = data.get("id", json_file.parent.name)
                    else:
                        repo_name = data.get("id", json_file.stem)
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    def extract_results(self, data: dict) -> dict[str, Any]:
        """Extract results from analysis data, handling envelope format.

        Args:
            data: Raw analysis data (may be envelope or direct format)

        Returns:
            Results dictionary with summary and authors
        """
        # Use shared unwrap_envelope helper
        inner = unwrap_envelope(data)
        # Handle legacy format (results)
        if "results" in inner:
            return inner["results"]
        # Handle direct format
        return inner

    def extract_authors(self, data: dict) -> list[dict[str, Any]]:
        """Extract authors list from analysis data.

        Args:
            data: Analysis data dictionary

        Returns:
            List of author dictionaries
        """
        results = self.extract_results(data)
        return results.get("authors", [])

    def extract_summary(self, data: dict) -> dict[str, Any]:
        """Extract summary from analysis data.

        Args:
            data: Analysis data dictionary

        Returns:
            Summary dictionary with concentration metrics
        """
        results = self.extract_results(data)
        return results.get("summary", {})

    def calculate_bus_factor(self, authors: list[dict]) -> int:
        """Calculate bus factor from authors list.

        Bus factor = minimum number of authors needed to cover 50% of code.

        Args:
            authors: List of author dictionaries with ownership_pct

        Returns:
            Bus factor integer
        """
        if not authors:
            return 0

        # Sort by ownership_pct descending
        sorted_authors = sorted(
            authors,
            key=lambda a: a.get("ownership_pct", 0),
            reverse=True
        )

        cumulative = 0.0
        for i, author in enumerate(sorted_authors, 1):
            cumulative += author.get("ownership_pct", 0)
            if cumulative >= 50:
                return i

        return len(sorted_authors)

    def calculate_hhi(self, authors: list[dict]) -> float:
        """Calculate Herfindahl-Hirschman Index from authors list.

        HHI = sum of squared ownership fractions (0 = equal, 1 = monopoly)

        Args:
            authors: List of author dictionaries with ownership_pct

        Returns:
            HHI value between 0 and 1
        """
        if not authors:
            return 0.0

        total_pct = sum(a.get("ownership_pct", 0) for a in authors)
        if total_pct == 0:
            return 0.0

        hhi = sum(
            (a.get("ownership_pct", 0) / total_pct) ** 2
            for a in authors
        )
        return round(hhi, 4)

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Overrides parent to support per-key placeholder replacement.
        """
        template = self.load_prompt_template()

        # Replace placeholders in template
        prompt = template
        for key, value in evidence.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            prompt = prompt.replace(placeholder, value_str)

        # Check for {{ evidence }} placeholder and replace with full dict
        if "{{ evidence }}" in prompt:
            evidence_str = json.dumps(evidence, indent=2, default=str)
            prompt = prompt.replace("{{ evidence }}", evidence_str)

        if "{{" in prompt or "}}" in prompt:
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

        if response.strip().startswith("Error"):
            return JudgeResult(
                dimension=self.dimension_name,
                score=1,
                confidence=0.0,
                reasoning=response.strip(),
                evidence_cited=[],
                recommendations=["LLM execution error; check Claude CLI availability"],
                raw_response=response,
            )

        return super().parse_response(response)
