"""LLM-as-a-Judge evaluation module for coverage-ingest.

This module provides LLM-based evaluation of coverage-ingest output quality
across three dimensions:

1. Risk Tier Quality (35%): Evaluates correctness of risk tier classifications
2. Gap Actionability (35%): Evaluates if coverage gaps enable developer action
3. Cross-Format Consistency (30%): Evaluates consistency across format parsers

Usage:
    from evaluation.llm import run_all_judges, JUDGES

    results = run_all_judges(output_dir=Path("outputs/run-123"))
"""

from .judges import (
    JUDGES,
    BaseJudge,
    JudgeResult,
    RiskTierQualityJudge,
    GapActionabilityJudge,
    CrossFormatConsistencyJudge,
)
from .orchestrator import run_all_judges, get_grade, print_report

__all__ = [
    # Orchestration
    "run_all_judges",
    "get_grade",
    "print_report",
    # Registry
    "JUDGES",
    # Base classes
    "BaseJudge",
    "JudgeResult",
    # Judge classes
    "RiskTierQualityJudge",
    "GapActionabilityJudge",
    "CrossFormatConsistencyJudge",
]
