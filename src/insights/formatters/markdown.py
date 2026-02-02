"""
Markdown formatter for report output.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .base import BaseFormatter
from ..sections.base import SectionData


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter using Jinja2 templates."""

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the Markdown formatter.

        Args:
            templates_dir: Optional custom templates directory.
        """
        super().__init__(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,  # No escaping for Markdown
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["format_number"] = self._format_number
        self.env.filters["format_percent"] = self._format_percent
        self.env.filters["md_table"] = self._md_table
        self.env.filters["severity_emoji"] = self._severity_emoji
        self.env.filters["grade_emoji"] = self._grade_emoji

    @staticmethod
    def _format_number(value: int | float | None) -> str:
        """Format a number with thousands separator."""
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return f"{value:,}"

    @staticmethod
    def _format_percent(value: float | None) -> str:
        """Format a percentage value."""
        if value is None:
            return "N/A"
        return f"{value:.1f}%"

    @staticmethod
    def _severity_emoji(severity: str | None) -> str:
        """Get emoji for a severity level."""
        emojis = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "🔵",
        }
        if severity is None:
            return "⚪"
        return emojis.get(severity.lower(), "⚪")

    @staticmethod
    def _grade_emoji(grade: str | None) -> str:
        """Get emoji for a health grade."""
        emojis = {
            "a": "🟢",
            "b": "🟢",
            "c": "🟡",
            "d": "🟠",
            "f": "🔴",
        }
        if grade is None:
            return "⚪"
        return emojis.get(grade.lower(), "⚪")

    @staticmethod
    def _md_table(rows: list[dict], columns: list[str] | None = None) -> str:
        """
        Format a list of dicts as a Markdown table.

        Args:
            rows: List of dictionaries representing table rows.
            columns: Optional list of column names to include (in order).

        Returns:
            Formatted Markdown table string.
        """
        if not rows:
            return "*No data available*"

        if columns is None:
            columns = list(rows[0].keys())

        # Header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"

        # Rows
        table_rows = []
        for row in rows:
            values = [str(row.get(col, "")) for col in columns]
            table_rows.append("| " + " | ".join(values) + " |")

        return "\n".join([header, separator] + table_rows)

    def format_report(
        self,
        title: str,
        sections: list[SectionData],
        metadata: dict[str, Any],
    ) -> str:
        """
        Format a complete Markdown report.

        Args:
            title: Report title.
            sections: List of rendered section data.
            metadata: Report metadata.

        Returns:
            Complete Markdown document.
        """
        try:
            template = self.env.get_template("base.md.j2")
            return template.render(
                report_title=title,
                sections=sections,
                generated_at=metadata.get("generated_at", ""),
                run_pk=metadata.get("run_pk", ""),
                repository=metadata.get("repository", ""),
                **metadata,
            )
        except Exception:
            # Fallback to inline rendering
            return self._render_fallback_report(title, sections, metadata)

    def _render_fallback_report(
        self,
        title: str,
        sections: list[SectionData],
        metadata: dict[str, Any],
    ) -> str:
        """Render a fallback report when template is missing."""
        lines = [
            f"# {title}",
            "",
            f"**Generated:** {metadata.get('generated_at', 'N/A')}",
            f"**Run:** {metadata.get('run_pk', 'N/A')}",
            "",
            "---",
            "",
            "## Table of Contents",
            "",
        ]

        # TOC
        for section in sections:
            anchor = section.id.replace("_", "-")
            lines.append(f"- [{section.title}](#{anchor})")

        lines.extend(["", "---", ""])

        # Sections
        for section in sections:
            lines.append(section.content)
            lines.append("")

        lines.extend([
            "---",
            "",
            "*Generated by Project Vulcan Insights*",
        ])

        return "\n".join(lines)

    def format_section(
        self,
        section_name: str,
        template_name: str,
        data: dict[str, Any],
    ) -> str:
        """
        Format a single Markdown section.

        Args:
            section_name: Name/ID of the section.
            template_name: Template file to use.
            data: Data to pass to the template.

        Returns:
            Rendered Markdown for the section.
        """
        template_path = f"sections/{template_name}"
        try:
            template = self.env.get_template(template_path)
            return template.render(section_id=section_name, **data)
        except Exception:
            # Fallback to inline rendering
            return self._render_fallback_section(section_name, data)

    def _render_fallback_section(
        self,
        section_name: str,
        data: dict[str, Any],
    ) -> str:
        """Render a fallback section when template is missing."""
        title = section_name.replace("_", " ").title()
        lines = [
            f"## {title}",
            "",
        ]

        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                lines.append(f"**{key}:** {len(value)} items")
                if value and isinstance(value[0], dict):
                    lines.append("")
                    lines.append(self._md_table(value[:10]))  # Limit to 10 rows
            elif isinstance(value, dict):
                lines.append(f"**{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)

    @property
    def file_extension(self) -> str:
        """Return the file extension for Markdown format."""
        return ".md"
