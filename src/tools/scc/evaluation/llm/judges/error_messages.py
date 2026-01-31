"""Error Messages Judge - evaluates error message quality."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ErrorMessagesJudge(BaseJudge):
    """Evaluates the quality of scc error messages."""

    @property
    def dimension_name(self) -> str:
        return "error_messages"

    @property
    def weight(self) -> float:
        return 0.08  # 8%

    def get_default_prompt(self) -> str:
        return """# Error Messages Judge

Evaluate scc error message quality. Score 1-5:
- 5: Clear, actionable with suggestions
- 4: Informative, points to problem
- 3: Basic error info
- 2: Vague messages
- 1: Cryptic errors or silent failures

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect error scenarios and messages."""
        error_scenarios = []
        error_messages = []
        exit_codes = {}

        # Test: nonexistent path
        try:
            result = subprocess.run(
                ["./bin/scc", "/nonexistent/path/xyz"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.working_dir),
            )
            error_scenarios.append("Nonexistent path")
            error_messages.append(result.stderr or result.stdout)
            exit_codes["nonexistent_path"] = result.returncode
        except Exception as e:
            error_messages.append(f"Error running test: {e}")

        # Test: invalid flag
        try:
            result = subprocess.run(
                ["./bin/scc", "--invalid-flag-xyz"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.working_dir),
            )
            error_scenarios.append("Invalid flag")
            error_messages.append(result.stderr or result.stdout)
            exit_codes["invalid_flag"] = result.returncode
        except Exception as e:
            error_messages.append(f"Error running test: {e}")

        return {
            "error_scenarios": error_scenarios,
            "error_messages": "\n---\n".join(error_messages),
            "exit_codes": exit_codes,
        }

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
