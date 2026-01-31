"""Base judge class for LLM-as-a-Judge evaluation of Lizard outputs."""

from __future__ import annotations

import json
import subprocess
import tempfile
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

    Each judge evaluates a specific dimension of Lizard function complexity
    analysis quality. Judges invoke Claude Code in headless mode with
    specialized prompts.
    """

    def __init__(
        self,
        model: str = "opus",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.analysis_path = analysis_path or self._resolve_analysis_path()
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

    def _resolve_analysis_path(self) -> Path:
        """Resolve default analysis path for evaluation."""
        evaluation_path = self.working_dir / "evaluation" / "results" / "output.json"
        if evaluation_path.exists():
            return evaluation_path

        outputs_root = self.working_dir / "outputs"
        if outputs_root.exists():
            candidates = [
                p for p in outputs_root.iterdir()
                if p.is_dir() and (p / "output.json").exists()
            ]
            if candidates:
                return max(candidates, key=lambda p: p.stat().st_mtime) / "output.json"

        return self.working_dir / "output" / "output.json"

    def _load_analysis(self) -> dict[str, Any]:
        """Load analysis JSON, handling envelope payloads."""
        analysis = json.loads(self.analysis_path.read_text())
        if isinstance(analysis, dict) and "data" in analysis:
            return analysis.get("data") or {}
        return analysis

    @abstractmethod
    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        ...

    @abstractmethod
    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence files and data for evaluation."""
        ...

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
            cmd = [
                "claude",
                "-p", "-",  # Read from stdin
                "--model", self.model,
                "--output-format", "text",
                "--allowedTools", "",
                "--max-turns", "3",
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
