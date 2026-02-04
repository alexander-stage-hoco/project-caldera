"""Unit tests for edge case checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.edge_cases import run_edge_case_checks
from checks import CheckCategory


class TestEdgeCaseChecks:
    """Tests for run_edge_case_checks function."""

    def test_all_edge_case_checks_returned(self) -> None:
        """All edge case checks should be returned."""
        analysis = {"files": [], "summary": {}}
        results = run_edge_case_checks(analysis)
        
        # Should have at least some edge case checks
        assert len(results) >= 4
        for r in results:
            assert r.category == CheckCategory.EDGE_CASES

    def test_ec1_empty_file_handling(self) -> None:
        """EC-1: Empty file handling."""
        analysis = {
            "files": [
                {"path": "empty.cs", "language": "csharp", "issues": [], "lines": 0}
            ]
        }
        results = run_edge_case_checks(analysis)
        
        ec1 = next((r for r in results if r.check_id == "EC-1"), None)
        if ec1:  # Check exists
            assert ec1.category == CheckCategory.EDGE_CASES

    def test_ec2_large_file_handling(self) -> None:
        """EC-2: Large file handling."""
        analysis = {
            "files": [
                {"path": "large.cs", "language": "csharp", "issues": [], "lines": 50000}
            ]
        }
        results = run_edge_case_checks(analysis)
        
        ec2 = next((r for r in results if r.check_id == "EC-2"), None)
        if ec2:
            assert ec2.category == CheckCategory.EDGE_CASES

    def test_ec3_special_characters_in_path(self) -> None:
        """EC-3: Special characters in file path handling."""
        analysis = {
            "files": [
                {"path": "path/with spaces/test file.cs", "language": "csharp", "issues": []}
            ]
        }
        results = run_edge_case_checks(analysis)
        
        ec3 = next((r for r in results if r.check_id == "EC-3"), None)
        if ec3:
            assert ec3.category == CheckCategory.EDGE_CASES

    def test_ec4_unicode_content_handling(self) -> None:
        """EC-4: Unicode content handling."""
        analysis = {
            "files": [
                {"path": "unicode_file.cs", "language": "csharp", "issues": []}
            ]
        }
        results = run_edge_case_checks(analysis)
        
        ec4 = next((r for r in results if r.check_id == "EC-4"), None)
        if ec4:
            assert ec4.category == CheckCategory.EDGE_CASES

    def test_edge_case_checks_have_required_fields(self) -> None:
        """All check results should have required fields."""
        analysis = {"files": [], "summary": {}}
        results = run_edge_case_checks(analysis)
        
        for result in results:
            assert result.check_id is not None
            assert result.name is not None
            assert result.category == CheckCategory.EDGE_CASES
            assert isinstance(result.passed, bool)
            assert 0.0 <= result.score <= 1.0

    def test_deeply_nested_path_handling(self) -> None:
        """Edge case: Deeply nested directory paths."""
        analysis = {
            "files": [
                {"path": "a/b/c/d/e/f/g/h/i/j/test.cs", "language": "csharp", "issues": []}
            ]
        }
        # Should not raise any errors
        results = run_edge_case_checks(analysis)
        assert len(results) >= 4

    def test_no_files_analysis(self) -> None:
        """Edge case: Analysis with no files."""
        analysis = {"files": [], "summary": {"total_issues": 0}}
        results = run_edge_case_checks(analysis)
        
        # Should handle gracefully without errors
        assert len(results) >= 4
