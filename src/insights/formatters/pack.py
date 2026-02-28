"""LLM context pack formatter — produces a directory of topic-organized markdown files.

Unlike BaseFormatter subclasses (which render a single string via Jinja2),
PackFormatter writes multiple self-contained markdown files designed for
upload to an LLM as context.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..evidence.entities import EvidenceRegistry


# ---------------------------------------------------------------------------
# Topic mapping definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TopicMapping:
    """Maps a topic file to the report sections it aggregates."""

    filename: str
    title: str
    description: str
    sections: tuple[str, ...]


TOPIC_MAPPINGS: tuple[TopicMapping, ...] = (
    TopicMapping(
        filename="summary.md",
        title="Executive Summary and Repository Overview",
        description="High-level overview of repository health, tool coverage, and composite risk.",
        sections=(
            "executive_summary",
            "repo_health",
            "composite_risk",
            "tool_readiness",
            "tool_coverage_dashboard",
        ),
    ),
    TopicMapping(
        filename="security.md",
        title="Security Analysis",
        description="CVEs, secrets, security linting rules, and IaC misconfigurations.",
        sections=(
            "vulnerabilities",
            "secrets",
            "devskim_security",
            "iac_misconfigs",
        ),
    ),
    TopicMapping(
        filename="complexity.md",
        title="Complexity and Technical Debt",
        description="Cyclomatic complexity, size hotspots, and technical debt indicators.",
        sections=(
            "function_complexity",
            "file_hotspots",
            "code_size_hotspots",
            "technical_debt_summary",
            "distribution_insights",
        ),
    ),
    TopicMapping(
        filename="architecture.md",
        title="Architecture and Dependencies",
        description="Coupling, dependency health, import structure, and directory layout.",
        sections=(
            "coupling_analysis",
            "coupling_debt",
            "dependency_health",
            "import_dependencies",
            "circular_dependencies",
            "blast_radius",
            "directory_structure",
            "directory_analysis",
            "component_inventory",
        ),
    ),
    TopicMapping(
        filename="coverage.md",
        title="Test Coverage and Duplication",
        description="Test coverage gaps, .NET coverage, language-level coverage, and copy-paste detection.",
        sections=(
            "coverage_gap",
            "dotcover_coverage",
            "language_coverage",
            "code_duplication",
        ),
    ),
    TopicMapping(
        filename="ownership.md",
        title="Code Ownership and Knowledge Risk",
        description="Authorship distribution, bus factor, and knowledge concentration.",
        sections=(
            "authorship_risk",
            "knowledge_risk",
            "code_inequality",
        ),
    ),
    TopicMapping(
        filename="quality.md",
        title="Code Quality and Compliance",
        description="Linting rules, Roslyn violations, SonarQube findings, licenses, and cross-tool analysis.",
        sections=(
            "code_quality_rules",
            "roslyn_violations",
            "sonarqube_deep_dive",
            "module_health",
            "cross_tool",
            "license_compliance",
        ),
    ),
    TopicMapping(
        filename="risks.md",
        title="Risk Register and Evidence Chain",
        description="Aggregated risks, rewrite risk, evidence pack, claims, and sampling rationale.",
        sections=(
            "risk_register",
            "rewrite_risk",
            "evidence_pack",
            "claim_register",
            "sampling_rationale",
            "git_sizer",
        ),
    ),
)


# ---------------------------------------------------------------------------
# PackFormatter
# ---------------------------------------------------------------------------


class PackFormatter:
    """Renders Caldera analysis data into a directory of topic markdown files."""

    MAX_TABLE_ROWS = 50

    def render_pack(
        self,
        title: str,
        section_data: dict[str, dict[str, Any]],
        section_titles: dict[str, str],
        metadata: dict[str, Any],
        evidence_registry: EvidenceRegistry | None,
        output_dir: Path,
    ) -> Path:
        """Write all topic files, INDEX.md, and metadata.json to *output_dir*.

        Args:
            title: Report title (e.g. "Insights Report: my-repo").
            section_data: ``{section_name: data_dict}`` for every fetched section.
            section_titles: ``{section_name: human_title}``.
            metadata: Dict to embed in metadata.json.
            evidence_registry: Optional evidence registry for summary stats.
            output_dir: Directory to write into (created if needed).

        Returns:
            The *output_dir* path.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        repository = metadata.get("repository", "Unknown")
        topics_written: list[dict[str, Any]] = []

        for topic in TOPIC_MAPPINGS:
            content = self._render_topic(
                topic, section_data, section_titles, repository
            )
            if content is None:
                # Record skipped topic
                topics_written.append(
                    {
                        "filename": topic.filename,
                        "title": topic.title,
                        "sections_included": [],
                        "sections_skipped": list(topic.sections),
                        "written": False,
                    }
                )
                continue

            (output_dir / topic.filename).write_text(content)

            included = [s for s in topic.sections if s in section_data]
            skipped = [s for s in topic.sections if s not in section_data]
            topics_written.append(
                {
                    "filename": topic.filename,
                    "title": topic.title,
                    "sections_included": included,
                    "sections_skipped": skipped,
                    "written": True,
                }
            )

        # INDEX.md
        index_content = self._render_index(title, topics_written, metadata)
        (output_dir / "INDEX.md").write_text(index_content)

        # metadata.json
        meta_dict = self._build_metadata_json(
            metadata, topics_written, evidence_registry
        )
        (output_dir / "metadata.json").write_text(
            json.dumps(meta_dict, indent=2, default=str) + "\n"
        )

        return output_dir

    # -- Topic rendering ----------------------------------------------------

    def _render_topic(
        self,
        topic: TopicMapping,
        section_data: dict[str, dict[str, Any]],
        section_titles: dict[str, str],
        repository: str,
    ) -> str | None:
        """Render a single topic file.  Returns ``None`` if no sections have data."""
        parts: list[str] = []

        for section_name in topic.sections:
            data = section_data.get(section_name)
            if data is None:
                continue
            title = section_titles.get(section_name, section_name)
            rendered = self._render_section_data(section_name, title, data)
            if rendered:
                parts.append(rendered)

        if not parts:
            return None

        header = (
            f"# {topic.title}\n\n"
            f"> Part of Caldera analysis for {repository}. "
            f"See INDEX.md for full contents.\n"
        )
        return header + "\n---\n\n" + "\n---\n\n".join(parts) + "\n"

    # -- Section data rendering ---------------------------------------------

    def _render_section_data(
        self, section_name: str, title: str, data: dict[str, Any]
    ) -> str:
        """Render a section's data dict into structured markdown."""
        lines: list[str] = [f"## {title}\n"]

        for key, value in data.items():
            if self._should_skip_key(key):
                continue
            rendered = self._render_value(key, value)
            if rendered:
                lines.append(rendered)

        # Only the heading — nothing useful to show
        if len(lines) <= 1:
            return ""

        return "\n".join(lines) + "\n"

    def _render_value(self, key: str, value: Any, indent: int = 0) -> str:
        """Type-based dispatch to render a single value."""
        label = self._humanise_key(key)
        prefix = "  " * indent

        if value is None:
            return ""

        # Dataclass → convert to dict
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            value = dataclasses.asdict(value)

        if isinstance(value, list):
            if not value:
                return ""
            if isinstance(value[0], dict):
                return f"{prefix}**{label}:**\n\n{self._render_table(value)}"
            # List of scalars
            items = "\n".join(f"{prefix}- {v}" for v in value)
            return f"{prefix}**{label}:**\n{items}"

        if isinstance(value, dict):
            if not value:
                return ""
            inner = "\n".join(
                self._render_value(k, v, indent + 1)
                for k, v in value.items()
                if not self._should_skip_key(k) and self._render_value(k, v, indent + 1)
            )
            if not inner:
                return ""
            return f"{prefix}**{label}:**\n{inner}"

        if isinstance(value, float):
            formatted = f"{value:,.2f}" if abs(value) >= 0.01 else f"{value:.4g}"
            return f"{prefix}- {label}: {formatted}"

        if isinstance(value, int):
            return f"{prefix}- {label}: {value:,}"

        if isinstance(value, bool):
            return f"{prefix}- {label}: {'Yes' if value else 'No'}"

        # str / fallback
        return f"{prefix}- {label}: {value}"

    # -- Table rendering ----------------------------------------------------

    def _render_table(self, rows: list[dict[str, Any]], max_rows: int | None = None) -> str:
        """Render a list of dicts as a plain markdown table."""
        if not rows:
            return ""

        max_rows = max_rows or self.MAX_TABLE_ROWS

        # Collect headers from all rows (some may have different keys)
        headers: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for k in row:
                if k not in seen and not self._should_skip_key(k):
                    headers.append(k)
                    seen.add(k)

        if not headers:
            return ""

        # Header row
        header_labels = [self._humanise_key(h) for h in headers]
        header_line = "| " + " | ".join(header_labels) + " |"
        separator = "| " + " | ".join("---" for _ in headers) + " |"

        # Data rows
        display_rows = rows[:max_rows]
        data_lines: list[str] = []
        for row in display_rows:
            cells = []
            for h in headers:
                val = row.get(h, "")
                cells.append(self._format_cell(val))
            data_lines.append("| " + " | ".join(cells) + " |")

        parts = [header_line, separator, *data_lines]

        if len(rows) > max_rows:
            parts.append(f"\n*({len(rows) - max_rows} more rows not shown)*")

        return "\n".join(parts) + "\n"

    # -- INDEX.md -----------------------------------------------------------

    def _render_index(
        self,
        title: str,
        topics_written: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> str:
        """Render INDEX.md — orientation file for the LLM."""
        repository = metadata.get("repository", "Unknown")
        commit = metadata.get("commit", "unknown")
        generated_at = metadata.get("generated_at", "unknown")
        run_pk = metadata.get("run_pk", "unknown")
        profile = metadata.get("profile")

        written_topics = [t for t in topics_written if t["written"]]

        contents_rows: list[str] = []
        for t in written_topics:
            n_sections = len(t["sections_included"])
            contents_rows.append(
                f"| {t['filename']} | {t['title']} | {n_sections} |"
            )
        contents_table = "\n".join(contents_rows) if contents_rows else "| (none) | | |"

        return f"""# {title}

This context pack contains structured analysis results for the repository
"{repository}", generated by Project Caldera on {generated_at}.

## How to Use This Pack

Each file covers a specific analysis topic. Upload all files for comprehensive
Q&A, or select specific topic files for focused analysis.

## Contents

| File | Topic | Sections |
|------|-------|----------|
{contents_table}

## Evidence Traceability

Findings are linked via IDs across files:
- Evidence items: [E-XXX-NNN] — raw findings from tools
- Claims: [CLM-XXX-NNN] — pattern-based assertions derived from evidence
- Risks: [RISK-NNN] — execution risks aggregated from claims

Trace from risks.md -> claim IDs -> evidence IDs in topic files.

## Run Context

- Repository: {repository}
- Commit: {commit}
- Generated: {generated_at}
- Run PK: {run_pk}
- Profile: {profile or "all sections"}
"""

    # -- metadata.json ------------------------------------------------------

    def _build_metadata_json(
        self,
        metadata: dict[str, Any],
        topics_written: list[dict[str, Any]],
        evidence_registry: EvidenceRegistry | None,
    ) -> dict[str, Any]:
        """Build the metadata.json payload."""
        sections_included = sum(
            len(t["sections_included"]) for t in topics_written
        )
        sections_total = sum(
            len(t["sections_included"]) + len(t["sections_skipped"])
            for t in topics_written
        )

        evidence_summary: dict[str, int] = {}
        if evidence_registry is not None:
            summary = evidence_registry.summary()
            evidence_summary = {
                "total_evidence": summary["total_evidence"],
                "total_claims": summary["total_claims"],
                "total_risks": summary["total_risks"],
            }

        return {
            "schema_version": "1.0.0",
            "format": "pack",
            "generated_at": metadata.get("generated_at"),
            "repository": metadata.get("repository"),
            "commit": metadata.get("commit"),
            "run_pk": metadata.get("run_pk"),
            "profile": metadata.get("profile"),
            "topics": [
                {
                    "filename": t["filename"],
                    "title": t["title"],
                    "sections_included": t["sections_included"],
                    "sections_skipped": t["sections_skipped"],
                }
                for t in topics_written
            ],
            "sections_total": sections_total,
            "sections_included": sections_included,
            "evidence_summary": evidence_summary,
        }

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _should_skip_key(key: str) -> bool:
        """Skip internal and template-conditional keys."""
        return key.startswith("_") or key.startswith("has_")

    @staticmethod
    def _humanise_key(key: str) -> str:
        """Convert snake_case to Title Case."""
        return key.replace("_", " ").strip().title()

    @staticmethod
    def _format_cell(value: Any) -> str:
        """Format a single table cell value."""
        if value is None:
            return ""
        if isinstance(value, float):
            return f"{value:,.2f}" if abs(value) >= 0.01 else f"{value:.4g}"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, (list, dict)):
            return str(value)[:80]
        # Escape pipe characters in cell content
        return str(value).replace("|", "\\|")
