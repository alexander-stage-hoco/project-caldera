"""
HTML formatter using Jinja2 templates.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .base import BaseFormatter
from ..sections.base import SectionData


class HtmlFormatter(BaseFormatter):
    """HTML formatter using Jinja2 templates."""

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the HTML formatter.

        Args:
            templates_dir: Optional custom templates directory.
        """
        super().__init__(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["format_number"] = self._format_number
        self.env.filters["format_percent"] = self._format_percent
        self.env.filters["severity_class"] = self._severity_class
        self.env.filters["grade_class"] = self._grade_class
        self.env.filters["truncate_path"] = self._truncate_path

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
    def _severity_class(severity: str | None) -> str:
        """Get CSS class for a severity level."""
        if severity is None:
            return "severity-unknown"
        return f"severity-{severity.lower()}"

    @staticmethod
    def _grade_class(grade: str | None) -> str:
        """Get CSS class for a health grade."""
        if grade is None:
            return "grade-unknown"
        return f"grade-{grade.lower()}"

    @staticmethod
    def _truncate_path(path: str, max_length: int = 60) -> str:
        """Truncate a file path for display."""
        if len(path) <= max_length:
            return path
        return "..." + path[-(max_length - 3):]

    def format_report(
        self,
        title: str,
        sections: list[SectionData],
        metadata: dict[str, Any],
    ) -> str:
        """
        Format a complete HTML report.

        Args:
            title: Report title.
            sections: List of rendered section data.
            metadata: Report metadata.

        Returns:
            Complete HTML document.
        """
        template = self.env.get_template("base.html.j2")
        return template.render(
            report_title=title,
            sections=sections,
            generated_at=metadata.get("generated_at", ""),
            run_pk=metadata.get("run_pk", ""),
            repository=metadata.get("repository", ""),
            sections_included=metadata.get("sections_included", []),
            format=metadata.get("format", "html"),
        )

    def format_section(
        self,
        section_name: str,
        template_name: str,
        data: dict[str, Any],
    ) -> str:
        """
        Format a single HTML section.

        Args:
            section_name: Name/ID of the section.
            template_name: Template file to use.
            data: Data to pass to the template.

        Returns:
            Rendered HTML for the section.
        """
        template_path = f"sections/{template_name}"
        try:
            template = self.env.get_template(template_path)
        except Exception:
            # Fallback to inline rendering if template doesn't exist
            return self._render_fallback_section(section_name, data)

        return template.render(section_id=section_name, **data)

    def _render_fallback_section(
        self,
        section_name: str,
        data: dict[str, Any],
    ) -> str:
        """Render a fallback section when template is missing."""
        html_parts = [
            f'<section id="{section_name}" class="report-section">',
            f"<h2>{section_name.replace('_', ' ').title()}</h2>",
            "<p><em>Section template not available. Raw data:</em></p>",
            "<pre>",
        ]

        for key, value in data.items():
            if isinstance(value, list):
                html_parts.append(f"{key}: [{len(value)} items]")
            else:
                html_parts.append(f"{key}: {value}")

        html_parts.extend(["</pre>", "</section>"])
        return "\n".join(html_parts)

    @property
    def file_extension(self) -> str:
        """Return the file extension for HTML format."""
        return ".html"
