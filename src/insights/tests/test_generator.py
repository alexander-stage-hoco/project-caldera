"""Tests for InsightsGenerator."""

from unittest.mock import patch, MagicMock

from insights.generator import InsightsGenerator
from insights.sections.base import BaseSection, SectionConfig, SectionData
from insights.formatters.markdown import MarkdownFormatter


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
            "risk_register",
            "evidence_pack",
            "claim_register",
            "sampling_rationale",
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

        # All priorities should be valid numbers in range 0-99
        # Note: Some sections share priorities (e.g., secrets and cross_tool both use 5)
        # Evidence framework sections use high priorities (97-99) for appendix placement
        assert all(0 <= p <= 99 for p in priorities)
        assert len(priorities) == len(InsightsGenerator.SECTIONS)


class TestRenderSectionFallback:
    """Tests for _render_section error handling."""

    def test_render_section_uses_fallback_on_fetch_error(self):
        """When section.fetch_data raises, _render_section should use fallback data
        and set data['_error']."""
        with patch.object(InsightsGenerator, "__init__", lambda x, **kwargs: None):
            generator = InsightsGenerator.__new__(InsightsGenerator)

            # Create a section whose fetch_data raises
            section = MagicMock(spec=BaseSection)
            section.config = SectionConfig(
                name="broken_section",
                title="Broken",
                description="Always fails",
                priority=50,
            )
            section.fetch_data.side_effect = RuntimeError("DB gone")
            section.get_fallback_data.return_value = {"fallback_key": "fallback_val"}
            section.validate_data.return_value = []
            section.get_markdown_template_name.return_value = "broken.md.j2"

            # Use a real MarkdownFormatter which will hit _render_fallback_section
            formatter = MagicMock()
            formatter.format_section.return_value = "<rendered>"

            generator.fetcher = MagicMock()

            result = generator._render_section(section, run_pk=1, formatter=formatter)

            assert isinstance(result, SectionData)
            assert result.data["_error"] == "DB gone"
            assert result.data["fallback_key"] == "fallback_val"


class TestGenerateByCollection:
    """Tests for generate_by_collection delegation."""

    def test_delegates_to_generate_with_resolved_run_pk(self):
        """generate_by_collection should resolve SCC run_pk then call generate."""
        with patch.object(InsightsGenerator, "__init__", lambda x, **kwargs: None):
            generator = InsightsGenerator.__new__(InsightsGenerator)
            generator.fetcher = MagicMock()
            generator.fetcher.get_scc_run_pk_for_collection.return_value = 42

            with patch.object(generator, "generate", return_value="<report>") as mock_gen:
                result = generator.generate_by_collection(
                    collection_run_id="coll-abc",
                    format="md",
                    sections=["repo_health"],
                    title="My Report",
                )

            assert result == "<report>"
            mock_gen.assert_called_once_with(
                run_pk=42,
                format="md",
                sections=["repo_health"],
                output_path=None,
                title="My Report",
            )
            generator.fetcher.get_scc_run_pk_for_collection.assert_called_once_with("coll-abc")

