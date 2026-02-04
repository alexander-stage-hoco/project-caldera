"""Base judge class for LLM-as-a-Judge evaluation of DevSkim security linting."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# Optional anthropic SDK import
try:
    import anthropic
    HAS_ANTHROPIC_SDK = True
except ImportError:
    anthropic = None  # type: ignore
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

    Each judge evaluates a specific dimension of DevSkim security
    analysis quality. Judges invoke Claude in headless mode with
    specialized prompts.
    """

    def __init__(
        self,
        model: str = "opus",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        output_dir: Path | None = None,
        evaluation_mode: str | None = None,
    ):
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self.output_dir = output_dir or self.working_dir / "output"
        self.analysis_path = analysis_path or self.working_dir / "output" / "devskim_analysis.json"
        self.evaluation_mode = evaluation_mode
        self._prompt_template: str | None = None

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir."""
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            for json_file in sorted(self.output_dir.glob("*.json")):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        if not results and self.analysis_path.exists():
            try:
                data = json.loads(self.analysis_path.read_text())
                results["default"] = data
            except json.JSONDecodeError:
                pass

        return results

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

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence."""
        template = self.load_prompt_template()
        evidence_str = json.dumps(evidence, indent=2, default=str)
        return template.replace("{{ evidence }}", evidence_str)

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result."""
        try:
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

        score = 3
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
        """Invoke Claude, trying SDK first, then CLI fallback."""
        sdk_result = self._invoke_via_sdk(prompt)
        if sdk_result is not None:
            return sdk_result
        return self._invoke_via_cli(prompt)

    def _invoke_via_sdk(self, prompt: str) -> str | None:
        """Invoke via Anthropic Python SDK."""
        if not HAS_ANTHROPIC_SDK:
            return None

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            client = anthropic.Anthropic(api_key=api_key)
            model_map = {
                "opus": "claude-opus-4-20250514",
                "sonnet": "claude-sonnet-4-20250514",
                "haiku": "claude-3-5-haiku-20241022",
            }
            model_id = model_map.get(self.model, f"claude-3-5-{self.model}-latest")

            response = client.messages.create(
                model=model_id,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception:
            return None

    def _invoke_via_cli(self, prompt: str) -> str:
        """Invoke via Claude Code CLI."""
        if not shutil.which("claude"):
            return "Error: Neither Anthropic SDK (ANTHROPIC_API_KEY) nor Claude CLI available"

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
                return f"Error: {result.stderr}"

            return result.stdout

        except subprocess.TimeoutExpired:
            return "Error: Claude invocation timed out"
        except Exception as e:
            return f"Error: {e}"

    def evaluate(self) -> JudgeResult:
        """Run the full evaluation pipeline."""
        evidence = self.collect_evidence()
        prompt = self.build_prompt(evidence)
        response = self.invoke_claude(prompt)
        result = self.parse_response(response)
        return result

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        return True, []
