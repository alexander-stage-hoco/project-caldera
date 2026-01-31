"""Tests for freshness checking in vulnerability analyzer."""
import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from vulnerability_analyzer import (
    PackageFreshness,
    VulnerabilityAnalysis,
    analysis_to_dict,
)


class TestPackageFreshness:
    """Tests for PackageFreshness dataclass."""

    def test_freshness_dataclass_creation(self):
        """Test creating a PackageFreshness instance."""
        freshness = PackageFreshness(
            package="requests",
            package_type="pip",
            installed_version="2.25.0",
            latest_version="2.31.0",
            major_versions_behind=0,
            minor_versions_behind=6,
            patch_versions_behind=0,
            is_outdated=True,
            days_since_latest=100,
            has_vulnerability=True,
            vulnerability_count=2,
        )
        assert freshness.package == "requests"
        assert freshness.is_outdated is True
        assert freshness.minor_versions_behind == 6
        assert freshness.vulnerability_count == 2

    def test_freshness_not_outdated(self):
        """Test PackageFreshness for an up-to-date package."""
        freshness = PackageFreshness(
            package="flask",
            package_type="pip",
            installed_version="3.0.0",
            latest_version="3.0.0",
            major_versions_behind=0,
            minor_versions_behind=0,
            patch_versions_behind=0,
            is_outdated=False,
            days_since_latest=0,
            has_vulnerability=False,
            vulnerability_count=0,
        )
        assert freshness.is_outdated is False
        assert freshness.has_vulnerability is False

    def test_freshness_with_vulnerability(self):
        """Test PackageFreshness for package with known vulnerability."""
        freshness = PackageFreshness(
            package="urllib3",
            package_type="pip",
            installed_version="1.26.0",
            latest_version="2.0.0",
            major_versions_behind=1,
            minor_versions_behind=0,
            patch_versions_behind=0,
            is_outdated=True,
            days_since_latest=365,
            has_vulnerability=True,
            vulnerability_count=5,
        )
        assert freshness.major_versions_behind == 1
        assert freshness.has_vulnerability is True
        assert freshness.vulnerability_count == 5


class TestVulnerabilityAnalysisFreshness:
    """Tests for freshness fields in VulnerabilityAnalysis."""

    def test_analysis_freshness_defaults(self):
        """Test default freshness values in VulnerabilityAnalysis."""
        analysis = VulnerabilityAnalysis()
        assert analysis.freshness_checked is False
        assert analysis.outdated_count == 0
        assert analysis.outdated_pct == 0.0
        assert analysis.package_freshness == []

    def test_analysis_with_freshness_data(self):
        """Test VulnerabilityAnalysis with populated freshness data."""
        freshness_pkg = PackageFreshness(
            package="requests",
            package_type="pip",
            installed_version="2.25.0",
            latest_version="2.31.0",
            major_versions_behind=0,
            minor_versions_behind=6,
            patch_versions_behind=0,
            is_outdated=True,
            days_since_latest=100,
            has_vulnerability=True,
            vulnerability_count=2,
        )

        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=True,
            outdated_count=1,
            outdated_pct=100.0,
            package_freshness=[freshness_pkg],
        )

        assert analysis.freshness_checked is True
        assert analysis.outdated_count == 1
        assert len(analysis.package_freshness) == 1


class TestAnalysisToDictFreshness:
    """Tests for freshness section in analysis_to_dict output."""

    def test_freshness_in_dict_when_checked(self):
        """Test that freshness section appears when freshness_checked=True."""
        freshness_pkg = PackageFreshness(
            package="requests",
            package_type="pip",
            installed_version="2.25.0",
            latest_version="2.31.0",
            major_versions_behind=0,
            minor_versions_behind=6,
            patch_versions_behind=0,
            is_outdated=True,
            days_since_latest=100,
            has_vulnerability=True,
            vulnerability_count=2,
        )

        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=True,
            outdated_count=1,
            outdated_pct=100.0,
            package_freshness=[freshness_pkg],
        )

        result = analysis_to_dict(analysis)

        assert "results" in result
        assert "freshness" in result["results"]
        assert result["results"]["freshness"]["checked"] is True
        assert result["results"]["freshness"]["total_packages"] == 1
        assert result["results"]["freshness"]["outdated_count"] == 1
        assert len(result["results"]["freshness"]["packages"]) == 1

        pkg = result["results"]["freshness"]["packages"][0]
        assert pkg["package"] == "requests"
        assert pkg["installed_version"] == "2.25.0"
        assert pkg["latest_version"] == "2.31.0"
        assert pkg["is_outdated"] is True

    def test_no_freshness_when_not_checked(self):
        """Test that freshness section is absent when freshness_checked=False."""
        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=False,
        )

        result = analysis_to_dict(analysis)

        assert "results" in result
        assert "freshness" not in result["results"]

    def test_freshness_empty_packages(self):
        """Test freshness section with no packages (but checked)."""
        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=True,
            outdated_count=0,
            outdated_pct=0.0,
            package_freshness=[],
        )

        result = analysis_to_dict(analysis)

        assert "results" in result
        assert "freshness" in result["results"]
        assert result["results"]["freshness"]["total_packages"] == 0
        assert result["results"]["freshness"]["packages"] == []


class TestFreshnessMetrics:
    """Tests for freshness metric calculations."""

    def test_outdated_percentage_calculation(self):
        """Test that outdated percentage is calculated correctly."""
        pkg1 = PackageFreshness(
            package="pkg1", package_type="pip",
            installed_version="1.0.0", latest_version="2.0.0",
            major_versions_behind=1, minor_versions_behind=0, patch_versions_behind=0,
            is_outdated=True, days_since_latest=100,
            has_vulnerability=False, vulnerability_count=0,
        )
        pkg2 = PackageFreshness(
            package="pkg2", package_type="pip",
            installed_version="3.0.0", latest_version="3.0.0",
            major_versions_behind=0, minor_versions_behind=0, patch_versions_behind=0,
            is_outdated=False, days_since_latest=0,
            has_vulnerability=False, vulnerability_count=0,
        )

        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=True,
            outdated_count=1,
            outdated_pct=50.0,  # 1 out of 2 packages
            package_freshness=[pkg1, pkg2],
        )

        result = analysis_to_dict(analysis)
        assert result["results"]["freshness"]["outdated_pct"] == 50.0

    def test_major_versions_behind_total(self):
        """Test calculation of total major versions behind."""
        pkg1 = PackageFreshness(
            package="pkg1", package_type="pip",
            installed_version="1.0.0", latest_version="3.0.0",
            major_versions_behind=2, minor_versions_behind=0, patch_versions_behind=0,
            is_outdated=True, days_since_latest=200,
            has_vulnerability=False, vulnerability_count=0,
        )
        pkg2 = PackageFreshness(
            package="pkg2", package_type="pip",
            installed_version="1.0.0", latest_version="2.0.0",
            major_versions_behind=1, minor_versions_behind=0, patch_versions_behind=0,
            is_outdated=True, days_since_latest=100,
            has_vulnerability=False, vulnerability_count=0,
        )

        analysis = VulnerabilityAnalysis(
            repo_name="test-repo",
            freshness_checked=True,
            major_versions_behind_total=3,  # 2 + 1
            package_freshness=[pkg1, pkg2],
        )

        result = analysis_to_dict(analysis)
        assert result["results"]["freshness"]["major_versions_behind_total"] == 3
