"""Tests for registry client functions."""
import pytest
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from registry_clients import (
    calculate_version_delta,
    calculate_days_since,
    get_registry_fetcher,
)


class TestVersionDelta:
    """Tests for calculate_version_delta function."""

    def test_major_version_behind(self):
        """Test detection of major version differences."""
        result = calculate_version_delta("1.0.0", "2.0.0")
        assert result["major_behind"] == 1
        assert result["is_outdated"] is True

    def test_two_major_versions_behind(self):
        """Test detection of multiple major version differences."""
        result = calculate_version_delta("1.0.0", "3.0.0")
        assert result["major_behind"] == 2
        assert result["is_outdated"] is True

    def test_minor_version_behind(self):
        """Test detection of minor version differences."""
        result = calculate_version_delta("1.0.0", "1.5.0")
        assert result["major_behind"] == 0
        assert result["minor_behind"] == 5
        assert result["is_outdated"] is True

    def test_patch_version_behind(self):
        """Test detection of patch version differences."""
        result = calculate_version_delta("1.0.0", "1.0.3")
        assert result["major_behind"] == 0
        assert result["minor_behind"] == 0
        assert result["patch_behind"] == 3
        assert result["is_outdated"] is True

    def test_same_version(self):
        """Test that same versions are not outdated."""
        result = calculate_version_delta("2.0.0", "2.0.0")
        assert result["is_outdated"] is False
        assert result["major_behind"] == 0
        assert result["minor_behind"] == 0

    def test_newer_version_installed(self):
        """Test when installed version is newer (edge case)."""
        result = calculate_version_delta("3.0.0", "2.0.0")
        assert result["is_outdated"] is False

    def test_invalid_installed_version(self):
        """Test handling of invalid installed version."""
        result = calculate_version_delta("invalid", "2.0.0")
        assert result["major_behind"] == 0
        assert result["is_outdated"] is True  # String comparison fallback

    def test_invalid_latest_version(self):
        """Test handling of invalid latest version."""
        result = calculate_version_delta("2.0.0", "invalid")
        assert result["major_behind"] == 0

    def test_both_invalid_versions(self):
        """Test handling when both versions are invalid."""
        result = calculate_version_delta("invalid", "also-invalid")
        assert result["major_behind"] == 0
        assert result["is_outdated"] is True  # Different strings

    def test_version_with_v_prefix(self):
        """Test handling of version strings with 'v' prefix."""
        result = calculate_version_delta("v1.0.0", "v2.0.0")
        assert result["major_behind"] == 1
        assert result["is_outdated"] is True


class TestDaysSince:
    """Tests for calculate_days_since function."""

    def test_valid_iso_date_with_z(self):
        """Test parsing of ISO date with Z suffix."""
        result = calculate_days_since("2020-01-01T00:00:00Z")
        assert result > 0
        # Should be at least a few years of days
        assert result > 1000

    def test_valid_iso_date_with_offset(self):
        """Test parsing of ISO date with timezone offset."""
        result = calculate_days_since("2020-01-01T00:00:00+00:00")
        assert result > 0

    def test_simple_date_format(self):
        """Test parsing of simple date format."""
        result = calculate_days_since("2020-01-01")
        assert result > 0

    def test_none_date(self):
        """Test handling of None date."""
        result = calculate_days_since(None)
        assert result == 0

    def test_empty_string(self):
        """Test handling of empty string date."""
        result = calculate_days_since("")
        assert result == 0

    def test_invalid_date_format(self):
        """Test handling of invalid date format."""
        result = calculate_days_since("not-a-date")
        assert result == 0


class TestRegistryFetcher:
    """Tests for get_registry_fetcher function."""

    def test_pip_fetcher(self):
        """Test that pip package type returns a fetcher."""
        fetcher = get_registry_fetcher("pip")
        assert fetcher is not None
        assert callable(fetcher)

    def test_poetry_fetcher(self):
        """Test that poetry package type returns PyPI fetcher."""
        fetcher = get_registry_fetcher("poetry")
        assert fetcher is not None

    def test_npm_fetcher(self):
        """Test that npm package type returns a fetcher."""
        fetcher = get_registry_fetcher("npm")
        assert fetcher is not None
        assert callable(fetcher)

    def test_nodejs_fetcher(self):
        """Test that nodejs package type returns npm fetcher."""
        fetcher = get_registry_fetcher("nodejs")
        assert fetcher is not None

    def test_yarn_fetcher(self):
        """Test that yarn package type returns npm fetcher."""
        fetcher = get_registry_fetcher("yarn")
        assert fetcher is not None

    def test_gomod_fetcher(self):
        """Test that gomod package type returns a fetcher."""
        fetcher = get_registry_fetcher("gomod")
        assert fetcher is not None

    def test_nuget_fetcher(self):
        """Test that nuget package type returns a fetcher."""
        fetcher = get_registry_fetcher("nuget")
        assert fetcher is not None
        assert callable(fetcher)

    def test_dotnet_deps_fetcher(self):
        """Test that dotnet-deps package type returns NuGet fetcher."""
        fetcher = get_registry_fetcher("dotnet-deps")
        assert fetcher is not None

    def test_packages_config_fetcher(self):
        """Test that packages-config package type returns NuGet fetcher."""
        fetcher = get_registry_fetcher("packages-config")
        assert fetcher is not None

    def test_pom_fetcher(self):
        """Test that pom package type returns Maven fetcher."""
        fetcher = get_registry_fetcher("pom")
        assert fetcher is not None
        assert callable(fetcher)

    def test_gradle_lockfile_fetcher(self):
        """Test that gradle-lockfile package type returns Maven fetcher."""
        fetcher = get_registry_fetcher("gradle-lockfile")
        assert fetcher is not None

    def test_jar_fetcher(self):
        """Test that jar package type returns Maven fetcher."""
        fetcher = get_registry_fetcher("jar")
        assert fetcher is not None

    def test_unknown_fetcher(self):
        """Test that unknown package type returns None."""
        fetcher = get_registry_fetcher("unknown")
        assert fetcher is None

    def test_rust_fetcher_not_supported(self):
        """Test that rust/cargo is not yet supported."""
        fetcher = get_registry_fetcher("cargo")
        assert fetcher is None

    def test_case_insensitive(self):
        """Test that package type lookup is case-insensitive."""
        fetcher = get_registry_fetcher("PIP")
        assert fetcher is not None

        fetcher = get_registry_fetcher("NPM")
        assert fetcher is not None

        fetcher = get_registry_fetcher("NUGET")
        assert fetcher is not None

        fetcher = get_registry_fetcher("POM")
        assert fetcher is not None
