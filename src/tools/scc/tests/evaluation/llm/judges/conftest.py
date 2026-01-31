"""Judge-specific test fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from evaluation.llm.judges.base import BaseJudge, JudgeResult
from evaluation.llm.judges.directory_analysis import DirectoryAnalysisJudge
from evaluation.llm.judges.statistics import StatisticsJudge
from evaluation.llm.judges.integration_fit import IntegrationFitJudge


@pytest.fixture
def poc_root() -> Path:
    """Return the poc-scc root directory."""
    return Path(__file__).parent.parent.parent.parent.parent


@pytest.fixture
def directory_analysis_judge(poc_root: Path) -> DirectoryAnalysisJudge:
    """Create a DirectoryAnalysisJudge for testing."""
    return DirectoryAnalysisJudge(working_dir=poc_root)


@pytest.fixture
def statistics_judge(poc_root: Path) -> StatisticsJudge:
    """Create a StatisticsJudge for testing."""
    return StatisticsJudge(working_dir=poc_root)


@pytest.fixture
def integration_fit_judge(poc_root: Path) -> IntegrationFitJudge:
    """Create an IntegrationFitJudge for testing."""
    return IntegrationFitJudge(working_dir=poc_root)


class ConcreteJudge(BaseJudge):
    """Concrete implementation of BaseJudge for testing."""

    @property
    def dimension_name(self) -> str:
        return "test_dimension"

    @property
    def weight(self) -> float:
        return 0.10

    def get_default_prompt(self) -> str:
        return "Test prompt for {{ key }}"

    def collect_evidence(self) -> dict[str, Any]:
        return {"key": "value", "nested": {"a": 1, "b": 2}}


@pytest.fixture
def concrete_judge(poc_root: Path) -> ConcreteJudge:
    """Create a concrete BaseJudge for testing."""
    return ConcreteJudge(working_dir=poc_root)


@pytest.fixture
def sample_llm_response_valid_json() -> str:
    """Sample LLM response with valid JSON."""
    return '''Based on my analysis, here is the evaluation:

{
    "dimension": "test_dimension",
    "score": 4,
    "confidence": 0.85,
    "reasoning": "The output is well-structured and complete.",
    "evidence_cited": ["field1", "field2"],
    "recommendations": ["Consider adding more detail"]
}

Overall, this is a good implementation.'''


@pytest.fixture
def sample_llm_response_score_in_text() -> str:
    """Sample LLM response with score in text (no JSON)."""
    return '''After reviewing the evidence, I would rate this:

Score: 4

The implementation meets most requirements but could be improved.'''


@pytest.fixture
def sample_llm_response_malformed_json() -> str:
    """Sample LLM response with malformed JSON."""
    return '''Here is my evaluation:

{
    "score": 3,
    "reasoning": "incomplete json
}

Missing closing brace.'''


@pytest.fixture
def sample_judge_result() -> JudgeResult:
    """Sample JudgeResult for testing."""
    return JudgeResult(
        dimension="test_dimension",
        score=4,
        confidence=0.85,
        reasoning="Test reasoning",
        evidence_cited=["evidence1", "evidence2"],
        recommendations=["recommendation1"],
        sub_scores={"sub1": 4, "sub2": 5},
        raw_response="raw response text"
    )
