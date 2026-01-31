"""Code Quality Judge - evaluates output richness and expressiveness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class CodeQualityJudge(BaseJudge):
    """Evaluates the richness and expressiveness of scc output."""

    @property
    def dimension_name(self) -> str:
        return "code_quality"

    @property
    def weight(self) -> float:
        return 0.10  # 10%

    def get_default_prompt(self) -> str:
        return """# Code Quality Judge

Evaluate the output richness of scc. Score 1-5 based on:
- 5: All metrics present, excellent structure
- 4: Core metrics with good detail
- 3: Basic counts present
- 2: Missing important metrics
- 1: Insufficient data

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect raw scc output for evaluation."""
        output_dir = self.working_dir / "output"

        # Load raw scc output
        raw_output = {}
        raw_file = output_dir / "raw_scc_output.json"
        if raw_file.exists():
            raw_output = json.loads(raw_file.read_text())

        # Load per-file output
        per_file_sample = {}
        full_file = output_dir / "raw_scc_full.json"
        if full_file.exists():
            full_data = json.loads(full_file.read_text())
            # Sample first language with files
            for lang in full_data:
                if lang.get("Files"):
                    per_file_sample = {
                        "language": lang.get("Name"),
                        "file_sample": lang["Files"][:2] if len(lang["Files"]) > 2 else lang["Files"]
                    }
                    break

        return {
            "raw_output": raw_output,
            "per_file_sample": per_file_sample,
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
