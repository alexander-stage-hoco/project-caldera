"""Base judge class for LLM-as-a-Judge evaluation of Semgrep smell detection."""

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

    Each judge evaluates a specific dimension of Semgrep code smell
    detection quality. Judges invoke Claude Code in headless mode with
    specialized prompts.
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
        # Support both single file and directory of files
        self.output_dir = output_dir or self.working_dir / "output" / "runs"
        # Legacy single file path (for backwards compatibility)
        self.analysis_path = analysis_path or self.working_dir / "output" / "smell_analysis.json"
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

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        Falls back to single analysis_path file if output_dir doesn't exist.

        Note: The returned data structure may have files under either:
        - data["files"] (legacy format)
        - data["results"]["files"] (current format)

        Use extract_files() and extract_summary() helpers to access data.
        """
        import sys
        results = {}

        # Debug: Print what we're looking for
        print(f"  [DEBUG] Looking for analysis files in: {self.output_dir}", file=sys.stderr)

        # Try output_dir first (new pattern)
        if self.output_dir.exists() and self.output_dir.is_dir():
            json_files = list(self.output_dir.glob("*.json"))
            print(f"  [DEBUG] Found {len(json_files)} JSON files", file=sys.stderr)
            for json_file in sorted(json_files):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    results[repo_name] = data
                    print(f"  [DEBUG] Loaded: {json_file.name}", file=sys.stderr)
                except json.JSONDecodeError as e:
                    print(f"  [DEBUG] Failed to parse {json_file.name}: {e}", file=sys.stderr)
                    continue
        else:
            print(f"  [DEBUG] output_dir does not exist or is not a directory", file=sys.stderr)

        # Fallback to single file (legacy pattern)
        if not results and self.analysis_path.exists():
            print(f"  [DEBUG] Falling back to single file: {self.analysis_path}", file=sys.stderr)
            try:
                data = json.loads(self.analysis_path.read_text())
                results["default"] = data
            except json.JSONDecodeError:
                pass

        if not results:
            print(f"  [DEBUG] WARNING: No analysis results loaded!", file=sys.stderr)

        return results

    @staticmethod
    def extract_files(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract files list from analysis data, handling both formats.

        Supports:
        - data["results"]["files"] (current format)
        - data["files"] (legacy format)
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
        """
        # Try current format first (results.summary)
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("summary", {})
        # Fallback to legacy format (direct summary)
        return analysis.get("summary", {})

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
        """Build the complete prompt with evidence.

        Uses single {{ evidence }} placeholder pattern (like trivy) for reliability.
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
