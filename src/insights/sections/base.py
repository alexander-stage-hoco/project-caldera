"""
Base classes for report sections.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from ..data_fetcher import DataFetcher

if TYPE_CHECKING:
    from ..evidence.entities import EvidenceRegistry


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
    _warned: ClassVar[set[tuple[str, str, str]]] = set()

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

    def _safe_fetch(
        self,
        fetcher: DataFetcher,
        query_name: str,
        run_pk: int,
        fallback: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Fetch data with graceful degradation and a warning on failure.

        Args:
            fetcher: DataFetcher instance for database queries.
            query_name: The query name to execute.
            run_pk: The collection run primary key.
            fallback: Value to return on failure (defaults to ``[]``).
            **kwargs: Additional keyword arguments forwarded to ``fetcher.fetch``.

        Returns:
            The fetched data, or *fallback* if the query raised an exception.
        """
        try:
            return fetcher.fetch(query_name, run_pk, **kwargs)
        except Exception as exc:
            key = (self.config.name, query_name, type(exc).__name__)
            if key not in BaseSection._warned:
                BaseSection._warned.add(key)
                warnings.warn(
                    f"[{self.config.name}] Query '{query_name}' failed: {exc}",
                    stacklevel=2,
                )
            return fallback if fallback is not None else []

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


class EvidenceAwareSection(BaseSection):
    """Mixin for sections that consume the evidence registry.

    The generator injects the registry via ``set_evidence_registry()``
    before calling ``fetch_data()``.  Subclasses access it through
    ``self._evidence_registry``.
    """

    _evidence_registry: EvidenceRegistry | None = None

    def set_evidence_registry(self, registry: EvidenceRegistry) -> None:
        """Inject the evidence registry for this render pass."""
        self._evidence_registry = registry
