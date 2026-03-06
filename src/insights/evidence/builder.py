"""Evidence registry builder — orchestrates collector, generator, aggregator.

Usage::

    builder = EvidenceRegistryBuilder()
    registry = builder.build(fetcher, run_pk)

    # Optionally persist to DuckDB:
    builder.persist(registry, conn, collection_run_id)

    # With parameter set:
    from insights.config import ConfigLoader
    ps = ConfigLoader.load_parameter_set("pe_due_diligence")
    reg = ConfigLoader.load_categories()
    builder = EvidenceRegistryBuilder(parameter_set=ps, category_registry=reg)
    registry = builder.build(fetcher, run_pk)
"""

from __future__ import annotations

import json
import uuid
import warnings
from typing import TYPE_CHECKING, Any

from ..data_fetcher import DataFetcher
from .action_generator import ActionGenerator
from .claim_generator import ClaimGenerator
from .collector import EvidenceCollector, check_warning_budget
from .entities import (
    CategoryRegistry,
    EvidenceItem,
    EvidenceRegistry,
    EvidenceSetMetadata,
    ExecutionRisk,
    ParameterSet,
    TechnicalClaim,
)
from .param_persistence import parameter_set_to_records, persist_params
from .risk_aggregator import RiskAggregator

if TYPE_CHECKING:
    from ..narrative.enricher import NarrativeEnricher


class EvidenceRegistryBuilder:
    """Orchestrates the full evidence → claim → risk pipeline.

    When ``parameter_set`` and/or ``category_registry`` are provided, the
    builder uses parameterized, registry-driven collection. Otherwise it
    falls back to the legacy hardcoded path for full backward compatibility.
    """

    def __init__(
        self,
        collector: EvidenceCollector | None = None,
        claim_generator: ClaimGenerator | None = None,
        risk_aggregator: RiskAggregator | None = None,
        action_generator: ActionGenerator | None = None,
        enricher: NarrativeEnricher | None = None,
        parameter_set: ParameterSet | None = None,
        category_registry: CategoryRegistry | None = None,
    ) -> None:
        self._parameter_set = parameter_set
        self._category_registry = category_registry

        if collector is not None:
            self._collector = collector
        elif parameter_set is not None or category_registry is not None:
            self._collector = EvidenceCollector(
                category_registry=category_registry,
                parameter_set=parameter_set,
            )
        else:
            self._collector = EvidenceCollector()

        if claim_generator is not None:
            self._claim_generator = claim_generator
        else:
            claim_params = parameter_set.claim_params if parameter_set else None
            self._claim_generator = ClaimGenerator(
                enricher=enricher,
                claim_params=claim_params,
            )

        if risk_aggregator is not None:
            self._risk_aggregator = risk_aggregator
        else:
            risk_params = parameter_set.risk_params if parameter_set else None
            self._risk_aggregator = RiskAggregator(risk_params=risk_params)

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
        parameter_set: ParameterSet | None = None,
    ) -> str | None:
        """Persist evidence, claims, risks, and warnings to DuckDB landing zone tables.

        When *parameter_set* is provided, auto-creates an ``lz_evidence_sets``
        row with structured parameter storage and links all evidence/claims/risks
        to the new evidence set.

        Returns the ``evidence_set_id`` if created, ``None`` otherwise.
        Idempotent: deletes existing data for the collection_run_id first.
        """
        try:
            # Clear previous data for this run
            for table in ("lz_evidence", "lz_claims", "lz_risks", "lz_warnings"):
                conn.execute(
                    f"DELETE FROM {table} WHERE collection_run_id = ?",
                    [collection_run_id],
                )

            # Auto-create evidence set when parameter_set is provided
            evidence_set_id: str | None = None
            if parameter_set is not None:
                evidence_set_id = str(uuid.uuid4())
                has_set_table = _table_has_column(conn, "lz_evidence_sets", "evidence_set_id")
                if has_set_table:
                    conn.execute(
                        """
                        INSERT INTO lz_evidence_sets (
                            evidence_set_id, collection_run_id, parameter_set_name,
                            parameter_set_json, status, total_items
                        ) VALUES (?, ?, ?, '{}', 'open', ?)
                        """,
                        [
                            evidence_set_id,
                            collection_run_id,
                            parameter_set.name,
                            len(registry.evidence),
                        ],
                    )
                    # Persist structured params
                    has_param_tables = _table_has_column(
                        conn, "lz_evidence_query_params", "evidence_set_id",
                    )
                    if has_param_tables:
                        qr, cr, rr = parameter_set_to_records(
                            parameter_set, evidence_set_id,
                        )
                        persist_params(conn, evidence_set_id, qr, cr, rr)

            # Persist evidence items
            if registry.evidence:
                # Check if metadata_json column exists (graceful upgrade)
                has_metadata = _table_has_column(conn, "lz_evidence", "metadata_json")
                if has_metadata:
                    conn.executemany(
                        """
                        INSERT INTO lz_evidence (
                            collection_run_id, evidence_id, evidence_type, category,
                            location, excerpt, observation, why_it_matters,
                            tool_source, run_pk, confidence, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                                json.dumps(e.metadata) if e.metadata else None,
                            )
                            for e in registry.evidence
                        ],
                    )
                else:
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

            # Link evidence/claims/risks to the evidence set
            if evidence_set_id is not None:
                for table in ("lz_evidence", "lz_claims", "lz_risks"):
                    has_col = _table_has_column(conn, table, "evidence_set_id")
                    if has_col:
                        conn.execute(
                            f"UPDATE {table} SET evidence_set_id = ? "
                            f"WHERE collection_run_id = ? AND evidence_set_id IS NULL",
                            [evidence_set_id, collection_run_id],
                        )

            return evidence_set_id

        except Exception as exc:
            warnings.warn(
                f"[EvidenceRegistryBuilder] Persistence failed: {exc}",
                stacklevel=2,
            )
            return None


def _table_has_column(conn: Any, table: str, column: str) -> bool:
    """Check if a column exists in a DuckDB table (graceful schema check)."""
    try:
        result = conn.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = ?",
            [table, column],
        ).fetchone()
        return result[0] > 0 if result else False
    except Exception:
        return False
