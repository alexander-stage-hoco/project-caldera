"""Evidence registry builder — orchestrates collector, generator, aggregator.

Usage::

    builder = EvidenceRegistryBuilder()
    registry = builder.build(fetcher, run_pk)
"""

from __future__ import annotations

import warnings

from ..data_fetcher import DataFetcher
from .claim_generator import ClaimGenerator
from .collector import EvidenceCollector
from .entities import EvidenceRegistry
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
