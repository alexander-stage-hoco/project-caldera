"""Base judge class for LLM-as-a-Judge evaluation of SonarQube analysis."""

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

    Each judge evaluates a specific dimension of SonarQube analysis quality.
    Judges can invoke Claude via the Anthropic SDK or Claude Code CLI.
    """

    def __init__(
        self,
        model: str = "opus",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        output_dir: Path | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.output_dir = output_dir or self.working_dir / "evaluation" / "llm" / "results"
        self.analysis_path = analysis_path
        self._analysis_data: dict | None = None
        self._prompt_template: str | None = None

    @classmethod
    def validate_claude_cli(cls) -> tuple[bool, str]:
        """Check if Claude CLI is available and executable."""
        claude_path = shutil.which("claude")
        if not claude_path:
            return False, "Claude CLI not found in PATH"

        if not os.access(claude_path, os.X_OK):
            return False, f"Claude CLI at {claude_path} is not executable"

        return True, claude_path

    @property
    def analysis_data(self) -> dict:
        """Load and cache analysis data."""
        if self._analysis_data is None:
            if self.analysis_path is None:
                raise ValueError("analysis_path not set")
            with open(self.analysis_path) as f:
                self._analysis_data = json.load(f)
        return self._analysis_data

    @property
    def analysis_results(self) -> dict:
        """Return the normalized results payload.

        Handles both Caldera envelope format and legacy flat format.
        """
        data = self.analysis_data
        # Handle Caldera envelope format
        if "data" in data and "metadata" in data:
            inner = data["data"]
            return inner.get("results", inner)
        return data.get("results", data)

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
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name.replace(' ', '_').lower()}.md"

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

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Uses single {{ evidence }} placeholder pattern for reliability.
        All evidence is serialized as JSON and substituted into the template.
        """
        template = self.load_prompt_template()
        evidence_str = json.dumps(evidence, indent=2, default=str)
        return template.replace("{{ evidence }}", evidence_str)

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

    def _invoke_via_sdk(self, prompt: str) -> str | None:
        """Invoke Claude via Anthropic SDK when available."""
        if not HAS_ANTHROPIC_SDK:
            return None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content = getattr(response, "content", []) or []
        return "".join(getattr(block, "text", "") for block in content)

    def _invoke_via_cli(self, prompt: str) -> str:
        """Invoke Claude Code in headless mode via CLI."""
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
        """Invoke Claude, preferring SDK and falling back to CLI."""
        sdk_response = self._invoke_via_sdk(prompt)
        if sdk_response is not None:
            return sdk_response
        return self._invoke_via_cli(prompt)

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

    def _create_result(
        self,
        score: int,
        confidence: float,
        reasoning: str,
        evidence: list[str] | None = None,
        recommendations: list[str] | None = None,
        sub_scores: dict[str, int] | None = None,
    ) -> JudgeResult:
        """Create a JudgeResult with common fields."""
        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            evidence_cited=evidence or [],
            recommendations=recommendations or [],
            sub_scores=sub_scores or {},
        )
