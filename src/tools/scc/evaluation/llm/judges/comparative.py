"""Comparative Judge - evaluates scc against alternative tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ComparativeJudge(BaseJudge):
    """Compares scc against alternative tools."""

    @property
    def dimension_name(self) -> str:
        return "comparative"

    @property
    def weight(self) -> float:
        return 0.08  # 8%

    def get_default_prompt(self) -> str:
        return """# Comparative Judge

Compare scc to alternatives (cloc, tokei, loc). Score 1-5:
- 5: Best in class
- 4: Above average
- 3: Competitive
- 2: Below average
- 1: Inferior

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect comparative data."""
        output_dir = self.working_dir / "output"
        results_dir = self.working_dir / "evaluation" / "results"

        # Load scc results
        scc_results = {}
        raw_file = output_dir / "raw_scc_output.json"
        if raw_file.exists():
            scc_results = json.loads(raw_file.read_text())

        # Load performance metrics from evaluation
        performance_data = {}
        latest_results = sorted(results_dir.glob("eval-*.json"))
        if latest_results:
            data = json.loads(latest_results[-1].read_text())
            for dim in data.get("dimensions", []):
                if dim.get("name") == "performance":
                    performance_data = dim

        # Known comparisons (from research)
        alternative_results = """
## Known Tool Comparisons

### scc (v3.6.0)
- Language: Go
- Speed: Very fast (parallel processing)
- Features: Complexity, COCOMO, per-file, JSON/CSV/SQL output
- Stars: 6.4k+ GitHub
- Active: Yes (2024 releases)

### cloc
- Language: Perl
- Speed: Slower than scc
- Features: Wide language support, mature
- Stars: 18k+ GitHub
- Active: Yes

### tokei
- Language: Rust
- Speed: Fast
- Features: Accurate, good CLI
- Stars: 10k+ GitHub
- Active: Yes

### loc
- Language: Rust
- Speed: Very fast (minimal features)
- Features: Minimal, just counts
- Stars: 2k+ GitHub
- Active: Limited

## scc Advantages
- Complexity calculation built-in
- COCOMO cost estimation
- Per-file analysis with --by-file
- Directory-level rollups
- Multiple output formats (JSON, CSV, SQL)
"""

        return {
            "scc_results": scc_results,
            "alternative_results": alternative_results,
            "performance": performance_data,
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
