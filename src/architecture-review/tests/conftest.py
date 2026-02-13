"""Shared test fixtures for architecture reviewer tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure architecture-review root and project src/ are on sys.path
_arch_review_root = Path(__file__).resolve().parent.parent
_project_root = _arch_review_root.parent.parent

if str(_arch_review_root) not in sys.path:
    sys.path.insert(0, str(_arch_review_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

import pytest

from models import DimensionResult, Finding, ReviewResult, ReviewSummary


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return _project_root


@pytest.fixture
def sample_finding() -> Finding:
    """Return a valid Finding instance."""
    return Finding(
        severity="warning",
        rule_id="ENTITY_FROZEN",
        message="Entity class is not frozen",
        category="pattern_violation",
        file="src/sot-engine/persistence/entities.py",
        line=42,
        evidence="@dataclass\nclass Foo:",
        recommendation="Add frozen=True to @dataclass decorator",
    )


@pytest.fixture
def sample_dimension_result(sample_finding: Finding) -> DimensionResult:
    """Return a valid DimensionResult instance."""
    return DimensionResult(
        dimension="entity_persistence_pattern",
        weight=0.20,
        status="warn",
        score=3,
        findings=[sample_finding],
    )
