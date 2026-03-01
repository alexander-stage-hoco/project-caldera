"""Evidence registry builder — orchestrates collector, generator, aggregator.

Usage::

    builder = EvidenceRegistryBuilder()
    registry = builder.build(fetcher, run_pk)

    # Optionally persist to DuckDB:
    builder.persist(registry, conn, collection_run_id)
"""

from __future__ import annotations

import warnings
from typing import Any

from ..data_fetcher import DataFetcher
from .claim_generator import ClaimGenerator
from .collector import EvidenceCollector
from .entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)
from .risk_aggregator import RiskAggregator


class EvidenceRegistryBuilder:
    """Orchestrates the full evidence → claim → risk pipeline."""

    def __init__(
        self,
        collector: EvidenceCollector | None = None,
        claim_generator: ClaimGenerator | None = None,
        risk_aggregator: RiskAggregator | None = None,
    ) -> None:
        self._collector = collector or EvidenceCollector()
        self._claim_generator = claim_generator or ClaimGenerator()
        self._risk_aggregator = risk_aggregator or RiskAggregator()

    def build(self, fetcher: DataFetcher, run_pk: int) -> EvidenceRegistry:
        """Run the full pipeline and return a populated registry."""
        try:
            evidence = self._collector.collect(fetcher, run_pk)
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

        return EvidenceRegistry(
            evidence=evidence,
            claims=claims,
            risks=risks,
        )

    @staticmethod
    def persist(
        registry: EvidenceRegistry,
        conn: Any,
        collection_run_id: str,
    ) -> None:
        """Persist evidence, claims, and risks to DuckDB landing zone tables.

        Idempotent: deletes existing data for the collection_run_id first.
        """
        try:
            # Clear previous data for this run
            for table in ("lz_evidence", "lz_claims", "lz_risks"):
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
                        triggered_by, severity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                        )
                        for r in registry.risks
                    ],
                )

        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Persistence failed: {exc}",
                stacklevel=2,
            )
