"""Pytest configuration for DevSkim tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add devskim tool directory to path so 'scripts' can be imported as a package
# This allows both direct imports (from security_analyzer) and package imports (from scripts.analyze)
devskim_root = Path(__file__).parent.parent
sys.path.insert(0, str(devskim_root))
sys.path.insert(0, str(devskim_root / "scripts"))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require DevSkim binary)"
    )


@pytest.fixture
def mock_analysis_result():
    """Create a mock AnalysisResult for testing."""
    from security_analyzer import (
        AnalysisResult,
        FileStats,
        SecurityFinding,
        DirectoryEntry,
        DirectoryStats,
        LanguageStats,
    )

    finding = SecurityFinding(
        rule_id="DS126858",
        dd_category="insecure_crypto",
        cwe_ids=["CWE-328"],
        file_path="src/Crypto.cs",
        line_start=10,
        line_end=10,
        column_start=5,
        column_end=30,
        severity="HIGH",
        message="Weak hash algorithm MD5",
        code_snippet="var hash = MD5.Create();",
    )

    file_stats = FileStats(
        path="src/Crypto.cs",
        language="csharp",
        lines=150,
        issue_count=1,
        issue_density=0.67,
        by_category={"insecure_crypto": 1},
        by_severity={"HIGH": 1},
        issues=[finding],
    )

    dir_stats_direct = DirectoryStats(
        file_count=1,
        lines_code=150,
        issue_count=1,
        by_category={"insecure_crypto": 1},
        by_severity={"HIGH": 1},
        issue_density=0.67,
    )

    dir_entry = DirectoryEntry(
        path="src",
        name="src",
        depth=1,
        is_leaf=True,
        child_count=1,
        subdirectories=[],
        direct=dir_stats_direct,
        recursive=dir_stats_direct,
    )

    lang_stats = LanguageStats(
        files=1,
        lines=150,
        issue_count=1,
        categories_covered={"insecure_crypto"},
    )

    return AnalysisResult(
        generated_at="2026-01-22T00:00:00Z",
        repo_name="test-repo",
        repo_path="/tmp/test-repo",
        run_id="test-run-123",
        timestamp="2026-01-22T00:00:00Z",
        devskim_version="1.0.28",
        rules_used=["DS126858"],
        analysis_duration_ms=500,
        directories=[dir_entry],
        files=[file_stats],
        findings=[finding],
        by_language={"csharp": lang_stats},
        by_category={"insecure_crypto": 1},
        by_severity={"HIGH": 1},
    )


@pytest.fixture
def mock_evaluation_report():
    """Create a mock EvaluationReport for testing."""
    from checks import CheckResult, CheckCategory, EvaluationReport

    checks = [
        CheckResult(
            check_id="AC-1",
            name="SQL injection detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="Detected 3/3 SQL injection issues",
        ),
        CheckResult(
            check_id="AC-2",
            name="Hardcoded secret detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="Detected 2/2 hardcoded secrets",
        ),
        CheckResult(
            check_id="CV-1",
            name="Language coverage",
            category=CheckCategory.COVERAGE,
            passed=True,
            score=1.0,
            message="5/5 languages covered",
        ),
        CheckResult(
            check_id="PF-1",
            name="Analysis speed",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.5,
            message="Analysis took 2000ms (expected < 1000ms)",
        ),
    ]

    return EvaluationReport(
        timestamp="2026-01-22T00:00:00Z",
        analysis_path="/tmp/analysis.json",
        ground_truth_dir="/tmp/ground-truth",
        checks=checks,
    )


@pytest.fixture
def empty_analysis_result():
    """Create an empty AnalysisResult for testing edge cases."""
    from security_analyzer import AnalysisResult

    return AnalysisResult(
        generated_at="2026-01-22T00:00:00Z",
        repo_name="empty-repo",
        repo_path="/tmp/empty-repo",
    )
