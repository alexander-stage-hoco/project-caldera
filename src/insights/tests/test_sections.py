"""Tests for report sections."""

import pytest
from unittest.mock import MagicMock

from insights.sections.repo_health import RepoHealthSection
from insights.sections.file_hotspots import FileHotspotsSection
from insights.sections.directory_analysis import DirectoryAnalysisSection
from insights.sections.vulnerabilities import VulnerabilitiesSection
from insights.sections.cross_tool import CrossToolSection
from insights.sections.language_coverage import LanguageCoverageSection
from insights.sections.coverage_gap import CoverageGapSection
from insights.sections.technical_debt_summary import TechnicalDebtSummarySection


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


class TestCoverageGapSection:
    """Tests for CoverageGapSection."""

    def test_config(self):
        """Test section configuration."""
        section = CoverageGapSection()

        assert section.config.name == "coverage_gap"
        assert section.config.title == "Coverage Gap Analysis"
        assert section.config.priority == 3.5
        assert "complexity" in section.config.description.lower()

    def test_get_template_name(self):
        """Test template name."""
        section = CoverageGapSection()
        assert section.get_template_name() == "coverage_gap.html.j2"

    def test_get_fallback_data(self):
        """Test fallback data structure."""
        section = CoverageGapSection()
        fallback = section.get_fallback_data()

        # Check top-level keys
        assert "hotspots" in fallback
        assert "critical_hotspots" in fallback
        assert "high_hotspots" in fallback
        assert "summary" in fallback
        assert "has_data" in fallback

        # Check fallback values
        assert fallback["hotspots"] == []
        assert fallback["has_data"] is False

        # Check summary structure
        summary = fallback["summary"]
        assert summary["critical_count"] == 0
        assert summary["high_count"] == 0
        assert summary["total_files"] == 0
        assert summary["total_statements_at_risk"] == 0

    def test_validate_data_no_data(self):
        """Test validation returns error when no data available."""
        section = CoverageGapSection()
        errors = section.validate_data({"has_data": False})

        assert len(errors) == 1
        assert "lizard" in errors[0].lower() or "coverage" in errors[0].lower()

    def test_validate_data_with_data(self):
        """Test validation passes when data is available."""
        section = CoverageGapSection()
        errors = section.validate_data({"has_data": True})

        assert len(errors) == 0


class TestTechnicalDebtSummarySection:
    """Tests for TechnicalDebtSummarySection."""

    def test_config(self):
        """Test section configuration."""
        section = TechnicalDebtSummarySection()

        assert section.config.name == "technical_debt_summary"
        assert section.config.title == "Technical Debt Summary"
        assert section.config.priority == 2
        assert "debt" in section.config.description.lower()

    def test_get_template_name(self):
        """Test template name."""
        section = TechnicalDebtSummarySection()
        assert section.get_template_name() == "technical_debt_summary.html.j2"

    def test_get_fallback_data(self):
        """Test fallback data structure."""
        section = TechnicalDebtSummarySection()
        fallback = section.get_fallback_data()

        # Check top-level keys
        assert "summary" in fallback
        assert "categories" in fallback
        assert "overall_score" in fallback
        assert "overall_grade" in fallback
        assert "hotspots" in fallback
        assert "hotspots_by_type" in fallback
        assert "priorities" in fallback
        assert "has_data" in fallback

        # Check category keys
        categories = fallback["categories"]
        assert "complexity" in categories
        assert "duplication" in categories
        assert "code_smells" in categories
        assert "coverage_gaps" in categories
        assert "size" in categories

        # Check default values
        assert fallback["overall_grade"] == "A"
        assert fallback["overall_score"] == 0
        assert fallback["has_data"] is False

    def test_validate_data_no_data(self):
        """Test validation returns error when no data available."""
        section = TechnicalDebtSummarySection()
        errors = section.validate_data({"has_data": False})

        assert len(errors) == 1
        assert "technical debt" in errors[0].lower() or "data" in errors[0].lower()

    def test_validate_data_with_data(self):
        """Test validation passes when data is available."""
        section = TechnicalDebtSummarySection()
        errors = section.validate_data({"has_data": True})

        assert len(errors) == 0

    def test_score_to_grade(self):
        """Test grade conversion from score."""
        section = TechnicalDebtSummarySection()

        # score >= 80 → "F"
        assert section._score_to_grade(80) == "F"
        assert section._score_to_grade(100) == "F"

        # score >= 60 → "D"
        assert section._score_to_grade(60) == "D"
        assert section._score_to_grade(79) == "D"

        # score >= 40 → "C"
        assert section._score_to_grade(40) == "C"
        assert section._score_to_grade(59) == "C"

        # score >= 20 → "B"
        assert section._score_to_grade(20) == "B"
        assert section._score_to_grade(39) == "B"

        # score < 20 → "A"
        assert section._score_to_grade(0) == "A"
        assert section._score_to_grade(19) == "A"

    def test_calculate_overall_score(self):
        """Test weighted score calculation."""
        section = TechnicalDebtSummarySection()

        categories = {
            "complexity": {"score": 50},
            "duplication": {"score": 40},
            "code_smells": {"score": 30},
            "coverage_gaps": {"score": 20},
            "size": {"score": 10},
        }

        # Weights: complexity=0.30, duplication=0.20, code_smells=0.25, coverage_gaps=0.15, size=0.10
        # Expected: 50*0.30 + 40*0.20 + 30*0.25 + 20*0.15 + 10*0.10
        # = 15 + 8 + 7.5 + 3 + 1 = 34.5 → rounds to 34 or 35
        score = section._calculate_overall_score(categories)

        assert score == 34 or score == 35  # Allow for rounding
        assert 30 <= score <= 40

    def test_get_remediation_action(self):
        """Test remediation action text generation."""
        section = TechnicalDebtSummarySection()

        # Complexity action
        complexity_data = {"critical": 5, "high": 10}
        action = section._get_remediation_action("complexity", complexity_data)
        assert "5 critical" in action
        assert "10 high" in action

        # Duplication action
        duplication_data = {"total_lines": 1500}
        action = section._get_remediation_action("duplication", duplication_data)
        assert "1,500" in action  # formatted with comma

        # Code smells action
        smells_data = {"high_plus": 25}
        action = section._get_remediation_action("code_smells", smells_data)
        assert "25" in action

        # Coverage gaps action
        coverage_data = {"critical": 3}
        action = section._get_remediation_action("coverage_gaps", coverage_data)
        assert "3 critical" in action

        # Size action
        size_data = {"critical": 8}
        action = section._get_remediation_action("size", size_data)
        assert "8 oversized" in action

        # Unknown category
        action = section._get_remediation_action("unknown", {})
        assert "review" in action.lower()
