"""Tests for report sections."""

import pytest
from unittest.mock import MagicMock

from insights.sections.repo_health import RepoHealthSection
from insights.sections.file_hotspots import FileHotspotsSection
from insights.sections.directory_analysis import DirectoryAnalysisSection
from insights.sections.vulnerabilities import VulnerabilitiesSection
from insights.sections.cross_tool import CrossToolSection
from insights.sections.language_coverage import LanguageCoverageSection


class TestRepoHealthSection:
    """Tests for RepoHealthSection."""

    def test_config(self):
        """Test section configuration."""
        section = RepoHealthSection()

        assert section.config.name == "repo_health"
        assert section.config.priority == 1
        assert "health" in section.config.description.lower()

    def test_get_template_name(self):
        """Test template name."""
        section = RepoHealthSection()
        assert section.get_template_name() == "repo_health.html.j2"

    def test_get_fallback_data(self):
        """Test fallback data structure."""
        section = RepoHealthSection()
        fallback = section.get_fallback_data()

        assert "total_files" in fallback
        assert "total_loc" in fallback
        assert "avg_ccn" in fallback
        assert "languages" in fallback
        assert fallback["total_files"] == 0


class TestFileHotspotsSection:
    """Tests for FileHotspotsSection."""

    def test_config(self):
        """Test section configuration."""
        section = FileHotspotsSection()

        assert section.config.name == "file_hotspots"
        assert section.config.priority == 2

    def test_find_compound_hotspots(self):
        """Test compound hotspot detection."""
        section = FileHotspotsSection()

        complexity = [
            {"relative_path": "file1.py", "complexity": 50},
            {"relative_path": "file2.py", "complexity": 40},
        ]
        size = [
            {"relative_path": "file1.py", "loc_total": 1000},
            {"relative_path": "file3.py", "loc_total": 800},
        ]
        smells = [
            {"relative_path": "file2.py", "smell_count": 10},
            {"relative_path": "file3.py", "smell_count": 8},
        ]

        compound = section._find_compound_hotspots(complexity, size, smells)

        # file1.py should be in compound (complexity + size)
        paths = [c["relative_path"] for c in compound]
        assert "file1.py" in paths

        # Check category count
        file1 = next(c for c in compound if c["relative_path"] == "file1.py")
        assert file1["category_count"] >= 2


class TestVulnerabilitiesSection:
    """Tests for VulnerabilitiesSection."""

    def test_config(self):
        """Test section configuration."""
        section = VulnerabilitiesSection()

        assert section.config.name == "vulnerabilities"
        assert section.config.priority == 4

    def test_calculate_risk_level(self):
        """Test risk level calculation."""
        section = VulnerabilitiesSection()

        assert section._calculate_risk_level(critical=5, high=10) == "critical"
        assert section._calculate_risk_level(critical=0, high=10) == "high"
        assert section._calculate_risk_level(critical=0, high=3) == "medium"
        assert section._calculate_risk_level(critical=0, high=0) == "low"


class TestDirectoryAnalysisSection:
    """Tests for DirectoryAnalysisSection."""

    def test_calculate_tree_stats(self):
        """Test tree statistics calculation."""
        section = DirectoryAnalysisSection()

        directories = [
            {"directory_path": "src/components/buttons"},
            {"directory_path": "src/utils"},
            {"directory_path": "tests"},
        ]

        stats = section._calculate_tree_stats(directories)

        assert stats["total_dirs"] == 3
        assert stats["max_depth"] >= 2
        assert stats["avg_depth"] > 0


class TestLanguageCoverageSection:
    """Tests for LanguageCoverageSection."""

    def test_categorize_languages(self):
        """Test language categorization."""
        section = LanguageCoverageSection()

        languages = [
            {"language": "Python", "file_count": 50, "loc": 10000},
            {"language": "JavaScript", "file_count": 30, "loc": 5000},
            {"language": "HTML", "file_count": 20, "loc": 3000},
            {"language": "C#", "file_count": 10, "loc": 2000},
        ]

        categories = section._categorize_languages(languages)

        # Check categorization
        assert any(l["language"] == "C#" for l in categories["compiled"])
        assert any(l["language"] == "Python" for l in categories["scripted"])
        assert any(l["language"] == "JavaScript" for l in categories["scripted"])
        assert any(l["language"] == "HTML" for l in categories["markup"])


class TestCrossToolSection:
    """Tests for CrossToolSection."""

    def test_calculate_risk_summary(self):
        """Test risk summary calculation."""
        section = CrossToolSection()

        complex_smelly = [
            {"relative_path": "file1.py"},
            {"relative_path": "file2.py"},
        ]
        complex_vulnerable = [
            {"relative_path": "file1.py"},
            {"relative_path": "file3.py"},
        ]

        summary = section._calculate_risk_summary(
            complex_smelly, complex_vulnerable
        )

        assert summary["total_risks"] == 3  # file1, file2, file3
        assert summary["complex_smelly_count"] == 2
        assert summary["complex_vulnerable_count"] == 2
