"""Evidence collector — SQL-driven extraction from existing marts.

Each ``collect_*`` method runs a query against an existing dbt mart and maps
rows to ``EvidenceItem`` instances.  If the underlying table does not exist
(because the tool was not run), the method silently returns an empty list.
"""

from __future__ import annotations

import warnings
from typing import Any

from ..data_fetcher import DataFetcher
from .entities import EVIDENCE_CATEGORIES, EvidenceCategory, EvidenceItem

# Category abbreviations for evidence IDs
_CATEGORY_ABBR: dict[EvidenceCategory, str] = {
    "complexity": "CCN",
    "security": "SEC",
    "coupling": "COUP",
    "coverage": "COV",
    "ownership": "OWN",
    "quality": "QUAL",
}


class EvidenceCollector:
    """Collects evidence items from SQL queries on existing marts."""

    def collect(
        self,
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[EvidenceItem]:
        """Run all evidence source queries and return combined results."""
        items: list[EvidenceItem] = []

        collectors = [
            self._collect_complexity,
            self._collect_security,
            self._collect_coupling,
            self._collect_coverage,
            self._collect_ownership,
            self._collect_quality,
        ]

        for collector_fn in collectors:
            try:
                items.extend(collector_fn(fetcher, run_pk))
            except Exception as exc:
                warnings.warn(
                    f"[EvidenceCollector] {collector_fn.__name__} failed: {exc}",
                    stacklevel=2,
                )

        return items

    # -- Per-category collectors -------------------------------------------

    def _collect_complexity(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_complexity", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            items.append(
                EvidenceItem(
                    evidence_id=_make_id("CCN", i),
                    evidence_type="file_complexity",
                    category="complexity",
                    location=row.get("relative_path", ""),
                    excerpt=f"max_ccn={row.get('max_ccn', 0)}, "
                    f"functions={row.get('function_count', 0)}, "
                    f"loc={row.get('loc_total', 0)}",
                    observation=f"File has cyclomatic complexity of "
                    f"{row.get('max_ccn', 0)} (threshold: 15)",
                    why_it_matters="High CCN increases defect probability "
                    "and makes the file harder to test and modify safely.",
                    tool_source="lizard",
                    run_pk=row.get("tool_run_pk", run_pk),
                )
            )
        return items

    def _collect_security(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_security", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            finding_type = row.get("finding_type", "cve")
            if finding_type == "secret":
                items.append(
                    EvidenceItem(
                        evidence_id=_make_id("SEC", i),
                        evidence_type="secret_detection",
                        category="security",
                        location=row.get("location", ""),
                        excerpt=f"rule={row.get('finding_id', '')}",
                        observation=f"Secret detected: "
                        f"{row.get('description', 'unknown')}",
                        why_it_matters="Exposed secrets enable unauthorized "
                        "access to systems and data.",
                        tool_source="gitleaks",
                        run_pk=row.get("tool_run_pk", run_pk),
                        confidence="high",
                    )
                )
            else:
                severity = row.get("severity", "HIGH")
                items.append(
                    EvidenceItem(
                        evidence_id=_make_id("SEC", i),
                        evidence_type="vulnerability",
                        category="security",
                        location=row.get("location", ""),
                        excerpt=f"{row.get('finding_id', '')} "
                        f"({severity}) in {row.get('package_name', '?')} "
                        f"{row.get('installed_version', '?')}",
                        observation=f"{severity} vulnerability: "
                        f"{row.get('description', 'N/A')}",
                        why_it_matters="Known vulnerabilities are actively "
                        "exploited; unpatched dependencies increase "
                        "attack surface.",
                        tool_source="trivy",
                        run_pk=row.get("tool_run_pk", run_pk),
                        confidence="high",
                    )
                )
        return items

    def _collect_coupling(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_coupling", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            items.append(
                EvidenceItem(
                    evidence_id=_make_id("COUP", i),
                    evidence_type="symbol_coupling",
                    category="coupling",
                    location=row.get("relative_path", ""),
                    excerpt=f"{row.get('symbol_name', '')} "
                    f"({row.get('symbol_type', '')}): "
                    f"fan_in={row.get('fan_in', 0)}, "
                    f"fan_out={row.get('fan_out', 0)}, "
                    f"coupling={row.get('total_coupling', 0)}",
                    observation=f"Symbol has {row.get('coupling_risk', '')} "
                    f"coupling risk with pattern "
                    f"'{row.get('coupling_pattern', '')}'",
                    why_it_matters="High coupling amplifies change cost: "
                    "modifications propagate across the codebase.",
                    tool_source="symbol-scanner",
                    run_pk=row.get("tool_run_pk", run_pk),
                )
            )
        return items

    def _collect_coverage(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_coverage", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            coverage = row.get("line_coverage_pct", 0) or 0
            items.append(
                EvidenceItem(
                    evidence_id=_make_id("COV", i),
                    evidence_type="coverage_gap",
                    category="coverage",
                    location=row.get("relative_path", ""),
                    excerpt=f"coverage={coverage:.0f}%, "
                    f"max_ccn={row.get('max_ccn', 0)}, "
                    f"loc={row.get('loc_total', 0)}",
                    observation=f"File has only {coverage:.0f}% line coverage "
                    f"with complexity of {row.get('max_ccn', 0)}",
                    why_it_matters="Complex files with low coverage carry "
                    "high regression risk — defects are likely latent.",
                    tool_source="coverage-ingest",
                    run_pk=row.get("tool_run_pk", run_pk),
                )
            )
        return items

    def _collect_ownership(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_ownership", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            items.append(
                EvidenceItem(
                    evidence_id=_make_id("OWN", i),
                    evidence_type="knowledge_risk",
                    category="ownership",
                    location=row.get("relative_path", ""),
                    excerpt=f"authors={row.get('unique_authors', 0)}, "
                    f"top_author={row.get('top_author', '?')} "
                    f"({row.get('top_author_pct', 0):.0f}%), "
                    f"lines={row.get('total_lines', 0)}",
                    observation=f"File has {row.get('risk_level', '')} "
                    f"knowledge risk — "
                    f"{row.get('unique_authors', 0)} author(s)",
                    why_it_matters="Single-author files create bus factor "
                    "risk; knowledge silos slow onboarding and increase "
                    "incident response time.",
                    tool_source="git-blame-scanner",
                    run_pk=row.get("tool_run_pk", run_pk),
                )
            )
        return items

    def _collect_quality(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_quality", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            smell_d = row.get("smell_density_per_kloc", 0) or 0
            issue_d = row.get("issue_density_per_kloc", 0) or 0
            items.append(
                EvidenceItem(
                    evidence_id=_make_id("QUAL", i),
                    evidence_type="quality_issue",
                    category="quality",
                    location=row.get("relative_path", ""),
                    excerpt=f"smells={row.get('smell_count', 0)}, "
                    f"issues={row.get('issue_count', 0)}, "
                    f"loc={row.get('loc_total', 0)}",
                    observation=f"File has {smell_d:.0f} smells/KLOC and "
                    f"{issue_d:.0f} issues/KLOC",
                    why_it_matters="High issue density correlates with "
                    "elevated defect rates and higher maintenance cost.",
                    tool_source="semgrep",
                    run_pk=row.get("tool_run_pk", run_pk),
                )
            )
        return items

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _safe_query(
        fetcher: DataFetcher,
        query_name: str,
        run_pk: int,
    ) -> list[dict[str, Any]]:
        """Execute a query, returning empty list on failure."""
        try:
            return fetcher.fetch(query_name, run_pk)
        except Exception as exc:
            warnings.warn(
                f"[EvidenceCollector] Query '{query_name}' failed: {exc}",
                stacklevel=2,
            )
            return []


def _make_id(abbr: str, seq: int) -> str:
    """Generate an evidence ID like ``E-CCN-001``."""
    return f"E-{abbr}-{seq:03d}"
