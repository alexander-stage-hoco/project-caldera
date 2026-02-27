"""Tests for report sections."""

from insights.sections.file_hotspots import FileHotspotsSection
from insights.sections.directory_analysis import DirectoryAnalysisSection
from insights.sections.vulnerabilities import VulnerabilitiesSection
from insights.sections.cross_tool import CrossToolSection
from insights.sections.language_coverage import LanguageCoverageSection
from insights.sections.technical_debt_summary import TechnicalDebtSummarySection


class TestFileHotspotsSection:
    """Tests for FileHotspotsSection."""

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


class TestFileHotspotsCompoundHotspots:
    """Tests for _find_compound_hotspots edge cases."""

    def test_file_in_all_three_categories_is_compound(self):
        """A file appearing in all 3 categories should be included in compound."""
        section = FileHotspotsSection()

        complexity = [{"relative_path": "src/big.py", "complexity": 60}]
        size = [{"relative_path": "src/big.py", "loc_total": 2000}]
        smells = [{"relative_path": "src/big.py", "smell_count": 15}]

        compound = section._find_compound_hotspots(complexity, size, smells)

        assert len(compound) == 1
        assert compound[0]["relative_path"] == "src/big.py"
        assert compound[0]["category_count"] == 3
        assert set(compound[0]["categories"]) == {"complexity", "size", "smells"}

    def test_file_in_only_one_category_is_excluded(self):
        """A file in only 1 category should NOT appear in compound hotspots."""
        section = FileHotspotsSection()

        complexity = [{"relative_path": "src/only_complex.py", "complexity": 60}]
        size = [{"relative_path": "src/only_big.py", "loc_total": 2000}]
        smells = [{"relative_path": "src/only_smelly.py", "smell_count": 15}]

        compound = section._find_compound_hotspots(complexity, size, smells)

        assert len(compound) == 0


class TestTechnicalDebtSummarySection:
    """Tests for TechnicalDebtSummarySection."""

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

    def test_score_to_grade_boundary_79_vs_80(self):
        """Test boundary at exactly 79 vs 80."""
        section = TechnicalDebtSummarySection()

        # 79 is >= 60 but < 80, so grade is "D"
        assert section._score_to_grade(79) == "D"
        # 80 is >= 80, so grade is "F"
        assert section._score_to_grade(80) == "F"

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
