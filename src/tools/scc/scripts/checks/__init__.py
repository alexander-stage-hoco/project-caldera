"""Evaluation checks module for scc PoC."""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from pathlib import Path
import json


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str
    name: str
    passed: bool
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    evidence: Optional[dict] = field(default_factory=dict)


@dataclass
class DimensionResult:
    """Result for an evaluation dimension."""
    dimension: str
    weight: float
    checks: List[CheckResult]
    score: int  # 1-5
    weighted_score: float

    @property
    def checks_passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def checks_total(self) -> int:
        return len(self.checks)


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    run_id: str
    timestamp: str
    dimensions: List[DimensionResult]
    total_score: float
    decision: str  # STRONG_PASS, PASS, WEAK_PASS, FAIL
    summary: dict = field(default_factory=dict)


def load_json(path: Path) -> Any:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def load_ground_truth(base_path: Path) -> dict:
    """Load ground truth files."""
    gt_path = base_path / "evaluation" / "ground-truth"
    return {
        "synthetic": load_json(gt_path / "synthetic.json"),
        "behavior": load_json(gt_path / "expected_behavior.json")
    }
