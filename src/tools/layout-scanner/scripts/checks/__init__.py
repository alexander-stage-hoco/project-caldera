"""
Evaluation Checks Framework for Layout Scanner.

Provides the CheckResult dataclass and check registration infrastructure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class CheckCategory(Enum):
    """Categories for evaluation checks."""
    OUTPUT_QUALITY = "output_quality"
    ACCURACY = "accuracy"
    CLASSIFICATION = "classification"
    PERFORMANCE = "performance"
    EDGE_CASES = "edge_cases"
    GIT_METADATA = "git_metadata"
    CONTENT_METADATA = "content_metadata"


@dataclass
class CheckResult:
    """Result of running a single evaluation check."""
    check_id: str
    name: str
    category: CheckCategory
    passed: bool
    score: float  # 0.0 to 1.0
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category.value,
            "passed": self.passed,
            "score": self.score,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass
class DimensionResult:
    """Result for an entire dimension of checks."""
    category: CheckCategory
    checks: List[CheckResult]
    passed_count: int
    total_count: int
    score: float  # 1.0 to 5.0

    @classmethod
    def from_checks(cls, category: CheckCategory, checks: List[CheckResult]) -> "DimensionResult":
        """Create dimension result from check results."""
        passed = sum(1 for c in checks if c.passed)
        total = len(checks)

        # Convert to 1-5 score based on pass rate
        pass_rate = passed / total if total > 0 else 0
        score = 1.0 + (pass_rate * 4.0)  # Maps 0-100% to 1-5

        return cls(
            category=category,
            checks=checks,
            passed_count=passed,
            total_count=total,
            score=round(score, 2),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "score": self.score,
            "checks": [c.to_dict() for c in self.checks],
        }


# Scoring tables for each dimension
SCORING_TABLES = {
    CheckCategory.OUTPUT_QUALITY: {8: 5.0, 7: 4.0, 5: 3.0, 3: 2.0, 0: 1.0},
    CheckCategory.ACCURACY: {8: 5.0, 7: 4.0, 5: 3.0, 3: 2.0, 0: 1.0},
    CheckCategory.CLASSIFICATION: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.PERFORMANCE: {4: 5.0, 3: 4.0, 2: 3.0, 1: 2.0, 0: 1.0},
    CheckCategory.EDGE_CASES: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.GIT_METADATA: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
    CheckCategory.CONTENT_METADATA: {6: 5.0, 5: 4.0, 4: 3.0, 2: 2.0, 0: 1.0},
}

# Dimension weights for overall score
# Note: GIT_METADATA and CONTENT_METADATA are optional and only factored in when their passes are enabled
DIMENSION_WEIGHTS = {
    CheckCategory.OUTPUT_QUALITY: 0.25,
    CheckCategory.ACCURACY: 0.25,
    CheckCategory.CLASSIFICATION: 0.20,
    CheckCategory.PERFORMANCE: 0.15,
    CheckCategory.EDGE_CASES: 0.15,
    CheckCategory.GIT_METADATA: 0.0,  # Optional, weighted separately when present
    CheckCategory.CONTENT_METADATA: 0.0,  # Optional, weighted separately when present
}

# Decision thresholds
DECISION_THRESHOLDS = {
    "STRONG_PASS": 4.0,
    "PASS": 3.5,
    "WEAK_PASS": 3.0,
    "FAIL": 0.0,
}


def score_from_table(category: CheckCategory, passed_count: int) -> float:
    """Get score from scoring table based on passed check count."""
    table = SCORING_TABLES.get(category, {})
    for threshold, score in sorted(table.items(), reverse=True):
        if passed_count >= threshold:
            return score
    return 1.0


def calculate_overall_score(dimension_results: List[DimensionResult]) -> float:
    """Calculate weighted overall score."""
    total_weight = 0.0
    weighted_sum = 0.0

    for result in dimension_results:
        weight = DIMENSION_WEIGHTS.get(result.category, 0.0)
        weighted_sum += result.score * weight
        total_weight += weight

    if total_weight == 0:
        return 1.0

    return round(weighted_sum / total_weight, 2)


def get_decision(overall_score: float) -> str:
    """Get decision based on overall score."""
    if overall_score >= DECISION_THRESHOLDS["STRONG_PASS"]:
        return "STRONG_PASS"
    elif overall_score >= DECISION_THRESHOLDS["PASS"]:
        return "PASS"
    elif overall_score >= DECISION_THRESHOLDS["WEAK_PASS"]:
        return "WEAK_PASS"
    else:
        return "FAIL"


# Check registry
_check_registry: Dict[str, Callable] = {}


def register_check(check_id: str) -> Callable:
    """Decorator to register a check function."""
    def decorator(func: Callable) -> Callable:
        _check_registry[check_id] = func
        return func
    return decorator


def get_check(check_id: str) -> Optional[Callable]:
    """Get a registered check by ID."""
    return _check_registry.get(check_id)


def get_all_checks() -> Dict[str, Callable]:
    """Get all registered checks."""
    return _check_registry.copy()
