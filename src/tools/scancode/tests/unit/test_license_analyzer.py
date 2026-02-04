"""Unit tests for license_analyzer.py core functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from license_analyzer import (
    LICENSE_PATTERNS,
    LICENSE_CATEGORIES,
    CATEGORY_RISK,
    LicenseFinding,
    FileSummary,
    DirectoryStats,
    LicenseAnalysis,
    get_category,
    detect_license_in_content,
    analyze_repository,
)


class TestLicensePatterns:
    """Tests for license pattern matching."""

    def test_mit_license_full_text_detection(self):
        """MIT license full text should be detected."""
        content = """MIT License

        Copyright (c) 2025 Example

        Permission is hereby granted, free of charge, to any person obtaining a copy
        """
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "MIT"
        assert findings[0].category == "permissive"

    def test_mit_license_spdx_header_detection(self):
        """SPDX MIT header should be detected with high confidence."""
        content = "# SPDX-License-Identifier: MIT"
        findings = detect_license_in_content(content, "main.py")
        assert len(findings) == 1
        assert findings[0].spdx_id == "MIT"
        assert findings[0].match_type == "spdx"
        assert findings[0].confidence == 0.95

    def test_apache_license_detection(self):
        """Apache 2.0 license should be detected."""
        content = "Licensed under the Apache License, Version 2.0"
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "Apache-2.0"
        assert findings[0].category == "permissive"

    def test_gpl3_license_detection(self):
        """GPL-3.0 license should be detected as copyleft."""
        content = """GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007
        """
        findings = detect_license_in_content(content, "COPYING")
        assert len(findings) == 1
        assert findings[0].spdx_id == "GPL-3.0-only"
        assert findings[0].category == "copyleft"

    def test_gpl2_license_detection(self):
        """GPL-2.0 license should be detected (not confused with 2.1)."""
        content = """GNU GENERAL PUBLIC LICENSE
                       Version 2, June 1991
        """
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "GPL-2.0-only"
        assert findings[0].category == "copyleft"

    def test_lgpl_21_detection(self):
        """LGPL-2.1 should be detected as weak-copyleft."""
        content = "GNU LESSER GENERAL PUBLIC LICENSE Version 2.1"
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "LGPL-2.1-only"
        assert findings[0].category == "weak-copyleft"

    def test_lgpl_30_spdx_detection(self):
        """LGPL-3.0 SPDX header should be detected."""
        content = "// SPDX-License-Identifier: LGPL-3.0-only"
        findings = detect_license_in_content(content, "lib.c")
        assert len(findings) == 1
        assert findings[0].spdx_id == "LGPL-3.0-only"
        assert findings[0].category == "weak-copyleft"

    def test_bsd_3_clause_detection(self):
        """BSD 3-Clause license should be detected."""
        content = "BSD 3-Clause License"
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "BSD-3-Clause"
        assert findings[0].category == "permissive"

    def test_bsd_redistribution_pattern_detection(self):
        """BSD redistribution clause should trigger BSD-3-Clause."""
        content = "Redistributions of source code must retain the above copyright"
        findings = detect_license_in_content(content, "LICENSE.txt")
        assert len(findings) == 1
        assert findings[0].spdx_id == "BSD-3-Clause"

    def test_bsd_2_clause_spdx_detection(self):
        """BSD-2-Clause SPDX header should be detected."""
        content = "/* SPDX-License-Identifier: BSD-2-Clause */"
        findings = detect_license_in_content(content, "module.c")
        assert len(findings) == 1
        assert findings[0].spdx_id == "BSD-2-Clause"

    def test_isc_license_detection(self):
        """ISC license should be detected."""
        content = "ISC License\n\nCopyright..."
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "ISC"
        assert findings[0].category == "permissive"

    def test_mpl_20_detection(self):
        """Mozilla Public License 2.0 should be detected as weak-copyleft."""
        content = "Mozilla Public License Version 2.0"
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "MPL-2.0"
        assert findings[0].category == "weak-copyleft"

    def test_agpl_30_detection(self):
        """AGPL-3.0 should be detected as copyleft."""
        content = "GNU AFFERO GENERAL PUBLIC LICENSE Version 3"
        findings = detect_license_in_content(content, "LICENSE")
        assert len(findings) == 1
        assert findings[0].spdx_id == "AGPL-3.0-only"
        assert findings[0].category == "copyleft"

    def test_no_license_returns_empty(self):
        """Content without any license should return empty findings."""
        content = "This is a README file with no license information."
        findings = detect_license_in_content(content, "README.md")
        assert findings == []

    def test_multiple_licenses_not_duplicated(self):
        """Each license type should only be detected once per file."""
        content = """MIT License

        Permission is hereby granted, free of charge

        MIT License (again)
        """
        findings = detect_license_in_content(content, "LICENSE")
        # Should only detect MIT once despite multiple matches
        mit_findings = [f for f in findings if f.spdx_id == "MIT"]
        assert len(mit_findings) == 1


class TestMatchTypeAndConfidence:
    """Tests for match type classification and confidence scoring."""

    def test_license_file_match_type(self):
        """License file should have 'file' match type and 0.90 confidence."""
        content = "MIT License"
        findings = detect_license_in_content(content, "LICENSE")
        assert findings[0].match_type == "file"
        assert findings[0].confidence == 0.90

    def test_copying_file_match_type(self):
        """COPYING file should have 'file' match type."""
        content = "MIT License"
        findings = detect_license_in_content(content, "COPYING")
        assert findings[0].match_type == "file"
        assert findings[0].confidence == 0.90

    def test_spdx_header_match_type(self):
        """SPDX identifier should have 'spdx' match type and 0.95 confidence."""
        content = "// SPDX-License-Identifier: Apache-2.0"
        findings = detect_license_in_content(content, "main.go")
        assert findings[0].match_type == "spdx"
        assert findings[0].confidence == 0.95

    def test_header_match_type(self):
        """Non-license, non-SPDX file should have 'header' match type."""
        content = "MIT License"
        findings = detect_license_in_content(content, "README.md")
        assert findings[0].match_type == "header"
        assert findings[0].confidence == 0.80

    def test_line_number_tracking(self):
        """Line number should be correctly tracked."""
        content = """Some header text

// SPDX-License-Identifier: MIT
"""
        findings = detect_license_in_content(content, "main.py")
        assert findings[0].line_number == 3


class TestGetCategory:
    """Tests for get_category function."""

    def test_permissive_licenses(self):
        """All permissive licenses should return 'permissive'."""
        for license_id in LICENSE_CATEGORIES["permissive"]:
            assert get_category(license_id) == "permissive"

    def test_weak_copyleft_licenses(self):
        """All weak-copyleft licenses should return 'weak-copyleft'."""
        for license_id in LICENSE_CATEGORIES["weak-copyleft"]:
            assert get_category(license_id) == "weak-copyleft"

    def test_copyleft_licenses(self):
        """All copyleft licenses should return 'copyleft'."""
        for license_id in LICENSE_CATEGORIES["copyleft"]:
            assert get_category(license_id) == "copyleft"

    def test_unknown_license(self):
        """Unknown license ID should return 'unknown'."""
        assert get_category("Unknown-License-1.0") == "unknown"
        assert get_category("Proprietary") == "unknown"


class TestCategoryRisk:
    """Tests for category to risk mapping."""

    def test_permissive_is_low_risk(self):
        """Permissive category should be low risk."""
        assert CATEGORY_RISK["permissive"] == "low"

    def test_weak_copyleft_is_medium_risk(self):
        """Weak-copyleft category should be medium risk."""
        assert CATEGORY_RISK["weak-copyleft"] == "medium"

    def test_copyleft_is_critical_risk(self):
        """Copyleft category should be critical risk."""
        assert CATEGORY_RISK["copyleft"] == "critical"

    def test_unknown_is_high_risk(self):
        """Unknown category should be high risk."""
        assert CATEGORY_RISK["unknown"] == "high"


class TestLicenseAnalysisDataclass:
    """Tests for LicenseAnalysis dataclass and serialization."""

    def test_default_values(self):
        """LicenseAnalysis should have sensible defaults."""
        analysis = LicenseAnalysis()
        assert analysis.schema_version == "1.0.0"
        assert analysis.tool == "scancode"
        assert analysis.total_files_scanned == 0
        assert analysis.licenses_found == []
        assert analysis.overall_risk == "unknown"

    def test_to_dict_structure(self):
        """to_dict should return correct nested structure."""
        analysis = LicenseAnalysis(
            repo_name="test-repo",
            repo_path="/path/to/repo",
            generated_at="2025-01-01T00:00:00Z",
            total_files_scanned=10,
            files_with_licenses=2,
            licenses_found=["MIT"],
            license_counts={"MIT": 2},
            has_permissive=True,
            overall_risk="low",
        )
        result = analysis.to_dict()

        # Check root level fields
        assert result["schema_version"] == "1.0.0"
        assert result["repo_name"] == "test-repo"
        assert result["repo_path"] == "/path/to/repo"
        assert result["generated_at"] == "2025-01-01T00:00:00Z"

        # Check results nested object
        assert "results" in result
        assert result["results"]["tool"] == "scancode"
        assert result["results"]["total_files_scanned"] == 10
        assert result["results"]["licenses_found"] == ["MIT"]
        assert result["results"]["overall_risk"] == "low"

    def test_findings_serialization(self):
        """Findings should be serialized to dicts."""
        finding = LicenseFinding(
            file_path="LICENSE",
            spdx_id="MIT",
            category="permissive",
            confidence=0.90,
            match_type="file",
            line_number=1,
        )
        analysis = LicenseAnalysis(findings=[finding])
        result = analysis.to_dict()

        assert len(result["results"]["findings"]) == 1
        assert result["results"]["findings"][0]["spdx_id"] == "MIT"
        assert result["results"]["findings"][0]["confidence"] == 0.90

    def test_file_summaries_serialization(self):
        """File summaries should be serialized to dicts."""
        summary = FileSummary(
            file_path="LICENSE",
            licenses=["MIT"],
            category="permissive",
            has_spdx_header=False,
        )
        analysis = LicenseAnalysis(files={"LICENSE": summary})
        result = analysis.to_dict()

        assert "LICENSE" in result["results"]["files"]
        assert result["results"]["files"]["LICENSE"]["licenses"] == ["MIT"]


class TestAnalyzeRepository:
    """Tests for analyze_repository function."""

    def test_analyze_empty_repo(self):
        """Empty repository should return high risk (no license)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            # Create empty directory structure
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')")

            analysis = analyze_repository(repo_path)

            assert analysis.overall_risk == "high"
            assert analysis.has_unknown is True
            assert "No license found" in analysis.risk_reasons[0]

    def test_analyze_mit_only_repo(self):
        """Repository with only MIT license should return low risk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("MIT License\n\nPermission is hereby granted, free of charge")
            (repo_path / "main.py").write_text("# SPDX-License-Identifier: MIT\nprint('hello')")

            analysis = analyze_repository(repo_path)

            assert analysis.overall_risk == "low"
            assert analysis.has_permissive is True
            assert analysis.has_copyleft is False
            assert "MIT" in analysis.licenses_found

    def test_analyze_gpl_repo(self):
        """Repository with GPL license should return critical risk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "COPYING").write_text("GNU GENERAL PUBLIC LICENSE Version 3")
            (repo_path / "lib.c").write_text("// SPDX-License-Identifier: GPL-3.0-only\nint main() {}")

            analysis = analyze_repository(repo_path)

            assert analysis.overall_risk == "critical"
            assert analysis.has_copyleft is True
            assert "GPL-3.0-only" in analysis.licenses_found
            assert "Copyleft license" in analysis.risk_reasons[0]

    def test_analyze_weak_copyleft_repo(self):
        """Repository with LGPL should return medium risk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("GNU LESSER GENERAL PUBLIC LICENSE Version 2.1")

            analysis = analyze_repository(repo_path)

            assert analysis.overall_risk == "medium"
            assert analysis.has_weak_copyleft is True
            assert "Weak copyleft" in analysis.risk_reasons[0]

    def test_analyze_counts_license_files(self):
        """License file count should be tracked."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("MIT License")
            (repo_path / "LICENSE.txt").write_text("MIT License")

            analysis = analyze_repository(repo_path)

            assert analysis.license_files_found >= 2

    def test_analyze_scan_time_recorded(self):
        """Scan time should be recorded and positive."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("MIT License")

            analysis = analyze_repository(repo_path)

            assert analysis.scan_time_ms > 0

    def test_analyze_file_summaries_generated(self):
        """File summaries should be generated for files with licenses."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("MIT License")

            analysis = analyze_repository(repo_path)

            assert len(analysis.files) >= 1
            license_summary = analysis.files.get("LICENSE")
            assert license_summary is not None
            assert "MIT" in license_summary.licenses

    def test_analyze_multiple_source_extensions(self):
        """Multiple source file extensions should be scanned."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir)
            (repo_path / "LICENSE").write_text("MIT License")
            (repo_path / "main.py").write_text("# SPDX-License-Identifier: MIT")
            (repo_path / "app.js").write_text("// SPDX-License-Identifier: MIT")
            (repo_path / "lib.go").write_text("// SPDX-License-Identifier: MIT")

            analysis = analyze_repository(repo_path)

            assert analysis.total_files_scanned >= 3
            assert analysis.files_with_licenses >= 3


class TestDirectoryStatsDataclass:
    """Tests for DirectoryStats dataclass."""

    def test_default_values(self):
        """DirectoryStats should have sensible defaults."""
        stats = DirectoryStats()
        assert stats.file_count == 0
        assert stats.files_with_licenses == 0
        assert stats.license_counts == {}
        assert stats.has_copyleft is False
        assert stats.worst_risk == "unknown"

    def test_with_values(self):
        """DirectoryStats should store provided values."""
        stats = DirectoryStats(
            file_count=10,
            files_with_licenses=5,
            license_counts={"MIT": 3, "Apache-2.0": 2},
            has_permissive=True,
            worst_risk="low",
        )
        assert stats.file_count == 10
        assert stats.license_counts["MIT"] == 3
        assert stats.worst_risk == "low"


class TestFileSummaryDataclass:
    """Tests for FileSummary dataclass."""

    def test_file_summary_creation(self):
        """FileSummary should store file-level license data."""
        summary = FileSummary(
            file_path="src/main.py",
            licenses=["MIT", "Apache-2.0"],
            category="permissive",
            has_spdx_header=True,
        )
        assert summary.file_path == "src/main.py"
        assert "MIT" in summary.licenses
        assert summary.has_spdx_header is True


class TestLicenseFindingDataclass:
    """Tests for LicenseFinding dataclass."""

    def test_license_finding_creation(self):
        """LicenseFinding should store detection data."""
        finding = LicenseFinding(
            file_path="LICENSE",
            spdx_id="MIT",
            category="permissive",
            confidence=0.95,
            match_type="spdx",
            line_number=1,
        )
        assert finding.file_path == "LICENSE"
        assert finding.spdx_id == "MIT"
        assert finding.confidence == 0.95

    def test_default_line_number(self):
        """Line number should default to 0."""
        finding = LicenseFinding(
            file_path="LICENSE",
            spdx_id="MIT",
            category="permissive",
            confidence=0.90,
            match_type="file",
        )
        assert finding.line_number == 0
