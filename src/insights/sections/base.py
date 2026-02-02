"""
Base classes for report sections.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..data_fetcher import DataFetcher


@dataclass
class SectionConfig:
    """Configuration for a report section."""

    name: str
    title: str
    description: str
    priority: int  # Ordering in report (lower = higher priority)


@dataclass
class SectionData:
    """Data container for a rendered section."""

    id: str
    title: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)


class BaseSection(ABC):
    """Abstract base class for report sections."""

    config: SectionConfig

    @abstractmethod
    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch data for this section.

        Args:
            fetcher: DataFetcher instance for database queries.
            run_pk: The collection run primary key.

        Returns:
            Dictionary containing all data needed for rendering.
        """
        ...

    @abstractmethod
    def get_template_name(self) -> str:
        """
        Return the template file name for this section.

        Returns:
            Template filename (e.g., 'repo_health.html.j2').
        """
        ...

    def get_markdown_template_name(self) -> str:
        """
        Return the markdown template file name for this section.

        Returns:
            Template filename (e.g., 'repo_health.md.j2').
        """
        # Default: derive from HTML template name
        html_name = self.get_template_name()
        return html_name.replace(".html.j2", ".md.j2")

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """
        Validate the fetched data.

        Args:
            data: The data dictionary to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        return []

    def get_fallback_data(self) -> dict[str, Any]:
        """
        Return fallback data when the section cannot be rendered.

        Returns:
            Dictionary with minimal/empty data for graceful degradation.
        """
        return {}
