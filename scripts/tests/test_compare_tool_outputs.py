"""Tests for compare_tool_outputs.py enhancements.

Covers tool-specific volatile keys, trivy normalizer, numeric tolerance,
array length tolerance, and normalizer dispatch.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compare_tool_outputs import (
    TOOL_NORMALIZERS,
    TOOL_VOLATILE_KEYS,
    _collect_diffs,
    _strip_volatile,
)


# ── TestToolVolatileKeys ──────────────────────────────────────────────────────


class TestToolVolatileKeys:
    def test_trivy_references_stripped(self):
        obj = {
            "data": {
                "vulnerabilities": [
                    {
                        "id": "CVE-2024-1234",
                        "severity": "HIGH",
                        "references": ["https://nvd.nist.gov/..."],
                        "description": "A vuln",
                        "published_date": "2024-01-01",
                        "age_days": 365,
                    }
                ]
            }
        }
        result = _strip_volatile(
            copy.deepcopy(obj),
            tool_volatile_keys=TOOL_VOLATILE_KEYS["trivy"],
        )
        vuln = result["data"]["vulnerabilities"][0]
        assert "references" not in vuln
        assert "description" not in vuln
        assert "published_date" not in vuln
        assert "age_days" not in vuln
        assert vuln["id"] == "CVE-2024-1234"
        assert vuln["severity"] == "HIGH"

    def test_unknown_tool_no_extra_stripping(self):
        obj = {
            "data": {
                "references": ["https://example.com"],
                "fingerprint": "abc123",
            }
        }
        result = _strip_volatile(copy.deepcopy(obj), tool_volatile_keys=None)
        assert "references" in result["data"]
        assert "fingerprint" in result["data"]

    def test_gitleaks_fingerprint_stripped(self):
        obj = {"findings": [{"rule_id": "aws-key", "fingerprint": "abc123"}]}
        result = _strip_volatile(
            copy.deepcopy(obj),
            tool_volatile_keys=TOOL_VOLATILE_KEYS["gitleaks"],
        )
        assert "fingerprint" not in result["findings"][0]
        assert result["findings"][0]["rule_id"] == "aws-key"

    def test_roslyn_message_stripped(self):
        obj = {"diagnostics": [{"id": "CA1000", "message": "Some SDK message"}]}
        result = _strip_volatile(
            copy.deepcopy(obj),
            tool_volatile_keys=TOOL_VOLATILE_KEYS["roslyn-analyzers"],
        )
        assert "message" not in result["diagnostics"][0]
        assert result["diagnostics"][0]["id"] == "CA1000"


# ── TestTrivyNormalizer ───────────────────────────────────────────────────────


class TestTrivyNormalizer:
    @pytest.fixture()
    def trivy_data(self):
        return {
            "data": {
                "vulnerabilities": [
                    {"id": "CVE-1", "severity": "HIGH"},
                    {"id": "CVE-2", "severity": "CRITICAL"},
                    {"id": "CVE-3", "severity": "HIGH"},
                ],
                "iac_misconfigurations": [
                    {"id": "MISCONFIG-1", "severity": "MEDIUM"},
                ],
                "total_misconfigurations": 1,
                "findings_summary": {
                    "by_severity": {"HIGH": 3, "CRITICAL": 1, "MEDIUM": 1},
                    "total_findings": 5,
                },
                "targets": [
                    {"name": "myimage", "type": "os"},
                    {"name": "Dockerfile", "type": "dockerfile"},
                    {"name": "main.tf", "type": "terraform"},
                ],
            }
        }

    @pytest.fixture()
    def args(self):
        return argparse.Namespace(tool="trivy")

    def test_misconfigs_removed(self, trivy_data, args):
        normalizer = TOOL_NORMALIZERS["trivy"]
        native, docker = normalizer(
            copy.deepcopy(trivy_data), copy.deepcopy(trivy_data), args,
        )
        assert "iac_misconfigurations" not in native["data"]
        assert "total_misconfigurations" not in native["data"]

    def test_severity_recounted(self, trivy_data, args):
        normalizer = TOOL_NORMALIZERS["trivy"]
        native, _ = normalizer(
            copy.deepcopy(trivy_data), copy.deepcopy(trivy_data), args,
        )
        summary = native["data"]["findings_summary"]
        assert summary["by_severity"] == {"HIGH": 2, "CRITICAL": 1}
        assert summary["total_findings"] == 3

    def test_iac_targets_filtered(self, trivy_data, args):
        normalizer = TOOL_NORMALIZERS["trivy"]
        native, _ = normalizer(
            copy.deepcopy(trivy_data), copy.deepcopy(trivy_data), args,
        )
        targets = native["data"]["targets"]
        assert len(targets) == 1
        assert targets[0]["type"] == "os"

    def test_no_data_key_handled(self, args):
        """Normalizer doesn't crash on unexpected structure."""
        normalizer = TOOL_NORMALIZERS["trivy"]
        native, docker = normalizer({"other": 1}, {"other": 1}, args)
        assert native == {"other": 1}


# ── TestNumericTolerance ──────────────────────────────────────────────────────


class TestNumericTolerance:
    def test_exact_match(self):
        diffs = _collect_diffs(100, 100, numeric_tolerance=0.01)
        assert diffs == []

    def test_within_tolerance(self):
        diffs = _collect_diffs(1000, 1001, numeric_tolerance=0.01)
        assert diffs == []

    def test_exceeds_tolerance(self):
        diffs = _collect_diffs(100, 200, numeric_tolerance=0.01)
        assert len(diffs) == 1

    def test_zero_handling(self):
        """When both are 0, they're equal; when one is 0, denominator is 1."""
        diffs = _collect_diffs(0, 0, numeric_tolerance=0.01)
        assert diffs == []

        # int vs float triggers type mismatch before numeric tolerance
        # so use same types for meaningful tolerance tests
        diffs = _collect_diffs(0.0, 0.005, numeric_tolerance=0.01)
        assert diffs == []

        diffs = _collect_diffs(0.0, 5.0, numeric_tolerance=0.01)
        assert len(diffs) == 1

    def test_no_tolerance_by_default(self):
        diffs = _collect_diffs(1000, 1001)
        assert len(diffs) == 1

    def test_nested_numeric_tolerance(self):
        native = {"metrics": {"complexity": 15.3}}
        docker = {"metrics": {"complexity": 15.31}}
        diffs = _collect_diffs(native, docker, numeric_tolerance=0.001)
        assert diffs == []


# ── TestArrayLengthTolerance ──────────────────────────────────────────────────


class TestArrayLengthTolerance:
    def test_exact_required_by_default(self):
        diffs = _collect_diffs([1, 2, 3], [1, 2])
        assert len(diffs) == 1
        assert "array length" in diffs[0]

    def test_intersection_match_within_tolerance(self):
        native = [
            {"name": "a", "value": 1},
            {"name": "b", "value": 2},
            {"name": "c", "value": 3},
        ]
        docker = [
            {"name": "a", "value": 1},
            {"name": "b", "value": 2},
        ]
        # 1/3 = 33% difference, within 50% tolerance
        diffs = _collect_diffs(native, docker, array_length_tolerance=0.5)
        # Should note the length diff within tolerance, but not fail on content
        assert len(diffs) == 1
        assert "within" in diffs[0]
        assert "tolerance" in diffs[0]

    def test_exceeds_tolerance(self):
        native = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        docker = [{"name": "a"}]
        # 2/3 = 67% difference, exceeds 10% tolerance
        diffs = _collect_diffs(native, docker, array_length_tolerance=0.1)
        assert len(diffs) == 1
        assert "within" not in diffs[0]

    def test_content_diffs_still_detected(self):
        native = [
            {"name": "a", "value": 1},
            {"name": "b", "value": 2},
            {"name": "c", "value": 3},
        ]
        docker = [
            {"name": "a", "value": 999},
            {"name": "b", "value": 2},
        ]
        diffs = _collect_diffs(native, docker, array_length_tolerance=0.5)
        # Length diff note + value diff for "a"
        assert len(diffs) == 2


# ── TestToolNormalizerDispatch ────────────────────────────────────────────────


class TestToolNormalizerDispatch:
    def test_registered_normalizer_called(self):
        assert "trivy" in TOOL_NORMALIZERS

    def test_no_error_for_unknown_tool(self):
        assert TOOL_NORMALIZERS.get("nonexistent-tool") is None
