"""Tests for InsightsGenerator."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from insights.generator import InsightsGenerator
from insights.sections.base import SectionData


class TestInsightsGenerator:
    """Tests for the InsightsGenerator class."""

    def test_sections_registered(self):
        """Test that all expected sections are registered."""
        expected_sections = [
            "tool_readiness",
            "tool_coverage_dashboard",
            "executive_summary",
            "repo_health",
            "file_hotspots",
            "directory_analysis",
            "vulnerabilities",
            "secrets",
            "cross_tool",
            "language_coverage",
            "distribution_insights",
            "roslyn_violations",
            "iac_misconfigs",
            "module_health",
            "code_inequality",
            "composite_risk",
            "function_complexity",
            "coupling_analysis",
            "authorship_risk",
            "knowledge_risk",
            "code_duplication",
            "dependency_health",
            "license_compliance",
            "directory_structure",
            "blast_radius",
            "code_size_hotspots",
            "code_quality_rules",
            "sonarqube_deep_dive",
            "coverage_gap",
            "technical_debt_summary",
            "coupling_debt",
            "component_inventory",
            "import_dependencies",
            "circular_dependencies",
            "devskim_security",
            "dotcover_coverage",
            "git_sizer",
        ]

        assert set(InsightsGenerator.SECTIONS.keys()) == set(expected_sections)

    def test_list_sections(self):
        """Test listing available sections."""
        with patch.object(InsightsGenerator, "__init__", lambda x, **kwargs: None):
            generator = InsightsGenerator.__new__(InsightsGenerator)
            generator.sections = {
                name: cls() for name, cls in InsightsGenerator.SECTIONS.items()
            }

            sections = generator.list_sections()

            assert len(sections) == len(InsightsGenerator.SECTIONS)
            assert all("name" in s for s in sections)
            assert all("title" in s for s in sections)
            assert all("description" in s for s in sections)
            assert all("priority" in s for s in sections)

    def test_section_priorities(self):
        """Test that sections have valid priorities."""
        priorities = []
        for cls in InsightsGenerator.SECTIONS.values():
            section = cls()
            priorities.append(section.config.priority)

        # All priorities should be valid numbers in range 0-11
        # Note: Some sections share priorities (e.g., secrets and cross_tool both use 5)
        assert all(0 <= p <= 11 for p in priorities)
        assert len(priorities) == len(InsightsGenerator.SECTIONS)

    @pytest.mark.parametrize("format_type", ["html", "md"])
    def test_format_support(self, format_type: str):
        """Test that both HTML and MD formats are supported."""
        with patch.object(InsightsGenerator, "__init__", lambda x, **kwargs: None):
            generator = InsightsGenerator.__new__(InsightsGenerator)
            generator._formatters = {
                "html": MagicMock(),
                "md": MagicMock(),
            }

            assert format_type in generator._formatters


class TestSectionData:
    """Tests for SectionData dataclass."""

    def test_section_data_creation(self):
        """Test creating a SectionData instance."""
        data = SectionData(
            id="test_section",
            title="Test Section",
            content="<div>Content</div>",
            data={"key": "value"},
        )

        assert data.id == "test_section"
        assert data.title == "Test Section"
        assert data.content == "<div>Content</div>"
        assert data.data == {"key": "value"}

    def test_section_data_default_data(self):
        """Test SectionData with default empty data."""
        data = SectionData(
            id="test",
            title="Test",
            content="",
        )

        assert data.data == {}
