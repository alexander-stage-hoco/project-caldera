"""
Base formatter class for report output.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..sections.base import SectionData


class BaseFormatter(ABC):
    """Abstract base class for report formatters."""

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize the formatter.

        Args:
            templates_dir: Optional custom templates directory.
        """
        self.templates_dir = templates_dir or (Path(__file__).parent.parent / "templates")

    @abstractmethod
    def format_report(
        self,
        title: str,
        sections: list[SectionData],
        metadata: dict[str, Any],
    ) -> str:
        """
        Format a complete report.

        Args:
            title: Report title.
            sections: List of rendered section data.
            metadata: Report metadata (run_pk, generated_at, etc.).

        Returns:
            Formatted report as a string.
        """
        ...

    @abstractmethod
    def format_section(
        self,
        section_name: str,
        template_name: str,
        data: dict[str, Any],
    ) -> str:
        """
        Format a single section.

        Args:
            section_name: Name/ID of the section.
            template_name: Template file to use.
            data: Data to pass to the template.

        Returns:
            Formatted section content.
        """
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format (e.g., '.html')."""
        ...
