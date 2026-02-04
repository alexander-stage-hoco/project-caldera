"""Unit tests for coverage checks module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.coverage import run_coverage_checks
from checks import CheckCategory


class TestCoverageChecks:
    """Tests for run_coverage_checks function."""

    def test_cv1_csharp_coverage(self) -> None:
        """CV-1: C# coverage check."""
        analysis = {
            "files": [
                {"path": "test.cs", "language": "csharp", "issues": [{"dd_category": "sql_injection"}]}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv1 = next((r for r in results if r.check_id == "CV-1"), None)
        assert cv1 is not None
        assert cv1.category == CheckCategory.COVERAGE

    def test_cv2_python_coverage(self) -> None:
        """CV-2: Python coverage check."""
        analysis = {
            "files": [
                {"path": "test.py", "language": "python", "issues": [{"dd_category": "hardcoded_secret"}]}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv2 = next((r for r in results if r.check_id == "CV-2"), None)
        assert cv2 is not None

    def test_cv3_javascript_coverage(self) -> None:
        """CV-3: JavaScript coverage check."""
        analysis = {
            "files": [
                {"path": "test.js", "language": "javascript", "issues": [{"dd_category": "xss"}]}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv3 = next((r for r in results if r.check_id == "CV-3"), None)
        assert cv3 is not None

    def test_cv4_java_coverage(self) -> None:
        """CV-4: Java coverage check."""
        analysis = {
            "files": [
                {"path": "Test.java", "language": "java", "issues": []}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv4 = next((r for r in results if r.check_id == "CV-4"), None)
        assert cv4 is not None

    def test_cv5_go_coverage(self) -> None:
        """CV-5: Go coverage check."""
        analysis = {
            "files": [
                {"path": "main.go", "language": "go", "issues": []}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv5 = next((r for r in results if r.check_id == "CV-5"), None)
        assert cv5 is not None

    def test_cv6_cpp_coverage(self) -> None:
        """CV-6: C/C++ coverage check."""
        analysis = {
            "files": [
                {"path": "main.cpp", "language": "cpp", "issues": []}
            ]
        }
        results = run_coverage_checks(analysis)
        
        cv6 = next((r for r in results if r.check_id == "CV-6"), None)
        assert cv6 is not None

    def test_cv7_multi_language_support(self) -> None:
        """CV-7: Multi-language support check - requires all 7 target languages."""
        analysis = {
            "files": [
                {"path": "test.cs", "language": "csharp", "issues": []},
                {"path": "test.py", "language": "python", "issues": []},
                {"path": "test.js", "language": "javascript", "issues": []},
                {"path": "Test.java", "language": "java", "issues": []},
                {"path": "main.go", "language": "go", "issues": []},
                {"path": "main.c", "language": "c", "issues": []},
                {"path": "main.cpp", "language": "cpp", "issues": []},
            ]
        }
        results = run_coverage_checks(analysis)

        cv7 = next((r for r in results if r.check_id == "CV-7"), None)
        assert cv7 is not None
        assert cv7.passed is True
        assert cv7.evidence["count"] >= 7

    def test_cv8_security_category_coverage(self) -> None:
        """CV-8: DD security category coverage check."""
        analysis = {
            "summary": {"issues_by_category": {
                "sql_injection": 1,
                "hardcoded_secret": 1,
                "insecure_crypto": 1
            }},
            "files": []
        }
        results = run_coverage_checks(analysis)
        
        cv8 = next((r for r in results if r.check_id == "CV-8"), None)
        assert cv8 is not None
        assert cv8.passed is True

    def test_all_coverage_checks_returned(self) -> None:
        """All 8 coverage checks should be returned."""
        analysis = {"files": [], "summary": {"issues_by_category": {}}}
        results = run_coverage_checks(analysis)
        
        assert len(results) == 8
        check_ids = {r.check_id for r in results}
        expected_ids = {f"CV-{i}" for i in range(1, 9)}
        assert check_ids == expected_ids

    def test_language_with_issues_gets_higher_score(self) -> None:
        """Language with detected issues should score higher than empty."""
        analysis_with_issues = {
            "files": [
                {"path": "test.cs", "language": "csharp", "issues": [
                    {"dd_category": "sql_injection"},
                    {"dd_category": "insecure_crypto"}
                ]}
            ]
        }
        analysis_without_issues = {
            "files": [
                {"path": "test.cs", "language": "csharp", "issues": []}
            ]
        }
        
        results_with = run_coverage_checks(analysis_with_issues)
        results_without = run_coverage_checks(analysis_without_issues)
        
        cv1_with = next(r for r in results_with if r.check_id == "CV-1")
        cv1_without = next(r for r in results_without if r.check_id == "CV-1")
        
        assert cv1_with.score >= cv1_without.score

    def test_empty_analysis_handles_gracefully(self) -> None:
        """Empty analysis should not raise errors."""
        analysis = {}
        results = run_coverage_checks(analysis)
        
        assert len(results) == 8
        for r in results:
            assert r.category == CheckCategory.COVERAGE
