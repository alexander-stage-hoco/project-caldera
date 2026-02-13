"""D4: Evaluation Infrastructure checks.

Validates BaseJudge inheritance, judge count, prompt evidence placeholders,
observability enforcement, and synthetic context.
"""

from __future__ import annotations

from pathlib import Path

from discovery import ToolFiles
from models import Finding

DIMENSION = "evaluation_infrastructure"
WEIGHT = 0.15


def check_d4(tool_files: ToolFiles) -> list[Finding]:
    """Run all D4 checks for a tool."""
    findings: list[Finding] = []

    findings.extend(_check_judge_base_shared(tool_files))
    findings.extend(_check_judge_min_4(tool_files))
    findings.extend(_check_prompt_evidence(tool_files))
    findings.extend(_check_observability_enforced(tool_files))

    return findings


def _check_judge_base_shared(tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if not tf.judges_dir or not tf.judges_dir.exists():
        findings.append(Finding(
            severity="warning",
            rule_id="JUDGE_DIR_MISSING",
            message="LLM judges directory not found",
            category="missing_requirement",
        ))
        return findings

    base_file = tf.judges_dir / "base.py"
    if not base_file.exists():
        findings.append(Finding(
            severity="info",
            rule_id="JUDGE_BASE_SHARED",
            message="No base.py in judges directory",
            category="pattern_violation",
            file=_rel(tf.judges_dir),
            recommendation="Create base.py that imports from shared.evaluation.base_judge",
        ))
        return findings

    content = base_file.read_text()
    if "BaseJudge" not in content and "base_judge" not in content:
        findings.append(Finding(
            severity="warning",
            rule_id="JUDGE_BASE_SHARED",
            message="judges/base.py does not reference shared BaseJudge",
            category="pattern_violation",
            file=_rel(base_file),
            recommendation="Import and extend shared.evaluation.base_judge.BaseJudge",
        ))
    return findings


def _check_judge_min_4(tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if not tf.judges_dir or not tf.judges_dir.exists():
        return findings

    judge_files = [
        f for f in tf.judges_dir.glob("*.py")
        if f.name not in ("__init__.py", "base.py")
    ]
    if len(judge_files) < 4:
        findings.append(Finding(
            severity="warning",
            rule_id="JUDGE_MIN_4",
            message=f"Only {len(judge_files)} judge(s) found, minimum recommended is 4",
            category="missing_requirement",
            file=_rel(tf.judges_dir),
            evidence=f"Found: {[f.name for f in judge_files]}",
            recommendation="Add more LLM judges for comprehensive evaluation",
        ))
    return findings


def _check_prompt_evidence(tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if not tf.prompts_dir or not tf.prompts_dir.exists():
        findings.append(Finding(
            severity="warning",
            rule_id="PROMPTS_DIR_MISSING",
            message="LLM prompts directory not found",
            category="missing_requirement",
        ))
        return findings

    prompt_files = list(tf.prompts_dir.glob("*.md"))
    if not prompt_files:
        findings.append(Finding(
            severity="warning",
            rule_id="PROMPTS_EMPTY",
            message="No prompt files found in prompts directory",
            category="missing_requirement",
            file=_rel(tf.prompts_dir),
        ))
        return findings

    missing_evidence = []
    for pf in prompt_files:
        content = pf.read_text()
        if "{{ evidence }}" not in content and "{{evidence}}" not in content:
            missing_evidence.append(pf.name)

    if missing_evidence:
        findings.append(Finding(
            severity="info",
            rule_id="PROMPT_EVIDENCE",
            message=f"Prompts missing '{{{{ evidence }}}}' placeholder: {missing_evidence}",
            category="pattern_violation",
            file=_rel(tf.prompts_dir),
            recommendation="Add {{ evidence }} placeholder to prompt templates",
        ))
    return findings


def _check_observability_enforced(tf: ToolFiles) -> list[Finding]:
    findings: list[Finding] = []
    if not tf.eval_orchestrator or not tf.eval_orchestrator.exists():
        findings.append(Finding(
            severity="info",
            rule_id="OBSERVABILITY_ENFORCED",
            message="Evaluation orchestrator not found",
            category="missing_requirement",
        ))
        return findings

    content = tf.eval_orchestrator.read_text()
    has_observability = "observability" in content or "trace" in content or "log_interaction" in content
    if not has_observability:
        findings.append(Finding(
            severity="info",
            rule_id="OBSERVABILITY_ENFORCED",
            message="Evaluation orchestrator does not reference observability/tracing",
            category="pattern_violation",
            file=_rel(tf.eval_orchestrator),
            recommendation="Integrate shared.observability for LLM interaction logging",
        ))
    return findings


def _rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        p = path
        while p != p.parent:
            if (p / "CLAUDE.md").exists():
                return str(path.relative_to(p))
            p = p.parent
    except (ValueError, OSError):
        pass
    return str(path)
