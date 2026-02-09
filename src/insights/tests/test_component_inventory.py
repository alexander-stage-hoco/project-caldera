"""Tests for ComponentInventorySection."""

import pytest
from unittest.mock import MagicMock

from insights.sections.component_inventory import ComponentInventorySection


class TestComponentInventorySection:
    """Tests for the ComponentInventorySection class."""

    def test_config(self):
        """Test section configuration."""
        section = ComponentInventorySection()
        assert section.config.name == "component_inventory"
        assert section.config.title == "Component Inventory"
        assert section.config.priority == 5

    def test_template_name(self):
        """Test template name generation."""
        section = ComponentInventorySection()
        assert section.get_template_name() == "component_inventory.html.j2"
        assert section.get_markdown_template_name() == "component_inventory.md.j2"

    def test_fallback_data(self):
        """Test fallback data structure."""
        section = ComponentInventorySection()
        fallback = section.get_fallback_data()

        assert fallback["components"] == []
        assert fallback["healthy_components"] == []
        assert fallback["at_risk_components"] == []
        assert fallback["critical_components"] == []
        assert fallback["has_data"] is False
        assert fallback["has_critical"] is False
        assert "summary" in fallback
        assert fallback["summary"]["total_components"] == 0
        assert "grade_distribution" in fallback
        assert fallback["grade_distribution"]["A"] == 0

    def test_validate_data_no_data(self):
        """Test validation with no data."""
        section = ComponentInventorySection()
        errors = section.validate_data({"has_data": False})
        assert len(errors) == 1
        assert "No component data" in errors[0]

    def test_validate_data_with_data(self):
        """Test validation with data."""
        section = ComponentInventorySection()
        errors = section.validate_data({"has_data": True})
        assert len(errors) == 0

    def test_identify_risks_high_coupling(self):
        """Test risk identification for high coupling."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 60,
            "fan_out": 10,
            "avg_ccn": 5,
            "avg_top_author_pct": 40,
            "instability": 0.5,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert any("High coupling" in r for r in risks)

    def test_identify_risks_high_fan_out(self):
        """Test risk identification for high fan-out."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 40,
            "fan_out": 35,
            "avg_ccn": 5,
            "avg_top_author_pct": 40,
            "instability": 0.5,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert any("fan_out" in r for r in risks)

    def test_identify_risks_high_complexity(self):
        """Test risk identification for high complexity."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 10,
            "fan_out": 5,
            "avg_ccn": 18,
            "avg_top_author_pct": 40,
            "instability": 0.5,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert any("complexity" in r.lower() for r in risks)

    def test_identify_risks_knowledge_concentration(self):
        """Test risk identification for knowledge concentration."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 10,
            "fan_out": 5,
            "avg_ccn": 5,
            "avg_top_author_pct": 80,
            "instability": 0.5,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert any("Knowledge concentration" in r for r in risks)

    def test_identify_risks_unstable(self):
        """Test risk identification for high instability."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 10,
            "fan_out": 5,
            "avg_ccn": 5,
            "avg_top_author_pct": 40,
            "instability": 0.9,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert any("unstable" in r.lower() for r in risks)

    def test_identify_risks_critical_hotspots(self):
        """Test risk identification for critical hotspots."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 10,
            "fan_out": 5,
            "avg_ccn": 5,
            "avg_top_author_pct": 40,
            "instability": 0.5,
            "hotspots": [
                {"hotspot_type": "critical_complexity"},
                {"hotspot_type": "critical_complexity"},
            ],
        }
        risks = section._identify_risks(comp)
        assert any("critical complexity hotspot" in r for r in risks)

    def test_identify_risks_no_risks(self):
        """Test when no risks are identified."""
        section = ComponentInventorySection()
        comp = {
            "total_coupling": 10,
            "fan_out": 5,
            "avg_ccn": 5,
            "avg_top_author_pct": 40,
            "instability": 0.5,
            "hotspots": [],
        }
        risks = section._identify_risks(comp)
        assert len(risks) == 0

    def test_build_summary_empty(self):
        """Test summary building with empty components."""
        section = ComponentInventorySection()
        summary = section._build_summary([])
        assert summary["total_components"] == 0
        assert summary["healthy_count"] == 0
        assert summary["avg_health_score"] == 0

    def test_build_summary(self):
        """Test summary building with components."""
        section = ComponentInventorySection()
        components = [
            {"health_grade": "A", "health_score": 95, "total_coupling": 10, "loc": 1000, "file_count": 5},
            {"health_grade": "B", "health_score": 85, "total_coupling": 20, "loc": 2000, "file_count": 10},
            {"health_grade": "C", "health_score": 72, "total_coupling": 30, "loc": 3000, "file_count": 15},
            {"health_grade": "F", "health_score": 45, "total_coupling": 60, "loc": 5000, "file_count": 25},
        ]
        summary = section._build_summary(components)

        assert summary["total_components"] == 4
        assert summary["healthy_count"] == 2
        assert summary["at_risk_count"] == 1
        assert summary["critical_count"] == 1
        assert summary["avg_health_score"] == 74.2  # (95+85+72+45)/4
        assert summary["total_loc"] == 11000
        assert summary["total_files"] == 55
        assert summary["avg_coupling"] == 30.0

    def test_fetch_data_no_data(self):
        """Test fetch_data with no data available."""
        section = ComponentInventorySection()
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("No data")

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is False
        assert data["components"] == []
        assert data["summary"]["total_components"] == 0

    def test_fetch_data_with_components(self):
        """Test fetch_data with component data."""
        section = ComponentInventorySection()
        mock_fetcher = MagicMock()

        # Mock component data
        mock_fetcher.fetch.side_effect = [
            # component_inventory query
            [
                {
                    "directory_id": "dir1",
                    "directory_path": "src/services",
                    "display_name": "services",
                    "depth": 1,
                    "file_count": 10,
                    "loc": 2000,
                    "code_loc": 1800,
                    "complexity": 50,
                    "language_count": 2,
                    "function_count": 30,
                    "total_ccn": 60,
                    "avg_ccn": 6.0,
                    "max_ccn": 15,
                    "fan_in": 5,
                    "fan_out": 10,
                    "total_coupling": 15,
                    "instability": 0.67,
                    "avg_top_author_pct": 45.0,
                    "max_top_author_pct": 60.0,
                    "avg_unique_authors": 3.0,
                    "health_score": 75.0,
                    "health_grade": "C",
                    "complexity_component": 70.0,
                    "coupling_component": 85.0,
                    "stability_component": 66.0,
                    "knowledge_component": 55.0,
                    "size_component": 100.0,
                },
            ],
            # component_dependencies query
            [
                {
                    "direction": "outbound",
                    "component_id": "dir1",
                    "component_path": "src/services",
                    "related_component": "src/models",
                    "call_type": "direct",
                    "call_count": 25,
                    "unique_callers": 5,
                    "unique_callees": 8,
                },
            ],
            # component_hotspots query
            [
                {
                    "component_id": "dir1",
                    "component_path": "src/services",
                    "file_id": "file1",
                    "file_path": "src/services/OrderService.cs",
                    "total_ccn": 45,
                    "max_ccn": 18,
                    "hotspot_type": "high_complexity",
                    "rank_in_component": 1,
                },
            ],
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert len(data["components"]) == 1
        assert data["components"][0]["display_name"] == "services"
        assert data["components"][0]["health_grade"] == "C"
        assert len(data["components"][0]["outbound_dependencies"]) == 1
        assert len(data["components"][0]["hotspots"]) == 1
        assert data["summary"]["total_components"] == 1
        assert data["summary"]["at_risk_count"] == 1

    def test_component_categorization(self):
        """Test that components are correctly categorized by grade."""
        section = ComponentInventorySection()
        mock_fetcher = MagicMock()

        mock_fetcher.fetch.side_effect = [
            # component_inventory query
            [
                {"directory_path": "src/a", "display_name": "a", "health_grade": "A", "health_score": 92, "total_coupling": 5, "loc": 500, "file_count": 3},
                {"directory_path": "src/b", "display_name": "b", "health_grade": "B", "health_score": 82, "total_coupling": 10, "loc": 800, "file_count": 5},
                {"directory_path": "src/c", "display_name": "c", "health_grade": "C", "health_score": 72, "total_coupling": 15, "loc": 1000, "file_count": 8},
                {"directory_path": "src/d", "display_name": "d", "health_grade": "D", "health_score": 62, "total_coupling": 25, "loc": 1500, "file_count": 10},
                {"directory_path": "src/e", "display_name": "e", "health_grade": "F", "health_score": 45, "total_coupling": 60, "loc": 3000, "file_count": 20},
            ],
            # component_dependencies query
            [],
            # component_hotspots query
            [],
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert len(data["healthy_components"]) == 2  # A and B
        assert len(data["at_risk_components"]) == 2  # C and D
        assert len(data["critical_components"]) == 1  # F
        assert data["has_critical"] is True

        # Check grade distribution
        assert data["grade_distribution"]["A"] == 1
        assert data["grade_distribution"]["B"] == 1
        assert data["grade_distribution"]["C"] == 1
        assert data["grade_distribution"]["D"] == 1
        assert data["grade_distribution"]["F"] == 1
