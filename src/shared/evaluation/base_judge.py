"""Shared base judge class for LLM-as-a-Judge evaluation.

This module provides a standardized BaseJudge implementation for use across
all Project Caldera analysis tools. Each tool's LLM judges should inherit
from this class.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

try:
    import anthropic  # type: ignore
    HAS_ANTHROPIC_SDK = True
except Exception:
    anthropic = None
    HAS_ANTHROPIC_SDK = False


@dataclass
class JudgeResult:
    """Result from an LLM judge evaluation.

    Attributes:
        dimension: Name of the evaluation dimension (e.g., "coverage", "accuracy")
        score: Numeric score from 1-5 (1=poor, 5=excellent)
        confidence: Confidence level from 0.0-1.0
        reasoning: Explanation of the score
        evidence_cited: List of evidence points used in evaluation
        recommendations: List of improvement recommendations
        sub_scores: Dictionary of sub-dimension scores
        raw_response: The raw LLM response text
    """

    dimension: str
    score: int  # 1-5
    confidence: float  # 0.0-1.0
    reasoning: str
    evidence_cited: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    sub_scores: dict[str, int] = field(default_factory=dict)
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JudgeResult:
        """Create JudgeResult from dictionary.

        Args:
            data: Dictionary with JudgeResult fields

        Returns:
            JudgeResult instance
        """
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

    def is_passing(self, threshold: int = 3) -> bool:
        """Check if the score meets the passing threshold.

        Args:
            threshold: Minimum passing score (default 3)

        Returns:
            True if score >= threshold
        """
        return self.score >= threshold


class BaseJudge(ABC):
    """Base class for LLM judges.

    Each judge evaluates a specific dimension of tool output quality.
    Judges can invoke Claude via the Anthropic SDK (preferred) or
    Claude Code CLI (fallback).

    Subclasses must implement:
        - dimension_name: Property returning the dimension name
        - weight: Property returning the dimension weight (0.0-1.0)
        - collect_evidence(): Method to gather evidence for evaluation
        - get_default_prompt(): Method returning the default prompt template

    Example:
        class AccuracyJudge(BaseJudge):
            @property
            def dimension_name(self) -> str:
                return "accuracy"

            @property
            def weight(self) -> float:
                return 0.35

            def collect_evidence(self) -> dict[str, Any]:
                return {...}

            def get_default_prompt(self) -> str:
                return "..."
    """

    # Model name to API ID mapping
    MODEL_MAP = {
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-20250514",
        "haiku": "claude-haiku-4-20250514",
    }

    def __init__(
        self,
        model: str = "sonnet",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
    ):
        """Initialize the judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
        """
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.output_dir = output_dir or self.working_dir / "output" / "runs"
        self.ground_truth_dir = ground_truth_dir or self.working_dir / "evaluation" / "ground-truth"
        self.use_llm = use_llm
        self._prompt_template: str | None = None

    @classmethod
    def validate_claude_cli(cls) -> tuple[bool, str]:
        """Check if Claude CLI is available and executable.

        Returns:
            Tuple of (is_valid, message). If valid, message contains the path.
            If invalid, message contains the error reason.
        """
        claude_path = shutil.which("claude")
        if not claude_path:
            return False, "Claude CLI not found in PATH"

        if not os.access(claude_path, os.X_OK):
            return False, f"Claude CLI at {claude_path} is not executable"

        return True, claude_path

    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """Name of the evaluation dimension (e.g., 'accuracy', 'coverage')."""
        ...

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight of this dimension in the overall score (0.0-1.0)."""
        ...

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file.

        Override this property to customize the prompt location.
        Default location is `../prompts/{dimension_name}.md` relative
        to the judge module.
        """
        return Path(__file__).parent / "prompts" / f"{self.dimension_name}.md"

    def load_prompt_template(self) -> str:
        """Load the prompt template from file.

        First tries to load from prompt_file. If not found, falls back
        to get_default_prompt().

        Returns:
            The prompt template string
        """
        if self._prompt_template is None:
            if self.prompt_file.exists():
                self._prompt_template = self.prompt_file.read_text()
            else:
                self._prompt_template = self.get_default_prompt()
        return self._prompt_template

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist.

        Subclasses should override this to provide a dimension-specific
        default prompt. The template should include `{{ evidence }}`
        placeholder for evidence injection.

        Returns:
            Default prompt template string
        """
        return f"""# {self.dimension_name.replace('_', ' ').title()} Evaluation

Evaluate the following evidence and provide a score from 1-5.

## Evidence

{{{{ evidence }}}}

## Response Format

Respond with ONLY a JSON object:

{{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<explanation>",
  "evidence_cited": ["<evidence points>"],
  "recommendations": ["<improvements>"],
  "sub_scores": {{}}
}}
"""

    @abstractmethod
    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence files and data for evaluation.

        Returns:
            Dictionary containing all evidence for the evaluation.
            This will be JSON-serialized and injected into the prompt.
        """
        ...

    def load_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns:
            Dictionary keyed by repo name (filename stem) to analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            json_files = list(self.output_dir.glob("*.json"))
            for json_file in sorted(json_files):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    # Handle envelope format
                    if "data" in data:
                        results[repo_name] = data.get("data", {})
                    elif "results" in data:
                        results[repo_name] = data
                    else:
                        results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    def load_ground_truth(self) -> dict[str, Any]:
        """Load all ground truth files.

        Returns:
            Dictionary keyed by repo name to ground truth data.
        """
        results = {}

        if self.ground_truth_dir.exists():
            for gt_file in sorted(self.ground_truth_dir.glob("*.json")):
                if gt_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(gt_file.read_text())
                    # Use 'id' field if present, otherwise filename stem
                    repo_name = data.get("id", gt_file.stem)
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    @staticmethod
    def extract_files(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract files list from analysis data, handling both formats.

        Supports:
            - data["results"]["files"] (current format)
            - data["files"] (legacy format)

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of file dictionaries
        """
        # Try current format first (results.files)
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("files", [])
        # Fallback to legacy format (direct files)
        return analysis.get("files", [])

    @staticmethod
    def extract_summary(analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract summary dict from analysis data, handling both formats.

        Supports:
            - data["results"]["summary"] (current format)
            - data["summary"] (legacy format)

        Args:
            analysis: Analysis data dictionary

        Returns:
            Summary dictionary
        """
        # Try current format first (results.summary)
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("summary", {})
        # Fallback to legacy format (direct summary)
        return analysis.get("summary", {})

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Uses {{ evidence }} placeholder pattern for reliability.
        All evidence is serialized as JSON and substituted into the template.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            Complete prompt string ready for LLM invocation
        """
        template = self.load_prompt_template()
        evidence_str = json.dumps(evidence, indent=2, default=str)
        return template.replace("{{ evidence }}", evidence_str)

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result.

        First attempts to extract JSON from the response. If JSON parsing
        fails, falls back to extracting score from text patterns.

        Args:
            response: Raw LLM response text

        Returns:
            JudgeResult with parsed data
        """
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
            reasoning=response[:500] if response else "No response received",
            raw_response=response,
        )

    def _invoke_via_sdk(self, prompt: str) -> str | None:
        """Invoke Claude via Anthropic SDK when available.

        Args:
            prompt: The prompt to send

        Returns:
            Response text if successful, None if SDK unavailable or error
        """
        if not HAS_ANTHROPIC_SDK:
            return None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        # Map model names to API model IDs
        model_id = self.MODEL_MAP.get(self.model, self.model)

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content = getattr(response, "content", []) or []
        return "".join(getattr(block, "text", "") for block in content)

    def _invoke_via_cli(self, prompt: str) -> str:
        """Invoke Claude Code in headless mode via CLI.

        Args:
            prompt: The prompt to send

        Returns:
            Response text or error message
        """
        claude_path = shutil.which("claude")
        if not claude_path:
            return "Error: Claude CLI not found"

        try:
            cmd = [
                "claude",
                "-p", prompt,
                "--model", self.model,
                "--output-format", "text",
                "--allowedTools", "",
                "--max-turns", "5",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.working_dir),
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "EPERM" in stderr or "permission" in stderr.lower():
                    return "Error: Permission denied executing Claude CLI"
                elif "ENOENT" in stderr:
                    return "Error: Claude CLI not found"
                return f"Error (exit {result.returncode}): {stderr[:200]}"

            return result.stdout

        except subprocess.TimeoutExpired:
            return f"Error: Claude invocation timed out after {self.timeout}s"
        except PermissionError as e:
            return f"Error: Permission denied - {e}"
        except FileNotFoundError:
            return "Error: Claude CLI not found"
        except OSError as e:
            return f"Error: OS error - {e}"
        except Exception as e:
            return f"Error: Unexpected - {type(e).__name__}: {e}"

    def invoke_claude(self, prompt: str) -> str:
        """Invoke Claude, preferring SDK and falling back to CLI.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        sdk_response = self._invoke_via_sdk(prompt)
        if sdk_response is not None:
            return sdk_response
        return self._invoke_via_cli(prompt)

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM.

        Override this method in subclasses to provide dimension-specific
        heuristic evaluation logic. The default implementation returns
        a neutral score.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            JudgeResult with heuristic-based scoring
        """
        return JudgeResult(
            dimension=self.dimension_name,
            score=3,
            confidence=0.6,
            reasoning="Heuristic evaluation not implemented for this dimension",
            evidence_cited=[],
            recommendations=["Implement run_heuristic_evaluation() for this judge"],
            raw_response="",
        )

    def evaluate(self) -> JudgeResult:
        """Run the full evaluation pipeline.

        If use_llm is False, runs heuristic evaluation only.
        Otherwise, collects evidence, builds prompt, invokes Claude,
        and parses the response.

        Returns:
            JudgeResult with evaluation outcome
        """
        # Collect evidence
        evidence = self.collect_evidence()

        # Check if we should use heuristic evaluation
        if not self.use_llm:
            return self.run_heuristic_evaluation(evidence)

        # Build prompt
        prompt = self.build_prompt(evidence)

        # Invoke Claude
        response = self.invoke_claude(prompt)

        # Parse response
        result = self.parse_response(response)

        return result

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Override this method in subclasses to add pre-evaluation
        validation checks.

        Returns:
            Tuple of (all_passed, list of failure messages)
        """
        # Default: no assertions, always pass
        return True, []

    # Legacy interface support
    def get_prompt(self, data: dict) -> str:
        """Generate the evaluation prompt (legacy interface).

        Deprecated: Use build_prompt() instead.

        Args:
            data: Evidence dictionary

        Returns:
            Prompt string
        """
        return self.build_prompt(data)
