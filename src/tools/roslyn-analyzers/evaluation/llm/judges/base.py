"""Base judge class for LLM-as-a-Judge evaluation of Roslyn Analyzers outputs."""

from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class JudgeResult:
    """Result from an LLM judge evaluation."""

    dimension: str
    score: int  # 1-5
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence_cited: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    sub_scores: dict[str, int] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JudgeResult:
        """Create from dictionary."""
        return cls(
            dimension=data.get("dimension", "unknown"),
            score=data.get("score", 0),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            evidence_cited=data.get("evidence_cited", []),
            recommendations=data.get("recommendations", []),
            sub_scores=data.get("sub_scores", {}),
            raw_response=data.get("raw_response", ""),
        )


class BaseJudge(ABC):
    """Base class for LLM judges.

    Each judge evaluates a specific dimension of Roslyn Analyzer
    static analysis quality. Judges invoke Claude Code in headless mode
    with specialized prompts.
    """

    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        analysis_path: Path | None = None,
        ground_truth_path: Path | None = None,
        evaluation_path: Path | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path(__file__).parent.parent.parent.parent
        self.output_dir = output_dir or self.working_dir / "output" / "runs"
        self.analysis_path = analysis_path or self.output_dir / "roslyn_analysis.json"
        self.ground_truth_path = ground_truth_path or self.working_dir / "evaluation" / "ground-truth" / "csharp.json"
        self.evaluation_path = evaluation_path or self.output_dir / "evaluation_report.json"
        self._prompt_template: str | None = None

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """Name of the evaluation dimension."""
        ...

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this dimension in the overall score (0.0-1.0)."""
        ...

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        if self._prompt_template is None:
            if self.prompt_file.exists():
                self._prompt_template = self.prompt_file.read_text()
            else:
                self._prompt_template = self.get_default_prompt()
        return self._prompt_template

    @abstractmethod
    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        ...

    @abstractmethod
    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence files and data for evaluation."""
        ...

    def load_analysis(self) -> dict[str, Any]:
        """Load the analysis JSON file."""
        if self.analysis_path.exists():
            return json.loads(self.analysis_path.read_text())
        return {}

    def load_ground_truth(self) -> dict[str, Any]:
        """Load the ground truth JSON file."""
        if self.ground_truth_path.exists():
            return json.loads(self.ground_truth_path.read_text())
        return {}

    def load_evaluation(self) -> dict[str, Any]:
        """Load the evaluation report JSON file."""
        if self.evaluation_path.exists():
            return json.loads(self.evaluation_path.read_text())
        return {}

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            for json_file in sorted(self.output_dir.glob("*.json")):
                # Skip hidden files and evaluation reports
                if json_file.name.startswith("."):
                    continue
                if "evaluation" in json_file.name.lower():
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    def load_ground_truth_by_name(self, name: str) -> dict[str, Any]:
        """Load ground truth for a specific category."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"
        gt_file = gt_dir / f"{name}.json"
        if gt_file.exists():
            return json.loads(gt_file.read_text())
        return {}

    def load_all_ground_truths(self) -> dict[str, Any]:
        """Load all ground truth files."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"
        results = {}

        if gt_dir.exists():
            for gt_file in sorted(gt_dir.glob("*.json")):
                try:
                    data = json.loads(gt_file.read_text())
                    results[gt_file.stem] = data
                except json.JSONDecodeError:
                    continue

        return results

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence."""
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

        return prompt

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result."""
        try:
            # Try to extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                result = JudgeResult.from_dict(data)
                result.dimension = self.dimension_name
                result.raw_response = response
                return result
        except json.JSONDecodeError:
            pass

        # Fallback: extract score from text
        score = 3  # Default to middle score
        for i in range(5, 0, -1):
            if f"score: {i}" in response.lower() or f"score:{i}" in response.lower():
                score = i
                break

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.5,
            reasoning=response[:500],
            raw_response=response,
        )

    def invoke_claude(self, prompt: str) -> str:
        """Invoke Claude Code in headless mode."""
        try:
            # Pass prompt directly via stdin
            # Disable tools and increase max-turns for complex prompts
            cmd = [
                "claude",
                "-p", "-",  # Read from stdin
                "--model", self.model,
                "--output-format", "text",
                "--allowedTools", "",
                "--max-turns", "1",  # Single turn since no tools allowed
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=prompt,
                timeout=self.timeout,
                cwd=str(self.working_dir),
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            return result.stdout

        except subprocess.TimeoutExpired:
            return "Error: Claude invocation timed out"
        except Exception as e:
            return f"Error: {e}"

    def evaluate(self) -> JudgeResult:
        """Run the full evaluation pipeline."""
        # Collect evidence
        evidence = self.collect_evidence()

        # Build prompt
        prompt = self.build_prompt(evidence)

        # Invoke Claude
        response = self.invoke_claude(prompt)

        # Parse response
        result = self.parse_response(response)

        return result

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Returns:
            Tuple of (all_passed, list of failure messages)
        """
        # Default: no assertions, always pass
        return True, []
