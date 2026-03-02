"""Evidence registry builder — orchestrates collector, generator, aggregator.

Usage::

    builder = EvidenceRegistryBuilder()
    registry = builder.build(fetcher, run_pk)

    # Optionally persist to DuckDB:
    builder.persist(registry, conn, collection_run_id)
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from ..data_fetcher import DataFetcher
from .action_generator import ActionGenerator
from .claim_generator import ClaimGenerator
from .collector import EvidenceCollector, check_warning_budget
from .entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)
from .risk_aggregator import RiskAggregator

if TYPE_CHECKING:
    from ..narrative.enricher import NarrativeEnricher


class EvidenceRegistryBuilder:
    """Orchestrates the full evidence → claim → risk pipeline."""

    def __init__(
        self,
        collector: EvidenceCollector | None = None,
        claim_generator: ClaimGenerator | None = None,
        risk_aggregator: RiskAggregator | None = None,
        action_generator: ActionGenerator | None = None,
        enricher: NarrativeEnricher | None = None,
    ) -> None:
        self._collector = collector or EvidenceCollector()
        self._claim_generator = claim_generator or ClaimGenerator(enricher=enricher)
        self._risk_aggregator = risk_aggregator or RiskAggregator()
        self._action_generator = action_generator or ActionGenerator()

    def build(self, fetcher: DataFetcher, run_pk: int) -> EvidenceRegistry:
        """Run the full pipeline and return a populated registry."""
        total_warnings = 0
        warning_details: dict[str, object] = {}
        try:
            collection_result = self._collector.collect_with_warnings(fetcher, run_pk)
            evidence = collection_result.items
            counts = collection_result.warning_counts()
            total_warnings = sum(counts.values())

            # Check warning budget and log violations
            budget = check_warning_budget(collection_result)
            budgets = {v.category: v.limit for v in budget.violations}
            # Include all budget thresholds (not just violations)
            from .collector import _load_warning_budget
            all_budgets = _load_warning_budget()

            warning_details = {
                "total": total_warnings,
                "budget_passed": budget.passed,
                "counts": dict(counts),
                "budgets": {k: v for k, v in all_budgets.items()},
                "warnings": [
                    {
                        "category": w.category,
                        "source": w.source,
                        "message": w.message,
                    }
                    for w in collection_result.warnings
                ],
            }

            if not budget.passed:
                for v in budget.violations:
                    warnings.warn(
                        f"[EvidenceRegistryBuilder] Warning budget exceeded: "
                        f"{v.category} has {v.actual} warnings (limit: {v.limit})",
                        stacklevel=2,
                    )
        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Evidence collection failed: {exc}",
                stacklevel=2,
            )
            return EvidenceRegistry()

        try:
            claims = self._claim_generator.generate(evidence, fetcher, run_pk)
        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Claim generation failed: {exc}",
                stacklevel=2,
            )
            claims = []

        try:
            risks = self._risk_aggregator.aggregate(claims, evidence)
        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Risk aggregation failed: {exc}",
                stacklevel=2,
            )
            risks = []

        try:
            risks = self._action_generator.enrich(risks)
        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Action enrichment failed: {exc}",
                stacklevel=2,
            )

        return EvidenceRegistry(
            evidence=evidence,
            claims=claims,
            risks=risks,
            warning_count=total_warnings,
            warning_details=warning_details,
        )

    @staticmethod
    def persist(
        registry: EvidenceRegistry,
        conn: Any,
        collection_run_id: str,
    ) -> None:
        """Persist evidence, claims, risks, and warnings to DuckDB landing zone tables.

        Idempotent: deletes existing data for the collection_run_id first.
        """
        try:
            # Clear previous data for this run
            for table in ("lz_evidence", "lz_claims", "lz_risks", "lz_warnings"):
                conn.execute(
                    f"DELETE FROM {table} WHERE collection_run_id = ?",
                    [collection_run_id],
                )

            # Persist evidence items
            if registry.evidence:
                conn.executemany(
                    """
                    INSERT INTO lz_evidence (
                        collection_run_id, evidence_id, evidence_type, category,
                        location, excerpt, observation, why_it_matters,
                        tool_source, run_pk, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            collection_run_id,
                            e.evidence_id,
                            e.evidence_type,
                            e.category,
                            e.location,
                            e.excerpt,
                            e.observation,
                            e.why_it_matters,
                            e.tool_source,
                            e.run_pk,
                            e.confidence,
                        )
                        for e in registry.evidence
                    ],
                )

            # Persist claims
            if registry.claims:
                conn.executemany(
                    """
                    INSERT INTO lz_claims (
                        collection_run_id, claim_id, category, statement,
                        evidence_ids, implication, confidence,
                        triggered_by, severity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            collection_run_id,
                            c.claim_id,
                            c.category,
                            c.statement,
                            ",".join(c.evidence_ids),
                            c.implication,
                            c.confidence,
                            c.triggered_by,
                            c.severity,
                        )
                        for c in registry.claims
                    ],
                )

            # Persist risks
            if registry.risks:
                conn.executemany(
                    """
                    INSERT INTO lz_risks (
                        collection_run_id, risk_id, description,
                        technical_cause, claim_ids, manifests_in,
                        triggered_by, severity,
                        owner, action, sla_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            collection_run_id,
                            r.risk_id,
                            r.description,
                            r.technical_cause,
                            ",".join(r.claim_ids),
                            ",".join(r.manifests_in),
                            r.triggered_by,
                            r.severity,
                            r.owner,
                            r.action,
                            r.sla_date,
                            r.status,
                        )
                        for r in registry.risks
                    ],
                )

            # Persist individual warnings
            warning_list = registry.warning_details.get("warnings", [])
            if warning_list:
                conn.executemany(
                    """
                    INSERT INTO lz_warnings (
                        collection_run_id, category, source, message
                    ) VALUES (?, ?, ?, ?)
                    """,
                    [
                        (
                            collection_run_id,
                            w["category"],
                            w["source"],
                            w["message"],
                        )
                        for w in warning_list
                    ],
                )

        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Persistence failed: {exc}",
                stacklevel=2,
            )
