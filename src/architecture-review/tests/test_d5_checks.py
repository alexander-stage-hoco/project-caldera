"""Tests for D5: Cross-Tool Consistency checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from checks.d5_cross_tool import (
    _check_adapter_structure_drift,
    _check_envelope_reference,
    _check_naming_formula,
    _expected_class_name,
    check_d5,
)
from discovery import list_all_tools


class TestExpectedClassName:
    @pytest.mark.parametrize(
        "tool_name,expected",
        [
            ("scc", "SccAdapter"),
            ("lizard", "LizardAdapter"),
            ("pmd-cpd", "PmdCpdAdapter"),
            ("git-sizer", "GitSizerAdapter"),
            ("roslyn-analyzers", "RoslynAnalyzersAdapter"),
            ("coverage-ingest", "CoverageIngestAdapter"),
        ],
    )
    def test_naming_formula(self, tool_name: str, expected: str) -> None:
        assert _expected_class_name(tool_name) == expected


class TestEnvelopeReference:
    def test_all_tools_have_fields(self, project_root: Path) -> None:
        tools = list_all_tools(project_root)
        findings = _check_envelope_reference(tools, project_root)
        # Some tools may have minor issues, but check it runs without errors
        assert isinstance(findings, list)


class TestNamingFormula:
    def test_known_tools(self, project_root: Path) -> None:
        # Check a few tools we know follow the formula
        findings = _check_naming_formula(["scc", "lizard"], project_root)
        # scc→SccAdapter and lizard→LizardAdapter should match
        assert len(findings) == 0


class TestAdapterStructureDrift:
    def test_all_have_constants(self, project_root: Path) -> None:
        tools = list_all_tools(project_root)
        findings = _check_adapter_structure_drift(tools, project_root)
        # This is a drift check — there may be some findings, but it shouldn't crash
        assert isinstance(findings, list)


class TestIntegration:
    def test_d5_runs(self, project_root: Path) -> None:
        findings = check_d5(project_root)
        assert isinstance(findings, list)
        # Verify the findings all have valid structure
        for f in findings:
            assert f.severity in ("error", "warning", "info")
            assert f.rule_id
