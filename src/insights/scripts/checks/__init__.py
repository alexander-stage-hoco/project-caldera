"""
Programmatic evaluation checks for Insights reports.

Check IDs follow the pattern: IN-{DIMENSION}-{NUMBER}
- IN-AC-*: Accuracy checks
- IN-CM-*: Completeness checks
- IN-FQ-*: Format quality checks
- IN-DI-*: Data integrity checks
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from functools import wraps


class CheckResult(Enum):
    """Result of a check execution."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class CheckOutput:
    """Output from a single check execution."""

    check_id: str
    name: str
    result: CheckResult
    score: float  # 0.0 to 1.0
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckDefinition:
    """Definition of an evaluation check."""

    check_id: str
    name: str
    description: str
    dimension: str
    weight: float  # Relative weight within dimension
    check_fn: Callable[..., CheckOutput]


# Registry of all checks
CHECK_REGISTRY: dict[str, CheckDefinition] = {}


def register_check(
    check_id: str,
    name: str,
    description: str,
    dimension: str,
    weight: float = 1.0,
) -> Callable:
    """Decorator to register a check function."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> CheckOutput:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                return CheckOutput(
                    check_id=check_id,
                    name=name,
                    result=CheckResult.ERROR,
                    score=0.0,
                    message=f"Check raised exception: {e}",
                    details={"exception": str(e)},
                )

        CHECK_REGISTRY[check_id] = CheckDefinition(
            check_id=check_id,
            name=name,
            description=description,
            dimension=dimension,
            weight=weight,
            check_fn=wrapper,
        )
        return wrapper

    return decorator


def get_checks_by_dimension(dimension: str) -> list[CheckDefinition]:
    """Get all checks for a given dimension."""
    return [c for c in CHECK_REGISTRY.values() if c.dimension == dimension]


def get_all_checks() -> list[CheckDefinition]:
    """Get all registered checks."""
    return list(CHECK_REGISTRY.values())


def run_check(check_id: str, **kwargs: Any) -> CheckOutput:
    """Run a single check by ID."""
    if check_id not in CHECK_REGISTRY:
        raise ValueError(f"Unknown check: {check_id}")
    return CHECK_REGISTRY[check_id].check_fn(**kwargs)


def run_all_checks(**kwargs: Any) -> list[CheckOutput]:
    """Run all registered checks."""
    return [check.check_fn(**kwargs) for check in CHECK_REGISTRY.values()]


# Import all check modules to register them
# This ensures checks are registered when the package is imported
# NOTE: These imports must come AFTER all class/function definitions to avoid circular imports
from .accuracy import ACCURACY_CHECKS  # noqa: E402
from .completeness import COMPLETENESS_CHECKS  # noqa: E402
from .format_quality import FORMAT_QUALITY_CHECKS  # noqa: E402
from .data_integrity import DATA_INTEGRITY_CHECKS  # noqa: E402

__all__ = [
    "CheckResult",
    "CheckOutput",
    "CheckDefinition",
    "register_check",
    "get_checks_by_dimension",
    "get_all_checks",
    "run_check",
    "run_all_checks",
    "CHECK_REGISTRY",
    "ACCURACY_CHECKS",
    "COMPLETENESS_CHECKS",
    "FORMAT_QUALITY_CHECKS",
    "DATA_INTEGRITY_CHECKS",
]
