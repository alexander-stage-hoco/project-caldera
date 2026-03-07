"""Evidence pack section — reference index of all collected evidence items."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from .base import EvidenceAwareSection, SectionConfig


class EvidencePackSection(EvidenceAwareSection):
    """Renders an evidence index table grouped by category (top 50 each)."""

    config = SectionConfig(
        name="evidence_pack",
        title="Evidence Pack",
        description="Reference material: all auditable evidence items grouped by category.",
        priority=98,
    )

    MAX_PER_CATEGORY = 50

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        registry = self._evidence_registry
        if not registry:
            return self.get_fallback_data()

        summary = registry.summary()
        categories_data: list[dict[str, Any]] = []

        from ..evidence.entities import EVIDENCE_CATEGORIES
        for cat in EVIDENCE_CATEGORIES:
            items = registry.evidence_by_category(cat)
            total = len(items)
            displayed = items[: self.MAX_PER_CATEGORY]

            # Look up quality score for this category from evaluations
            cat_eval = registry.evaluation_for(f"CAT-{cat.upper()}")
            category_quality_score = cat_eval.score if cat_eval else None

            categories_data.append({
                "category": cat,
                "total_count": total,
                "displayed_count": len(displayed),
                "truncated": total > self.MAX_PER_CATEGORY,
                "category_quality_score": category_quality_score,
                "evidence_items": [
                    {
                        "evidence_id": e.evidence_id,
                        "evidence_type": e.evidence_type,
                        "location": e.location,
                        "excerpt": e.excerpt,
                        "observation": e.observation,
                        "why_it_matters": e.why_it_matters,
                        "tool_source": e.tool_source,
                        "confidence": e.confidence,
                    }
                    for e in displayed
                ],
            })

        return {
            "categories": categories_data,
            "summary": summary,
            "total_evidence": summary["total_evidence"],
            "has_data": summary["total_evidence"] > 0,
        }

    def get_template_name(self) -> str:
        return "evidence_pack.html.j2"

    def get_fallback_data(self) -> dict[str, Any]:
        return {
            "categories": [],
            "summary": {"total_evidence": 0, "total_claims": 0, "total_risks": 0},
            "total_evidence": 0,
            "has_data": False,
        }
