"""Evidence collector — SQL-driven extraction from existing marts.

Each ``collect_*`` method runs a query against an existing dbt mart and maps
rows to ``EvidenceItem`` instances.  If the underlying table does not exist
(because the tool was not run), the method silently returns an empty list.

Warnings are classified into categories for budgeting:
- ``expected_missing``: tool was not run or is not applicable
- ``regression``: query that previously worked now fails
- ``degraded``: partial results returned
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

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

WarningCategory = Literal["expected_missing", "regression", "degraded"]


@dataclass
class CollectorWarning:
    """A classified warning emitted during evidence collection."""

    category: WarningCategory
    source: str
    message: str


@dataclass
class CollectionResult:
    """Result of evidence collection with classified warnings."""

    items: list[EvidenceItem] = field(default_factory=list)
    warnings: list[CollectorWarning] = field(default_factory=list)

    def warning_counts(self) -> dict[WarningCategory, int]:
        counts: dict[WarningCategory, int] = {
            "expected_missing": 0,
            "regression": 0,
            "degraded": 0,
        }
        for w in self.warnings:
            counts[w.category] = counts.get(w.category, 0) + 1
        return counts


@dataclass(frozen=True)
class BudgetViolation:
    """A single budget threshold exceeded."""

    category: WarningCategory
    actual: int
    limit: int


@dataclass
class BudgetResult:
    """Result of checking warning counts against the budget."""

    passed: bool
    violations: list[BudgetViolation] = field(default_factory=list)


def _load_warning_budget() -> dict[WarningCategory, int]:
    """Load warning budgets from ``warning_budget.yml``."""
    budget_path = Path(__file__).resolve().parent.parent / "warning_budget.yml"
    if not budget_path.exists():
        return {"expected_missing": 10, "regression": 0, "degraded": 3}
    with budget_path.open() as f:
        data = yaml.safe_load(f)
    budgets = data.get("budgets", {})
    return {
        "expected_missing": budgets.get("expected_missing", 10),
        "regression": budgets.get("regression", 0),
        "degraded": budgets.get("degraded", 3),
    }


def check_warning_budget(result: CollectionResult) -> BudgetResult:
    """Compare warning counts against the configured budget thresholds."""
    budgets = _load_warning_budget()
    counts = result.warning_counts()
    violations: list[BudgetViolation] = []
    for category, limit in budgets.items():
        actual = counts.get(category, 0)
        if actual > limit:
            violations.append(BudgetViolation(category=category, actual=actual, limit=limit))
    return BudgetResult(passed=len(violations) == 0, violations=violations)


# Known queries that map to optional tools — missing data is expected
_OPTIONAL_QUERIES: frozenset[str] = frozenset({
    "evidence_coupling",    # requires symbol-scanner (not always run)
    "evidence_coverage",    # requires coverage-ingest (not always run)
    "evidence_ownership",   # requires git-blame-scanner (not always run)
})


class EvidenceCollector:
    """Collects evidence items from SQL queries on existing marts."""

    def collect(
        self,
        fetcher: DataFetcher,
        run_pk: int,
    ) -> list[EvidenceItem]:
        """Run all evidence source queries and return combined results."""
        result = self.collect_with_warnings(fetcher, run_pk)
        return result.items

    def collect_with_warnings(
        self,
        fetcher: DataFetcher,
        run_pk: int,
    ) -> CollectionResult:
        """Run all evidence source queries and return items + classified warnings."""
        result = CollectionResult()

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
                result.items.extend(collector_fn(fetcher, run_pk))
            except Exception as exc:
                source = collector_fn.__name__
                # Classify warning based on query type
                query_name = source.replace("_collect_", "evidence_")
                if query_name in _OPTIONAL_QUERIES:
                    category: WarningCategory = "expected_missing"
                else:
                    category = "regression"
                result.warnings.append(CollectorWarning(
                    category=category,
                    source=source,
                    message=str(exc),
                ))
                warnings.warn(
                    f"[EvidenceCollector] {source} failed ({category}): {exc}",
                    stacklevel=2,
                )

        return result

    # -- Per-category collectors -------------------------------------------

    def _collect_complexity(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_complexity", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            _safe_append(items, lambda r=row: EvidenceItem(
                evidence_id=_make_id("CCN", i),
                evidence_type="file_complexity",
                category="complexity",
                location=r.get("relative_path", ""),
                excerpt=f"complexity_max={r.get('complexity_max', 0)}, "
                f"functions={r.get('function_count', 0)}, "
                f"loc={r.get('loc_total', 0)}",
                observation=f"File has cyclomatic complexity of "
                f"{r.get('complexity_max', 0)} (threshold: 15)",
                why_it_matters="High CCN increases defect probability "
                "and makes the file harder to test and modify safely.",
                tool_source="lizard",
                run_pk=r.get("tool_run_pk", run_pk),
            ), i, "complexity")
        return items

    def _collect_security(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_security", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            finding_type = row.get("finding_type", "cve")
            if finding_type == "secret":
                _safe_append(items, lambda r=row: EvidenceItem(
                    evidence_id=_make_id("SEC", i),
                    evidence_type="secret_detection",
                    category="security",
                    location=r.get("location", ""),
                    excerpt=f"rule={r.get('finding_id', '')}",
                    observation=f"Secret detected: "
                    f"{r.get('description', 'unknown')}",
                    why_it_matters="Exposed secrets enable unauthorized "
                    "access to systems and data.",
                    tool_source="gitleaks",
                    run_pk=r.get("tool_run_pk", run_pk),
                    confidence="high",
                ), i, "security")
            else:
                severity = row.get("severity", "HIGH")
                _safe_append(items, lambda r=row, sev=severity: EvidenceItem(
                    evidence_id=_make_id("SEC", i),
                    evidence_type="vulnerability",
                    category="security",
                    location=r.get("location", ""),
                    excerpt=f"{r.get('finding_id', '')} "
                    f"({sev}) in {r.get('package_name', '?')} "
                    f"{r.get('installed_version', '?')}",
                    observation=f"{sev} vulnerability: "
                    f"{r.get('description', 'N/A')}",
                    why_it_matters="Known vulnerabilities are actively "
                    "exploited; unpatched dependencies increase "
                    "attack surface.",
                    tool_source="trivy",
                    run_pk=r.get("tool_run_pk", run_pk),
                    confidence="high",
                ), i, "security")
        return items

    def _collect_coupling(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_coupling", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            _safe_append(items, lambda r=row: EvidenceItem(
                evidence_id=_make_id("COUP", i),
                evidence_type="symbol_coupling",
                category="coupling",
                location=r.get("relative_path", ""),
                excerpt=f"{r.get('symbol_name', '')} "
                f"({r.get('symbol_type', '')}): "
                f"fan_in={r.get('fan_in', 0)}, "
                f"fan_out={r.get('fan_out', 0)}, "
                f"coupling={r.get('total_coupling', 0)}",
                observation=f"Symbol has {r.get('coupling_risk', '')} "
                f"coupling risk with pattern "
                f"'{r.get('coupling_pattern', '')}'",
                why_it_matters="High coupling amplifies change cost: "
                "modifications propagate across the codebase.",
                tool_source="symbol-scanner",
                run_pk=r.get("tool_run_pk", run_pk),
            ), i, "coupling")
        return items

    def _collect_coverage(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_coverage", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            coverage = row.get("coverage_line_pct", 0) or 0
            _safe_append(items, lambda r=row, cov=coverage: EvidenceItem(
                evidence_id=_make_id("COV", i),
                evidence_type="coverage_gap",
                category="coverage",
                location=r.get("relative_path", ""),
                excerpt=f"coverage={cov:.0f}%, "
                f"complexity_max={r.get('complexity_max', 0)}, "
                f"loc={r.get('loc_total', 0)}",
                observation=f"File has only {cov:.0f}% line coverage "
                f"with complexity of {r.get('complexity_max', 0)}",
                why_it_matters="Complex files with low coverage carry "
                "high regression risk — defects are likely latent.",
                tool_source="coverage-ingest",
                run_pk=r.get("tool_run_pk", run_pk),
            ), i, "coverage")
        return items

    def _collect_ownership(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_ownership", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            _safe_append(items, lambda r=row: EvidenceItem(
                evidence_id=_make_id("OWN", i),
                evidence_type="knowledge_risk",
                category="ownership",
                location=r.get("relative_path", ""),
                excerpt=f"authors={r.get('unique_authors', 0)}, "
                f"top_author={r.get('top_author', '?')} "
                f"({r.get('top_author_pct', 0):.0f}%), "
                f"lines={r.get('total_lines', 0)}",
                observation=f"File has {r.get('risk_level', '')} "
                f"knowledge risk — "
                f"{r.get('unique_authors', 0)} author(s)",
                why_it_matters="Single-author files create bus factor "
                "risk; knowledge silos slow onboarding and increase "
                "incident response time.",
                tool_source="git-blame-scanner",
                run_pk=r.get("tool_run_pk", run_pk),
            ), i, "ownership")
        return items

    def _collect_quality(
        self, fetcher: DataFetcher, run_pk: int
    ) -> list[EvidenceItem]:
        rows = self._safe_query(fetcher, "evidence_quality", run_pk)
        items: list[EvidenceItem] = []
        for i, row in enumerate(rows, start=1):
            smell_d = row.get("smell_density_per_kloc", 0) or 0
            issue_d = row.get("issue_density_per_kloc", 0) or 0
            _safe_append(items, lambda r=row, sd=smell_d, id_=issue_d: EvidenceItem(
                evidence_id=_make_id("QUAL", i),
                evidence_type="quality_issue",
                category="quality",
                location=r.get("relative_path", ""),
                excerpt=f"smells={r.get('semgrep_smell_count', 0)}, "
                f"issues={r.get('devskim_issue_count', 0)}, "
                f"loc={r.get('loc_total', 0)}",
                observation=f"File has {sd:.0f} smells/KLOC and "
                f"{id_:.0f} issues/KLOC",
                why_it_matters="High issue density correlates with "
                "elevated defect rates and higher maintenance cost.",
                tool_source="semgrep",
                run_pk=r.get("tool_run_pk", run_pk),
            ), i, "quality")
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
            category = "expected_missing" if query_name in _OPTIONAL_QUERIES else "regression"
            warnings.warn(
                f"[EvidenceCollector] Query '{query_name}' failed ({category}): {exc}",
                stacklevel=2,
            )
            return []


def _make_id(abbr: str, seq: int) -> str:
    """Generate an evidence ID like ``E-CCN-001``."""
    return f"E-{abbr}-{seq:03d}"


def _safe_append(
    items: list[EvidenceItem],
    item_fn: Any,  # Callable[[], EvidenceItem]
    row_idx: int,
    category: str,
) -> None:
    """Append an EvidenceItem, warning and skipping on failure."""
    try:
        items.append(item_fn())
    except Exception as exc:
        warnings.warn(
            f"[EvidenceCollector] Skipping {category} row {row_idx}: {exc}",
            stacklevel=3,
        )
