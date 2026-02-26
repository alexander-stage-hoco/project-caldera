"""Sampling rationale section — explains what was analyzed and why."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from .base import EvidenceAwareSection, SectionConfig


class SamplingRationaleSection(EvidenceAwareSection):
    """Shows composite risk formula, top files by risk score, and rationale."""

    config = SectionConfig(
        name="sampling_rationale",
        title="Sampling Rationale",
        description="What was analyzed and why: composite risk formula and top targets.",
        priority=97,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        # Fetch composite risk targets from existing query
        targets = self._safe_fetch(fetcher, "sampling_targets", run_pk)

        registry = self._evidence_registry
        summary = registry.summary() if registry else {}

        # Build rationale entries from targets
        rationale_items: list[dict[str, Any]] = []
        for row in targets:
            rationale_items.append({
                "file_path": row.get("relative_path", ""),
                "composite_score": row.get("composite_score", 0),
                "ccn_score": row.get("ccn_score", 0),
                "coupling_score": row.get("coupling_score", 0),
                "ownership_score": row.get("ownership_score", 0),
                "coverage_score": row.get("coverage_score", 0),
                "quality_score": row.get("quality_score", 0),
                "rationale": _build_rationale(row),
            })

        # Tool coverage
        evidence_categories = summary.get("evidence_by_category", {})
        tools_contributing = [
            cat for cat, count in evidence_categories.items() if count > 0
        ]

        return {
            "targets": rationale_items,
            "target_count": len(rationale_items),
            "formula": "composite = 0.30*complexity + 0.25*coupling + 0.20*ownership + 0.15*coverage + 0.10*quality",
            "tools_contributing": tools_contributing,
            "evidence_summary": summary,
            "has_data": len(rationale_items) > 0,
        }

    def get_template_name(self) -> str:
        return "sampling_rationale.html.j2"

    def get_fallback_data(self) -> dict[str, Any]:
        return {
            "targets": [],
            "target_count": 0,
            "formula": "",
            "tools_contributing": [],
            "evidence_summary": {},
            "has_data": False,
        }


def _build_rationale(row: dict[str, Any]) -> str:
    """Build a human-readable rationale string for a sampling target."""
    reasons: list[str] = []

    ccn = row.get("ccn_score", 0)
    coupling = row.get("coupling_score", 0)
    ownership = row.get("ownership_score", 0)
    coverage = row.get("coverage_score", 0)

    if ccn > 0.7:
        reasons.append("high complexity")
    if coupling > 0.7:
        reasons.append("high coupling")
    if ownership > 0.7:
        reasons.append("knowledge risk")
    if coverage > 0.7:
        reasons.append("low test coverage")

    if not reasons:
        reasons.append("moderate multi-dimensional risk")

    return "Selected due to " + ", ".join(reasons)
