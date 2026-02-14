"""
Tests for accuracy checks (AC-1 to AC-10).

Tests cover:
- SQL injection detection recall (AC-1)
- XSS detection with analyzer limitation bypass (AC-2)
- Hardcoded secrets detection with analyzer limitation bypass (AC-3)
- Weak crypto detection recall (AC-4)
- Insecure deserialization detection (AC-5)
- Resource disposal detection across multiple files (AC-6)
- Dead code detection with skipped files (AC-7)
- Design violation detection (AC-8)
- Overall precision via false positive rate (AC-9)
- Overall recall (AC-10)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.accuracy import (
    ac1_sql_injection_detection,
    ac2_xss_detection,
    ac3_hardcoded_secrets_detection,
    ac4_weak_crypto_detection,
    ac5_insecure_deserialization_detection,
    ac6_resource_disposal_detection,
    ac7_dead_code_detection,
    ac8_design_violation_detection,
    ac9_overall_precision,
    ac10_overall_recall,
    run_all_accuracy_checks,
)


def _make_analysis(files=None, summary=None):
    """Build a minimal analysis dict."""
    return {
        "files": files or [],
        "summary": summary or {"total_violations": 0},
    }


def _make_ground_truth(files=None, summary=None):
    """Build a minimal ground truth dict."""
    return {
        "files": files or {},
        "summary": summary or {"total_expected_violations": 0},
    }


class TestAC1SqlInjection:
    """AC-1: SQL injection detection."""

    def test_perfect_recall(self):
        analysis = _make_analysis(files=[
            {"path": "security/sql_injection.cs", "violations": [
                {"rule_id": "CA3001", "line_start": 15},
                {"rule_id": "CA2100", "line_start": 28},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/sql_injection.cs": {
                "expected_violations": [
                    {"rule_id": "CA3001", "count": 1},
                    {"rule_id": "CA2100", "count": 1},
                ]
            }
        })
        result = ac1_sql_injection_detection(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)
        assert result.check_id == "AC-1"

    def test_partial_recall_below_threshold(self):
        analysis = _make_analysis(files=[
            {"path": "security/sql_injection.cs", "violations": [
                {"rule_id": "CA3001", "line_start": 15},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/sql_injection.cs": {
                "expected_violations": [
                    {"rule_id": "CA3001", "count": 2},
                    {"rule_id": "CA2100", "count": 3},
                ]
            }
        })
        result = ac1_sql_injection_detection(analysis, gt)
        # 1 detected out of 5 expected = 20% recall < 80%
        assert result.passed is False
        assert result.score == pytest.approx(0.2)

    def test_no_ground_truth_file(self):
        """When the target file is missing from ground truth, 0 expected -> recall 1.0."""
        analysis = _make_analysis(files=[])
        gt = _make_ground_truth(files={})
        result = ac1_sql_injection_detection(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)


class TestAC2XSSDetection:
    """AC-2: XSS detection."""

    def test_analyzer_limitation_bypass(self):
        """When analyzer_limitation=True and expected_count=0, check passes."""
        analysis = _make_analysis(files=[
            {"path": "security/xss_vulnerabilities.cs", "violations": []}
        ])
        gt = _make_ground_truth(files={
            "security/xss_vulnerabilities.cs": {
                "expected_violations": [],
                "analyzer_limitation": True,
            }
        })
        result = ac2_xss_detection(analysis, gt)
        assert result.passed is True
        assert result.score == 1.0
        assert "limitation" in result.message.lower()

    def test_normal_detection_passes(self):
        analysis = _make_analysis(files=[
            {"path": "security/xss_vulnerabilities.cs", "violations": [
                {"rule_id": "CA3002", "line_start": 10},
                {"rule_id": "SCS0002", "line_start": 20},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/xss_vulnerabilities.cs": {
                "expected_violations": [
                    {"rule_id": "CA3002", "count": 1},
                    {"rule_id": "SCS0002", "count": 1},
                ]
            }
        })
        result = ac2_xss_detection(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)


class TestAC3HardcodedSecrets:
    """AC-3: Hardcoded secrets detection."""

    def test_analyzer_limitation_bypass(self):
        analysis = _make_analysis(files=[])
        gt = _make_ground_truth(files={
            "security/hardcoded_secrets.cs": {
                "expected_violations": [],
                "analyzer_limitation": True,
            }
        })
        result = ac3_hardcoded_secrets_detection(analysis, gt)
        assert result.passed is True
        assert "limitation" in result.message.lower()

    def test_partial_detection(self):
        analysis = _make_analysis(files=[
            {"path": "security/hardcoded_secrets.cs", "violations": [
                {"rule_id": "SCS0015", "line_start": 5},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/hardcoded_secrets.cs": {
                "expected_violations": [
                    {"rule_id": "CA5390", "count": 1},
                    {"rule_id": "SCS0015", "count": 1},
                ]
            }
        })
        result = ac3_hardcoded_secrets_detection(analysis, gt)
        # 1 out of 2 = 50% < 80%
        assert result.passed is False
        assert result.score == pytest.approx(0.5)


class TestAC4WeakCrypto:
    """AC-4: Weak crypto detection."""

    def test_passes_at_threshold(self):
        analysis = _make_analysis(files=[
            {"path": "security/weak_crypto.cs", "violations": [
                {"rule_id": "CA5350", "line_start": 10},
                {"rule_id": "CA5350", "line_start": 20},
                {"rule_id": "CA5351", "line_start": 30},
                {"rule_id": "CA5351", "line_start": 40},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/weak_crypto.cs": {
                "expected_violations": [
                    {"rule_id": "CA5350", "count": 3},
                    {"rule_id": "CA5351", "count": 2},
                ]
            }
        })
        result = ac4_weak_crypto_detection(analysis, gt)
        # 4/5 = 80% exactly at threshold
        assert result.passed is True
        assert result.score == pytest.approx(0.8)


class TestAC5InsecureDeserialization:
    """AC-5: Insecure deserialization detection."""

    def test_full_detection(self):
        analysis = _make_analysis(files=[
            {"path": "security/insecure_deserialization.cs", "violations": [
                {"rule_id": "CA2300", "line_start": 5},
                {"rule_id": "CA2301", "line_start": 15},
            ]}
        ])
        gt = _make_ground_truth(files={
            "security/insecure_deserialization.cs": {
                "expected_violations": [
                    {"rule_id": "CA2300", "count": 1},
                    {"rule_id": "CA2301", "count": 1},
                ]
            }
        })
        result = ac5_insecure_deserialization_detection(analysis, gt)
        assert result.passed is True
        assert result.check_id == "AC-5"

    def test_no_detection(self):
        analysis = _make_analysis(files=[
            {"path": "security/insecure_deserialization.cs", "violations": []}
        ])
        gt = _make_ground_truth(files={
            "security/insecure_deserialization.cs": {
                "expected_violations": [
                    {"rule_id": "CA2300", "count": 3},
                ]
            }
        })
        result = ac5_insecure_deserialization_detection(analysis, gt)
        assert result.passed is False
        assert result.score == pytest.approx(0.0)


class TestAC6ResourceDisposal:
    """AC-6: Resource disposal detection across multiple files."""

    def test_checks_multiple_files(self):
        analysis = _make_analysis(files=[
            {"path": "resource/undisposed_objects.cs", "violations": [
                {"rule_id": "CA2000", "line_start": 10},
            ]},
            {"path": "resource/missing_idisposable.cs", "violations": [
                {"rule_id": "CA1001", "line_start": 5},
                {"rule_id": "CA1001", "line_start": 20},
            ]},
        ])
        gt = _make_ground_truth(files={
            "resource/undisposed_objects.cs": {
                "expected_violations": [
                    {"rule_id": "CA2000", "count": 1},
                ]
            },
            "resource/missing_idisposable.cs": {
                "expected_violations": [
                    {"rule_id": "CA1001", "count": 2},
                ]
            },
        })
        result = ac6_resource_disposal_detection(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)
        assert result.check_id == "AC-6"


class TestAC7DeadCode:
    """AC-7: Dead code detection with analyzer limitation skipping."""

    def test_skips_files_with_analyzer_limitation(self):
        analysis = _make_analysis(files=[
            {"path": "dead_code/unused_imports.cs", "violations": [
                {"rule_id": "IDE0005", "line_start": 1},
            ]},
        ])
        gt = _make_ground_truth(files={
            "dead_code/unused_imports.cs": {
                "expected_violations": [
                    {"rule_id": "IDE0005", "count": 1},
                ]
            },
            "dead_code/unused_parameters.cs": {
                "analyzer_limitation": True,
                "expected_violations": [
                    {"rule_id": "IDE0060", "count": 5},
                ]
            },
        })
        result = ac7_dead_code_detection(analysis, gt)
        # Only unused_imports.cs is counted; unused_parameters.cs skipped
        assert result.passed is True
        assert "skipped" in result.message

    def test_all_files_active(self):
        analysis = _make_analysis(files=[
            {"path": "dead_code/unused_imports.cs", "violations": [
                {"rule_id": "IDE0005", "line_start": 1},
                {"rule_id": "IDE0005", "line_start": 5},
            ]},
            {"path": "dead_code/unused_parameters.cs", "violations": [
                {"rule_id": "IDE0060", "line_start": 10},
            ]},
        ])
        gt = _make_ground_truth(files={
            "dead_code/unused_imports.cs": {
                "expected_violations": [{"rule_id": "IDE0005", "count": 2}],
            },
            "dead_code/unused_parameters.cs": {
                "expected_violations": [{"rule_id": "IDE0060", "count": 1}],
            },
        })
        result = ac7_dead_code_detection(analysis, gt)
        assert result.passed is True
        assert "skipped" not in result.message


class TestAC8DesignViolation:
    """AC-8: Design violation detection."""

    def test_design_detection(self):
        analysis = _make_analysis(files=[
            {"path": "design/visible_fields.cs", "violations": [
                {"rule_id": "CA1051", "line_start": 10},
                {"rule_id": "CA1051", "line_start": 20},
            ]},
            {"path": "design/empty_interfaces.cs", "violations": [
                {"rule_id": "CA1040", "line_start": 5},
            ]},
        ])
        gt = _make_ground_truth(files={
            "design/visible_fields.cs": {
                "expected_violations": [{"rule_id": "CA1051", "count": 2}],
            },
            "design/empty_interfaces.cs": {
                "expected_violations": [{"rule_id": "CA1040", "count": 1}],
            },
        })
        result = ac8_design_violation_detection(analysis, gt)
        assert result.passed is True
        assert result.check_id == "AC-8"


class TestAC9OverallPrecision:
    """AC-9: Overall precision measured via false positive rate on clean files."""

    def test_no_false_positives_high_precision(self):
        analysis = _make_analysis(
            files=[
                {"file": "src/test.cs", "path": "src/test.cs", "violations": [
                    {"rule_id": "CA3001"}
                ]},
                {"file": "clean/clean_service.cs", "path": "clean/clean_service.cs", "violations": []},
            ],
            summary={"total_violations": 1},
        )
        gt = _make_ground_truth(files={
            "clean/clean_service.cs": {
                "is_false_positive_test": True,
                "expected_violations": [],
            }
        })
        result = ac9_overall_precision(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_false_positives_on_clean_file(self):
        analysis = _make_analysis(
            files=[
                {"file": "clean/clean_service.cs", "path": "clean/clean_service.cs",
                 "violations": [{"rule_id": "CA0001"}, {"rule_id": "CA0002"}]},
            ],
            summary={"total_violations": 10},
        )
        gt = _make_ground_truth(files={
            "clean/clean_service.cs": {
                "is_false_positive_test": True,
                "expected_violations": [],
            }
        })
        result = ac9_overall_precision(analysis, gt)
        # 2 false positives out of 10 -> precision = 8/10 = 0.8 < 0.85
        assert result.passed is False
        assert result.score == pytest.approx(0.8)

    def test_no_clean_files_perfect_precision(self):
        """If no clean files are defined, precision is 1.0."""
        analysis = _make_analysis(
            files=[{"file": "src/test.cs", "violations": [{"rule_id": "CA3001"}]}],
            summary={"total_violations": 5},
        )
        gt = _make_ground_truth(files={})
        result = ac9_overall_precision(analysis, gt)
        assert result.passed is True


class TestAC10OverallRecall:
    """AC-10: Overall recall."""

    def test_full_recall(self):
        analysis = _make_analysis(summary={"total_violations": 10})
        gt = _make_ground_truth(summary={"total_expected_violations": 10})
        result = ac10_overall_recall(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_low_recall(self):
        analysis = _make_analysis(summary={"total_violations": 3})
        gt = _make_ground_truth(summary={"total_expected_violations": 10})
        result = ac10_overall_recall(analysis, gt)
        assert result.passed is False
        assert result.score == pytest.approx(0.3)

    def test_over_detection_capped(self):
        """detected is capped to expected, so recall stays <= 1.0."""
        analysis = _make_analysis(summary={"total_violations": 50})
        gt = _make_ground_truth(summary={"total_expected_violations": 10})
        result = ac10_overall_recall(analysis, gt)
        assert result.passed is True
        assert result.score == pytest.approx(1.0)

    def test_zero_expected(self):
        """Zero expected violations -> recall 1.0."""
        analysis = _make_analysis(summary={"total_violations": 0})
        gt = _make_ground_truth(summary={"total_expected_violations": 0})
        result = ac10_overall_recall(analysis, gt)
        assert result.passed is True


class TestRunAllAccuracyChecks:
    """Test run_all_accuracy_checks returns all 10 checks."""

    def test_returns_10_checks(self):
        analysis = _make_analysis()
        gt = _make_ground_truth()
        results = run_all_accuracy_checks(analysis, gt)
        assert len(results) == 10
        check_ids = [r.check_id for r in results]
        for i in range(1, 11):
            assert f"AC-{i}" in check_ids
