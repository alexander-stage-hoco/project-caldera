"""LLM-based error analysis for failing checks."""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from scripts.checks import CheckResult


# Check if observable provider is available
try:
    from insights.evaluation.llm.providers import get_observable_provider
    PROVIDER_AVAILABLE = True
except ImportError:
    PROVIDER_AVAILABLE = False


ERROR_ANALYSIS_PROMPT = """You are analyzing a failing evaluation check for a code analysis tool (scc).

## Check Details
- **Check ID**: {check_id}
- **Check Name**: {check_name}
- **Expected**: {expected}
- **Actual**: {actual}
- **Message**: {message}

## Evidence
{evidence}

## Task
Analyze why this check failed and provide:
1. Root cause analysis (1-2 sentences)
2. Impact assessment (how serious is this failure?)
3. Remediation suggestions (what could be done to fix it?)

Be concise and actionable.
"""


def get_provider() -> Optional[Any]:
    """Get observable LLM provider if available."""
    if not PROVIDER_AVAILABLE:
        return None

    try:
        return get_observable_provider("anthropic", trace_id=None)
    except (ValueError, ImportError):
        return None


def analyze_failure(check: CheckResult, model: str = "claude-3-haiku-20240307") -> Dict[str, Any]:
    """Use LLM to analyze why a check failed."""
    if check.passed:
        return {"analysis": "Check passed, no analysis needed", "llm_available": False}

    provider = get_provider()

    if not provider:
        return {
            "analysis": "LLM analysis skipped (provider not available)",
            "root_cause": "Unknown",
            "impact": "Unknown",
            "remediation": "Manual investigation required",
            "llm_available": False
        }

    prompt = ERROR_ANALYSIS_PROMPT.format(
        check_id=check.check_id,
        check_name=check.name,
        expected=check.expected or "N/A",
        actual=check.actual or "N/A",
        message=check.message,
        evidence=json.dumps(check.evidence, indent=2) if check.evidence else "None"
    )

    try:
        response = provider.complete(
            prompt=prompt,
            model=model,
            max_tokens=500,
        )

        content = response.content

        return {
            "analysis": content,
            "llm_available": True
        }

    except Exception as e:
        return {
            "analysis": f"LLM error: {str(e)}",
            "llm_available": True,
            "error": str(e)
        }


def analyze_all_failures(checks: List[CheckResult]) -> Dict[str, Dict[str, Any]]:
    """Analyze all failing checks."""
    results = {}

    failing_checks = [c for c in checks if not c.passed]

    if not failing_checks:
        return {"summary": "All checks passed, no failures to analyze"}

    for check in failing_checks:
        results[check.check_id] = analyze_failure(check)

    return results


def generate_failure_report(checks: List[CheckResult]) -> str:
    """Generate a failure analysis report."""
    failing_checks = [c for c in checks if not c.passed]

    if not failing_checks:
        return "# Failure Analysis Report\n\nAll checks passed! No failures to analyze."

    lines = [
        "# Failure Analysis Report",
        "",
        f"**Total Failing Checks:** {len(failing_checks)}",
        ""
    ]

    # Group by dimension (extract from check_id prefix)
    for check in failing_checks:
        lines.extend([
            f"## {check.check_id}: {check.name}",
            "",
            f"**Status:** FAILED",
            f"**Message:** {check.message}",
            ""
        ])

        if check.expected:
            lines.append(f"**Expected:** {check.expected}")
        if check.actual:
            lines.append(f"**Actual:** {check.actual}")

        # Add LLM analysis if available
        analysis = analyze_failure(check)
        if analysis.get("llm_available"):
            lines.extend([
                "",
                "### Analysis",
                analysis.get("analysis", "No analysis available"),
                ""
            ])
        else:
            lines.extend([
                "",
                "### Analysis",
                "_LLM analysis not available (set ANTHROPIC_API_KEY to enable)_",
                ""
            ])

    return "\n".join(lines)
