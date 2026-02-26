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

        # Fetch codebase summary stats
        summary_rows = self._safe_fetch(fetcher, "sampling_summary", run_pk)
        codebase_summary = summary_rows[0] if summary_rows else {
            "total_files": 0, "total_loc": 0,
            "eligible_files": 0, "eligible_loc": 0,
        }

        registry = self._evidence_registry
        evidence_summary = registry.summary() if registry else {}

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
                "total_coupling": row.get("total_coupling"),
                "unique_authors": row.get("unique_authors"),
                "top_author_pct": row.get("top_author_pct"),
                "churn_30d": row.get("churn_30d"),
                "loc_total": row.get("loc_total", 0),
                "rationale": _build_rationale(row),
            })

        # Compute risk driver breakdown
        risk_drivers = _compute_risk_drivers(rationale_items)

        # Tool coverage
        evidence_categories = evidence_summary.get("evidence_by_category", {})
        tools_contributing = [
            cat for cat, count in evidence_categories.items() if count > 0
        ]

        # Compute sampling coverage
        sampled_loc = sum(t.get("loc_total", 0) for t in rationale_items)
        total_loc = codebase_summary.get("total_loc", 0)
        sampling_coverage = {
            "total_files": codebase_summary.get("total_files", 0),
            "total_loc": total_loc,
            "eligible_files": codebase_summary.get("eligible_files", 0),
            "eligible_loc": codebase_summary.get("eligible_loc", 0),
            "sampled_files": len(rationale_items),
            "sampled_loc": sampled_loc,
            "sampled_pct": round(
                sampled_loc / total_loc * 100, 1
            ) if total_loc > 0 else 0,
            "sampled_kloc": round(sampled_loc / 1000, 1),
        }

        return {
            "targets": rationale_items,
            "target_count": len(rationale_items),
            "formula": "composite = 0.30*complexity + 0.25*coupling + 0.20*ownership + 0.15*coverage + 0.10*quality",
            "tools_contributing": tools_contributing,
            "evidence_summary": evidence_summary,
            "risk_drivers": risk_drivers,
            "sampling_coverage": sampling_coverage,
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
            "risk_drivers": {},
            "sampling_coverage": {},
            "has_data": False,
        }


def _build_rationale(row: dict[str, Any]) -> str:
    """Build a human-readable rationale string for a sampling target."""
    reasons: list[str] = []

    ccn = row.get("ccn_score", 0) or 0
    coupling = row.get("coupling_score", 0) or 0
    ownership = row.get("ownership_score", 0) or 0
    coverage = row.get("coverage_score", 0) or 0
    quality = row.get("quality_score", 0) or 0

    unique_authors = row.get("unique_authors")
    churn_30d = row.get("churn_30d")
    total_coupling = row.get("total_coupling")

    # Complexity + coverage combined signal
    if ccn > 0.7 and coverage > 0.7:
        reasons.append("complex + untested")
    elif ccn > 0.7:
        reasons.append("high complexity")

    # Coupling
    if total_coupling is not None and total_coupling > 15:
        reasons.append(f"high coupling (fan_out + fan_in = {int(total_coupling)})")
    elif coupling > 0.7:
        reasons.append("high coupling")

    # Ownership with specific context
    if unique_authors == 1 and ownership > 0.3:
        reasons.append("single-author knowledge silo")
    elif churn_30d is not None and churn_30d > 0 and ownership > 0.5:
        reasons.append("recently changed + concentrated ownership")
    elif ownership > 0.7:
        reasons.append("knowledge risk")

    if coverage > 0.7 and ccn <= 0.7:
        reasons.append("low test coverage")

    if quality > 0.7:
        reasons.append("high issue density")

    if not reasons:
        reasons.append("moderate multi-dimensional risk")

    return "Selected due to " + ", ".join(reasons)


def _compute_risk_drivers(targets: list[dict[str, Any]]) -> dict[str, int]:
    """Group targets by their dominant risk factor."""
    score_keys = [
        "ccn_score", "coupling_score", "ownership_score",
        "coverage_score", "quality_score",
    ]
    label_map = {
        "ccn_score": "complexity",
        "coupling_score": "coupling",
        "ownership_score": "ownership",
        "coverage_score": "coverage",
        "quality_score": "quality",
    }
    drivers: dict[str, int] = {
        "complexity": 0, "coupling": 0, "ownership": 0,
        "coverage": 0, "quality": 0,
    }
    for target in targets:
        dominant = max(score_keys, key=lambda k: target.get(k, 0) or 0)
        drivers[label_map[dominant]] += 1
    return drivers
