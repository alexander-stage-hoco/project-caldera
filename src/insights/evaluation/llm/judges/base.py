"""
Base judge class for LLM-based evaluation.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..providers import LLMProvider, get_provider
from ..providers.claude_code import ClaudeCodeHeadlessProvider


@dataclass
class JudgeResult:
    """Result from an LLM judge evaluation."""

    judge_name: str
    overall_score: float  # 1.0 to 5.0
    sub_scores: dict[str, float]  # Sub-dimension scores
    reasoning: str
    suggestions: list[str]
    raw_response: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_score(self) -> float:
        """Return score normalized to 0.0-1.0 range."""
        return (self.overall_score - 1.0) / 4.0


class BaseJudge(ABC):
    """Abstract base class for LLM judges."""

    # Judge configuration
    name: str = "base"
    weight: float = 1.0
    sub_dimensions: dict[str, float] = {}  # dimension_name -> weight

    def __init__(
        self,
        provider: LLMProvider | None = None,
        model: str | None = None,
        prompts_dir: Path | None = None,
    ):
        """
        Initialize the judge.

        Args:
            provider: LLM provider to use. Defaults to Claude Code Headless.
            model: Optional model override.
            prompts_dir: Optional custom prompts directory.
        """
        self.provider = provider or ClaudeCodeHeadlessProvider(model=model or "claude-opus-4-5")
        self.model = model
        self.prompts_dir = prompts_dir or (Path(__file__).parent.parent / "prompts")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this judge."""
        ...

    @abstractmethod
    def get_evaluation_prompt(self, report_content: str, context: dict[str, Any]) -> str:
        """
        Get the evaluation prompt for a specific report.

        Args:
            report_content: The report content to evaluate.
            context: Additional context (format, run_pk, etc.).

        Returns:
            The formatted evaluation prompt.
        """
        ...

    def evaluate(
        self,
        report_content: str,
        context: dict[str, Any] | None = None,
    ) -> JudgeResult:
        """
        Evaluate a report using this judge.

        Args:
            report_content: The report content to evaluate.
            context: Additional context for evaluation.

        Returns:
            JudgeResult with scores and feedback.
        """
        context = context or {}

        # Get prompts
        system_prompt = self.get_system_prompt()
        eval_prompt = self.get_evaluation_prompt(report_content, context)

        # Call LLM
        response = self.provider.complete(
            prompt=eval_prompt,
            system=system_prompt,
            model=self.model,
            temperature=0.0,
        )

        # Parse response
        return self._parse_response(response.content)

    def _parse_response(self, response: str) -> JudgeResult:
        """
        Parse the LLM response into a JudgeResult.

        Expects JSON format with:
        - overall_score: float (1-5)
        - sub_scores: dict[str, float]
        - reasoning: str
        - suggestions: list[str]
        """
        # Handle empty response (provider issue)
        if not response or not response.strip():
            return JudgeResult(
                judge_name=self.name,
                overall_score=3.0,
                sub_scores={},
                reasoning="LLM returned empty response - provider may have failed",
                suggestions=["Check Claude Code CLI is working correctly"],
                raw_response=response or "",
                metadata={"error": "empty_response"},
            )

        try:
            # Try to extract JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            return JudgeResult(
                judge_name=self.name,
                overall_score=float(data.get("overall_score", 3.0)),
                sub_scores={k: float(v) for k, v in data.get("sub_scores", {}).items()},
                reasoning=data.get("reasoning", ""),
                suggestions=data.get("suggestions", []),
                raw_response=response,
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Return a default result on parse failure
            return JudgeResult(
                judge_name=self.name,
                overall_score=3.0,
                sub_scores={},
                reasoning=f"Failed to parse response: {e}",
                suggestions=[],
                raw_response=response,
                metadata={"parse_error": str(e)},
            )

    def load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template from the prompts directory."""
        template_path = self.prompts_dir / f"{template_name}.txt"
        if template_path.exists():
            return template_path.read_text()
        raise FileNotFoundError(f"Prompt template not found: {template_path}")
