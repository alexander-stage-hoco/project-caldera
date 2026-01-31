"""Documentation Judge - evaluates documentation quality."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class DocumentationJudge(BaseJudge):
    """Evaluates scc documentation quality."""

    @property
    def dimension_name(self) -> str:
        return "documentation"

    @property
    def weight(self) -> float:
        return 0.08  # 8%

    def get_default_prompt(self) -> str:
        return """# Documentation Judge

Evaluate scc documentation quality. Score 1-5:
- 5: Comprehensive docs, examples, troubleshooting
- 4: Clear usage, common examples
- 3: Basic usage documented
- 2: Missing important docs
- 1: Cannot understand without source

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect documentation from scc."""
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
            help_output = f"Error getting help: {e}"

        # Check for README
        readme_content = ""
        readme_file = self.working_dir / "README.md"
        if readme_file.exists():
            readme_content = readme_file.read_text()[:5000]  # First 5000 chars
        else:
            # Try to get from scc repo info
            readme_content = "(README not found in working directory)"

        # List doc files
        doc_files = []
        docs_dir = self.working_dir / "docs"
        if docs_dir.exists():
            doc_files = [f.name for f in docs_dir.glob("*.md")]

        return {
            "readme_content": readme_content,
            "help_output": help_output,
            "doc_files": doc_files,
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
