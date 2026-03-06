"""Evidence mappers — convert SQL rows to ``EvidenceItem`` instances.

Each mapper handles one evidence category. Extracted from the collector's
hardcoded ``_collect_*`` methods to allow registry-driven iteration.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any

from .entities import EvidenceItem


class EvidenceMapper(ABC):
    """Base class for evidence row-to-entity mappers."""

    category: str
    abbreviation: str

    @abstractmethod
    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        """Convert a SQL result row to an ``EvidenceItem``."""
        ...

    def _make_id(self, seq: int) -> str:
        return f"E-{self.abbreviation}-{seq:03d}"


class ComplexityMapper(EvidenceMapper):
    category = "complexity"
    abbreviation = "CCN"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        ccn = row.get("complexity_max", 0)
        func_count = row.get("function_count", 0)
        loc = row.get("loc_total", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="file_complexity",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"complexity_max={ccn}, "
            f"functions={func_count}, "
            f"loc={loc}",
            observation=f"File has cyclomatic complexity of "
            f"{ccn} (threshold: 15)",
            why_it_matters="High CCN increases defect probability "
            "and makes the file harder to test and modify safely.",
            tool_source="lizard",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"complexity_max": ccn, "function_count": func_count, "loc_total": loc},
        )


class SecurityMapper(EvidenceMapper):
    category = "security"
    abbreviation = "SEC"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        finding_type = row.get("finding_type", "cve")
        if finding_type == "secret":
            return EvidenceItem(
                evidence_id=self._make_id(seq),
                evidence_type="secret_detection",
                category=self.category,
                location=row.get("location", ""),
                excerpt=f"rule={row.get('finding_id', '')}",
                observation=f"Secret detected: "
                f"{row.get('description', 'unknown')}",
                why_it_matters="Exposed secrets enable unauthorized "
                "access to systems and data.",
                tool_source="gitleaks",
                run_pk=row.get("tool_run_pk", run_pk),
                confidence="high",
                metadata={"finding_type": "secret", "finding_id": row.get("finding_id", "")},
            )
        severity = row.get("severity", "HIGH")
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="vulnerability",
            category=self.category,
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
            metadata={
                "finding_type": "cve",
                "severity": severity,
                "finding_id": row.get("finding_id", ""),
                "package_name": row.get("package_name"),
            },
        )


class CouplingMapper(EvidenceMapper):
    category = "coupling"
    abbreviation = "COUP"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        fan_in = row.get("fan_in", 0)
        fan_out = row.get("fan_out", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="symbol_coupling",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"{row.get('symbol_name', '')} "
            f"({row.get('symbol_type', '')}): "
            f"fan_in={fan_in}, "
            f"fan_out={fan_out}, "
            f"coupling={row.get('total_coupling', 0)}",
            observation=f"Symbol has {row.get('coupling_risk', '')} "
            f"coupling risk with pattern "
            f"'{row.get('coupling_pattern', '')}'",
            why_it_matters="High coupling amplifies change cost: "
            "modifications propagate across the codebase.",
            tool_source="symbol-scanner",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"fan_in": fan_in, "fan_out": fan_out, "total_coupling": row.get("total_coupling", 0)},
        )


class CoverageMapper(EvidenceMapper):
    category = "coverage"
    abbreviation = "COV"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        coverage = row.get("coverage_line_pct", 0) or 0
        ccn = row.get("complexity_max", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="coverage_gap",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"coverage={coverage:.0f}%, "
            f"complexity_max={ccn}, "
            f"loc={row.get('loc_total', 0)}",
            observation=f"File has only {coverage:.0f}% line coverage "
            f"with complexity of {ccn}",
            why_it_matters="Complex files with low coverage carry "
            "high regression risk — defects are likely latent.",
            tool_source="coverage-ingest",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"coverage_line_pct": coverage, "complexity_max": ccn},
        )


class OwnershipMapper(EvidenceMapper):
    category = "ownership"
    abbreviation = "OWN"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        authors = row.get("unique_authors", 0)
        lines = row.get("total_lines", 0)
        top_pct = row.get("top_author_pct", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="knowledge_risk",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"authors={authors}, "
            f"top_author={row.get('top_author', '?')} "
            f"({top_pct:.0f}%), "
            f"lines={lines}",
            observation=f"File has {row.get('risk_level', '')} "
            f"knowledge risk — "
            f"{authors} author(s)",
            why_it_matters="Single-author files create bus factor "
            "risk; knowledge silos slow onboarding and increase "
            "incident response time.",
            tool_source="git-blame-scanner",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"unique_authors": authors, "total_lines": lines, "top_author_pct": top_pct},
        )


class QualityMapper(EvidenceMapper):
    category = "quality"
    abbreviation = "QUAL"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        smell_d = row.get("smell_density_per_kloc", 0) or 0
        issue_d = row.get("issue_density_per_kloc", 0) or 0
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="quality_issue",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"smells={row.get('semgrep_smell_count', 0)}, "
            f"issues={row.get('devskim_issue_count', 0)}, "
            f"loc={row.get('loc_total', 0)}",
            observation=f"File has {smell_d:.0f} smells/KLOC and "
            f"{issue_d:.0f} issues/KLOC",
            why_it_matters="High issue density correlates with "
            "elevated defect rates and higher maintenance cost.",
            tool_source="semgrep",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"smell_density_per_kloc": smell_d, "issue_density_per_kloc": issue_d},
        )


class MaintainabilityMapper(EvidenceMapper):
    category = "maintainability"
    abbreviation = "MAINT"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        loc = row.get("loc_total", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="file_size_hotspot",
            category=self.category,
            location=row.get("relative_path", ""),
            excerpt=f"loc={loc}, "
            f"language={row.get('language', '?')}",
            observation=f"File has {loc} lines of code — large file hotspot",
            why_it_matters="Large files are harder to review, test, "
            "and maintain; they accumulate technical debt faster.",
            tool_source="scc",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"loc_total": loc, "language": row.get("language", "")},
        )


class ArchitectureMapper(EvidenceMapper):
    category = "architecture"
    abbreviation = "ARCH"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="directory_structure",
            category=self.category,
            location=row.get("directory_path", row.get("relative_path", "")),
            excerpt=f"depth={row.get('depth', 0)}, "
            f"file_count={row.get('file_count', 0)}",
            observation=f"Directory has {row.get('file_count', 0)} files at depth {row.get('depth', 0)}",
            why_it_matters="Deep or overly flat directory structures "
            "hinder navigation and indicate poor module boundaries.",
            tool_source="layout-scanner",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"depth": row.get("depth", 0), "file_count": row.get("file_count", 0)},
        )


class DependenciesMapper(EvidenceMapper):
    category = "dependencies"
    abbreviation = "DEP"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="dependency_issue",
            category=self.category,
            location=row.get("relative_path", row.get("package_file", "")),
            excerpt=f"package={row.get('package_name', '?')}, "
            f"version={row.get('installed_version', '?')}",
            observation=f"Dependency {row.get('package_name', '?')} "
            f"has health concerns",
            why_it_matters="Unhealthy dependencies increase supply chain "
            "risk and maintenance burden.",
            tool_source=row.get("tool_source", "dependensee"),
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"package_name": row.get("package_name", ""), "installed_version": row.get("installed_version", "")},
        )


class DuplicationMapper(EvidenceMapper):
    category = "duplication"
    abbreviation = "DUP"

    def map_row(self, row: dict[str, Any], seq: int, run_pk: int) -> EvidenceItem:
        tokens = row.get("tokens", 0)
        lines = row.get("lines", 0)
        return EvidenceItem(
            evidence_id=self._make_id(seq),
            evidence_type="code_duplication",
            category=self.category,
            location=row.get("relative_path", row.get("source_file", "")),
            excerpt=f"tokens={tokens}, lines={lines}, "
            f"occurrences={row.get('occurrences', 0)}",
            observation=f"Duplicate block of {lines} lines ({tokens} tokens) "
            f"found in {row.get('occurrences', 0)} locations",
            why_it_matters="Code duplication multiplies maintenance cost — "
            "a fix in one copy must be applied to all.",
            tool_source="pmd-cpd",
            run_pk=row.get("tool_run_pk", run_pk),
            metadata={"tokens": tokens, "lines": lines, "occurrences": row.get("occurrences", 0)},
        )


# Mapper registry: category name → mapper class
MAPPER_REGISTRY: dict[str, type[EvidenceMapper]] = {
    "complexity": ComplexityMapper,
    "security": SecurityMapper,
    "coupling": CouplingMapper,
    "coverage": CoverageMapper,
    "ownership": OwnershipMapper,
    "quality": QualityMapper,
    "maintainability": MaintainabilityMapper,
    "architecture": ArchitectureMapper,
    "dependencies": DependenciesMapper,
    "duplication": DuplicationMapper,
}


def safe_map_rows(
    mapper: EvidenceMapper,
    rows: list[dict[str, Any]],
    run_pk: int,
) -> list[EvidenceItem]:
    """Map rows to evidence items, warning and skipping on per-row failure."""
    items: list[EvidenceItem] = []
    for i, row in enumerate(rows, start=1):
        try:
            items.append(mapper.map_row(row, i, run_pk))
        except Exception as exc:
            warnings.warn(
                f"[EvidenceCollector] Skipping {mapper.category} row {i}: {exc}",
                stacklevel=3,
            )
    return items
