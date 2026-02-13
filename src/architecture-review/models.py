"""Data models for the architecture reviewer.

Frozen dataclasses matching the review_result.schema.json output schema.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

VALID_SEVERITIES = frozenset({"error", "warning", "info"})
VALID_STATUSES = frozenset({"pass", "warn", "fail"})
VALID_REVIEW_TYPES = frozenset({"tool_implementation", "cross_tool", "blueprint_alignment"})
VALID_OVERALL_STATUSES = frozenset({"STRONG_PASS", "PASS", "WEAK_PASS", "NEEDS_WORK"})
VALID_CATEGORIES = frozenset({
    "pattern_violation",
    "missing_requirement",
    "inconsistency",
    "anti_pattern",
    "placeholder_content",
    "naming_drift",
})


@dataclass(frozen=True)
class Finding:
    """Individual architecture review finding."""

    severity: str
    rule_id: str
    message: str
    category: str | None = None
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    recommendation: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(VALID_SEVERITIES)}, got '{self.severity}'")
        if not self.rule_id:
            raise ValueError("rule_id must be non-empty")
        if not self.message:
            raise ValueError("message must be non-empty")
        if self.category is not None and self.category not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}, got '{self.category}'")
        if self.line is not None and self.line < 1:
            raise ValueError("line must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "severity": self.severity,
            "rule_id": self.rule_id,
            "message": self.message,
        }
        if self.category is not None:
            d["category"] = self.category
        if self.file is not None:
            d["file"] = self.file
        if self.line is not None:
            d["line"] = self.line
        if self.evidence is not None:
            d["evidence"] = self.evidence
        if self.recommendation is not None:
            d["recommendation"] = self.recommendation
        return d


@dataclass(frozen=True)
class DimensionResult:
    """Results for a single review dimension."""

    dimension: str
    weight: float
    status: str
    score: int
    findings: list[Finding] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.dimension:
            raise ValueError("dimension must be non-empty")
        if not 0 <= self.weight <= 1:
            raise ValueError(f"weight must be between 0 and 1, got {self.weight}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}, got '{self.status}'")
        if not 1 <= self.score <= 5:
            raise ValueError(f"score must be between 1 and 5, got {self.score}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "weight": self.weight,
            "status": self.status,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass(frozen=True)
class ReviewSummary:
    """Summary across all reviewed dimensions."""

    total_findings: int
    by_severity: dict[str, int]
    overall_status: str
    overall_score: float
    dimensions_reviewed: int

    def __post_init__(self) -> None:
        if self.total_findings < 0:
            raise ValueError("total_findings must be >= 0")
        for sev in ("error", "warning", "info"):
            if sev not in self.by_severity:
                raise ValueError(f"by_severity must contain key '{sev}'")
            if self.by_severity[sev] < 0:
                raise ValueError(f"by_severity['{sev}'] must be >= 0")
        if self.overall_status not in VALID_OVERALL_STATUSES:
            raise ValueError(
                f"overall_status must be one of {sorted(VALID_OVERALL_STATUSES)}, "
                f"got '{self.overall_status}'"
            )
        if not 1 <= self.overall_score <= 5:
            raise ValueError(f"overall_score must be between 1 and 5, got {self.overall_score}")
        if self.dimensions_reviewed < 1:
            raise ValueError("dimensions_reviewed must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_findings": self.total_findings,
            "by_severity": dict(self.by_severity),
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "dimensions_reviewed": self.dimensions_reviewed,
        }


@dataclass(frozen=True)
class ReviewResult:
    """Complete architecture review result."""

    review_id: str
    timestamp: str
    target: str
    review_type: str
    dimensions: list[DimensionResult]
    summary: ReviewSummary

    def __post_init__(self) -> None:
        if not self.review_id:
            raise ValueError("review_id must be non-empty")
        if not self.timestamp:
            raise ValueError("timestamp must be non-empty")
        if not self.target:
            raise ValueError("target must be non-empty")
        if self.review_type not in VALID_REVIEW_TYPES:
            raise ValueError(
                f"review_type must be one of {sorted(VALID_REVIEW_TYPES)}, "
                f"got '{self.review_type}'"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "timestamp": self.timestamp,
            "target": self.target,
            "review_type": self.review_type,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "summary": self.summary.to_dict(),
        }

    @staticmethod
    def create_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def create_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
