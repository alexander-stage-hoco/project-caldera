"""Pytest configuration for Trivy tests."""

import pytest


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


@pytest.fixture
def temp_dir(tmp_path):
    """Alias for tmp_path fixture for backwards compatibility."""
    return tmp_path


@pytest.fixture
def sample_normalized_analysis():
    """Sample normalized trivy analysis output for detection tests.

    This fixture provides a complete analysis output that matches the expected
    schema for all check modules:
    - detection: vulnerabilities, summary, targets
    - output_quality: schema_version, repository, timestamp, tool, etc.
    - integration: directories, sbom, iac_misconfigurations, age_days
    """
    return {
        # Root-level fields for output quality checks
        "schema_version": "1.0.0",
        "repository": "test-repo",
        "timestamp": "2026-01-15T10:00:00Z",
        "tool": "trivy",
        "tool_version": "0.58.0",
        # Vulnerability data for detection checks
        "vulnerabilities": [
            {
                "id": "CVE-2021-0001",
                "severity": "CRITICAL",
                "package": "lodash",
                "installed_version": "4.17.20",
                "fix_available": True,
                "target": "package.json",
                "age_days": 365,
            },
            {
                "id": "CVE-2021-0002",
                "severity": "HIGH",
                "package": "express",
                "installed_version": "4.17.0",
                "fix_available": True,
                "target": "package.json",
                "age_days": 180,
            },
            {
                "id": "CVE-2021-0003",
                "severity": "MEDIUM",
                "package": "minimist",
                "installed_version": "1.2.0",
                "fix_available": False,
                "target": "package.json",
                "age_days": 90,
            },
        ],
        # Summary with all required fields for output quality checks
        "summary": {
            "total_count": 3,
            "total_vulnerabilities": 3,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0,
            "fix_available_count": 2,
            "fix_available_pct": 66.67,
            "dependency_count": 10,
            "oldest_cve_days": 365,
            "targets_scanned": 2,
        },
        "targets": [
            {"path": "requirements.txt", "type": "pip"},
            {"path": "package.json", "type": "npm"},
        ],
        # IaC misconfigurations for integration checks
        "iac_misconfigurations": {
            "total_count": 2,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 0,
            "low_count": 0,
            "misconfigurations": [
                {
                    "id": "DS002",
                    "target": "Dockerfile",
                    "severity": "CRITICAL",
                    "title": "Run as root",
                    "resolution": "Use USER directive to specify non-root user",
                },
                {
                    "id": "KSV001",
                    "target": "deployment.yaml",
                    "severity": "HIGH",
                    "title": "Privileged container",
                    "resolution": "Set securityContext.privileged to false",
                },
            ],
        },
        # Directory rollups for integration checks
        "directories": {
            "directory_count": 2,
            "directories": [
                {
                    "path": ".",
                    "direct": {"vulnerability_count": 1, "critical_count": 0},
                    "recursive": {"vulnerability_count": 3, "critical_count": 1},
                },
                {
                    "path": "src",
                    "direct": {"vulnerability_count": 2, "critical_count": 1},
                    "recursive": {"vulnerability_count": 2, "critical_count": 1},
                },
            ],
        },
        # SBOM for integration checks
        "sbom": {
            "format": "trivy-json",
            "total_packages": 10,
            "vulnerable_packages": 3,
            "clean_packages": 7,
        },
    }


@pytest.fixture
def sample_ground_truth_flat():
    """Sample ground truth for detection tests."""
    return {
        "required_cves": ["CVE-2021-0001", "CVE-2021-0002"],
        "expected_critical": {"min": 1, "max": 5},
        "expected_high": {"min": 0, "max": 10},
        "expected_targets": {"min": 1, "max": 5},
        "expected_fix_available_pct": {"min": 50, "max": 100},
    }


@pytest.fixture
def sample_freshness_analysis():
    """Sample analysis output with freshness data."""
    return {
        "freshness": {
            "checked": True,
            "total_packages": 5,
            "outdated_count": 2,
            "packages": [
                {
                    "package": "requests",
                    "current_version": "2.25.0",
                    "latest_version": "2.28.0",
                    "major_versions_behind": 0,
                    "minor_versions_behind": 3,
                    "patch_versions_behind": 0,
                    "is_outdated": True,
                    "package_type": "pip",
                },
                {
                    "package": "flask",
                    "current_version": "2.0.0",
                    "latest_version": "2.0.0",
                    "major_versions_behind": 0,
                    "minor_versions_behind": 0,
                    "patch_versions_behind": 0,
                    "is_outdated": False,
                    "package_type": "pip",
                },
            ],
        },
        "targets": [{"type": "pip"}],
    }


@pytest.fixture
def sample_trivy_raw_output():
    """Sample raw Trivy JSON output for parse_trivy_output tests.

    This fixture mimics the actual output from running `trivy fs --format json`.
    """
    return {
        "SchemaVersion": 2,
        "Results": [
            {
                "Target": "requirements.txt",
                "Class": "lang-pkgs",
                "Type": "pip",
                "Packages": [
                    {"Name": "requests", "Version": "2.28.0"},
                    {"Name": "urllib3", "Version": "1.26.0"},
                    {"Name": "pyyaml", "Version": "5.3"},
                ],
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2021-33503",
                        "PkgName": "urllib3",
                        "InstalledVersion": "1.26.0",
                        "FixedVersion": "1.26.5",
                        "Severity": "HIGH",
                        "Title": "ReDoS vulnerability in urllib3",
                        "Description": "Regular expression denial of service",
                        "PublishedDate": "2021-06-29T11:15:07Z",
                        "CVSS": {
                            "nvd": {"V3Score": 7.5, "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"}
                        },
                    },
                    {
                        "VulnerabilityID": "CVE-2020-14343",
                        "PkgName": "pyyaml",
                        "InstalledVersion": "5.3",
                        "FixedVersion": "5.4",
                        "Severity": "CRITICAL",
                        "Title": "Arbitrary code execution in PyYAML",
                        "Description": "Critical YAML vulnerability",
                        "PublishedDate": "2021-02-09T21:15:12Z",
                        "CVSS": {
                            "nvd": {"V3Score": 9.8}
                        },
                    },
                ],
            },
            {
                "Target": "Dockerfile",
                "Class": "config",
                "Type": "dockerfile",
                "Misconfigurations": [
                    {
                        "ID": "DS002",
                        "Severity": "HIGH",
                        "Title": "Root user",
                        "Description": "Running container as root",
                        "Resolution": "Use USER instruction",
                        "CauseMetadata": {
                            "StartLine": 1,
                            "EndLine": 5,
                        },
                    },
                ],
            },
        ],
    }


@pytest.fixture
def sample_iac_analysis():
    """Sample analysis output with IaC misconfiguration data."""
    return {
        "iac_misconfigurations": {
            "total_count": 3,
            "critical_count": 1,
            "high_count": 1,
            "medium_count": 1,
            "low_count": 0,
            "misconfigurations": [
                {
                    "id": "DS002",
                    "target": "Dockerfile",
                    "severity": "CRITICAL",
                    "title": "Run as root",
                    "message": "Running as root user",
                    "resolution": "Use USER directive to specify a non-root user",
                },
                {
                    "id": "KSV001",
                    "target": "deployment.yaml",
                    "severity": "HIGH",
                    "title": "Privileged container",
                    "message": "Container running in privileged mode",
                    "resolution": "Set securityContext.privileged to false",
                },
                {
                    "id": "KSV003",
                    "target": "service.yaml",
                    "severity": "MEDIUM",
                    "title": "Capabilities not dropped",
                    "message": "Container capabilities not dropped",
                    "resolution": "Drop all capabilities and add only required ones",
                },
            ],
        },
    }
