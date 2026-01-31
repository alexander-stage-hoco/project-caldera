"""API Design Judge - evaluates CLI usability and automation friendliness."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class APIDesignJudge(BaseJudge):
    """Evaluates the CLI API design of scc."""

    @property
    def dimension_name(self) -> str:
        return "api_design"

    @property
    def weight(self) -> float:
        return 0.10  # 10%

    def get_default_prompt(self) -> str:
        return """# API Design Judge

Evaluate scc CLI design. Score 1-5:
- 5: Intuitive flags, consistent, excellent defaults
- 4: Clear options, good defaults
- 3: Functional but some confusion
- 2: Inconsistent, hard to script
- 1: Unusable for automation

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect CLI usage evidence."""
        # Get help output
        help_output = ""
        try:
            result = subprocess.run(
                ["./bin/scc", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.working_dir),
            )
            help_output = result.stdout or result.stderr
        except Exception as e:
            help_output = f"Error: {e}"

        # Document usage examples
        usage_examples = """
# Basic usage
scc .

# JSON output
scc -f json .

# CSV output
scc -f csv .

# Per-file output
scc --by-file -f json .

# With COCOMO
scc --cocomo-project-type organic .

# Exclude directories
scc --exclude-dir vendor,node_modules .
"""

        # Test flag combinations
        flag_combinations = {
            "-f json": "JSON format output",
            "-f csv": "CSV format output",
            "--by-file": "Per-file breakdown",
            "--no-complexity": "Disable complexity calculation",
            "--include-ext py,go": "Include only specific extensions",
            "--exclude-dir vendor": "Exclude directories",
        }

        return {
            "help_output": help_output,
            "usage_examples": usage_examples,
            "flag_combinations": flag_combinations,
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
