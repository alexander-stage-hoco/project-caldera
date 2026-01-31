"""Risk Judge - evaluates production risks of using scc."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class RiskJudge(BaseJudge):
    """Evaluates production risks of scc."""

    @property
    def dimension_name(self) -> str:
        return "risk"

    @property
    def weight(self) -> float:
        return 0.08  # 8%

    def get_default_prompt(self) -> str:
        return """# Risk Judge

Evaluate scc production risks. Score 1-5:
- 5: Production ready, no significant risks
- 4: Low risk, minor concerns
- 3: Moderate risk, manageable
- 2: High risk, needs mitigation
- 1: Not production ready

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect risk assessment evidence."""
        results_dir = self.working_dir / "evaluation" / "results"

        # Project health metrics
        project_health = {
            "github_stars": "6,400+",
            "last_release": "2024 (v3.6.0)",
            "open_issues": "~50",
            "license": "MIT/Unlicense (dual)",
            "language": "Go",
            "contributors": "50+",
        }

        # Load test results
        test_results = {}
        latest_results = sorted(results_dir.glob("eval-*.json"))
        if latest_results:
            data = json.loads(latest_results[-1].read_text())
            test_results = {
                "total_checks": data.get("total_checks", 0),
                "passed_checks": data.get("passed_checks", 0),
                "score": data.get("total_score", 0),
            }

        # Known issues
        known_issues = """
## Known Considerations

1. **Large Repos**: May use significant memory on very large repos (1M+ files)
   - Mitigation: Use --exclude-dir for vendor/generated code

2. **Language Detection**: Some edge cases in language detection
   - Mitigation: Use --include-ext to force specific languages

3. **Complexity Algorithm**: Uses default complexity (not language-specific)
   - Note: Good for relative comparison, not absolute measures

4. **No CVEs**: No known security vulnerabilities

5. **Dependencies**: Single binary, no runtime dependencies
"""

        return {
            "github_stars": project_health["github_stars"],
            "last_release": project_health["last_release"],
            "open_issues": project_health["open_issues"],
            "license": project_health["license"],
            "test_results": test_results,
            "known_issues": known_issues,
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
