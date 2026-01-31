"""Tests for severity classification and mapping."""

import sys
from pathlib import Path

# Add scripts directory to path for importing smell_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from smell_analyzer import (
    SEVERITY_MAP,
    SmellInstance,
)


class TestSeverityMap:
    """Tests for the SEVERITY_MAP constant."""

    def test_error_maps_to_critical(self):
        """Test ERROR severity maps to CRITICAL."""
        assert SEVERITY_MAP.get("ERROR") == "CRITICAL"

    def test_warning_maps_to_high(self):
        """Test WARNING severity maps to HIGH."""
        assert SEVERITY_MAP.get("WARNING") == "HIGH"

    def test_info_maps_to_medium(self):
        """Test INFO severity maps to MEDIUM."""
        assert SEVERITY_MAP.get("INFO") == "MEDIUM"

    def test_all_semgrep_severities_mapped(self):
        """Test all known Semgrep severity levels are mapped."""
        expected_mappings = {
            "ERROR": "CRITICAL",
            "WARNING": "HIGH",
            "INFO": "MEDIUM",
        }
        for semgrep_sev, dd_sev in expected_mappings.items():
            assert SEVERITY_MAP.get(semgrep_sev) == dd_sev

    def test_unknown_severity_returns_none(self):
        """Test unknown severity returns None from dict.get()."""
        assert SEVERITY_MAP.get("UNKNOWN") is None
        assert SEVERITY_MAP.get("LOW") is None


class TestSmellInstanceSeverity:
    """Tests for SmellInstance severity field validation."""

    def test_smell_instance_with_critical_severity(self):
        """Test SmellInstance can hold CRITICAL severity."""
        smell = SmellInstance(
            rule_id="sql-injection",
            dd_smell_id="SQL_INJECTION",
            dd_category="security",
            file_path="src/db.py",
            line_start=10,
            line_end=10,
            column_start=1,
            column_end=50,
            severity="CRITICAL",
            message="SQL injection detected",
        )
        assert smell.severity == "CRITICAL"

    def test_smell_instance_with_high_severity(self):
        """Test SmellInstance can hold HIGH severity."""
        smell = SmellInstance(
            rule_id="empty-catch",
            dd_smell_id="D1_EMPTY_CATCH",
            dd_category="error_handling",
            file_path="src/handler.py",
            line_start=25,
            line_end=27,
            column_start=5,
            column_end=10,
            severity="HIGH",
            message="Empty catch block",
        )
        assert smell.severity == "HIGH"

    def test_smell_instance_with_medium_severity(self):
        """Test SmellInstance can hold MEDIUM severity."""
        smell = SmellInstance(
            rule_id="unused-import",
            dd_smell_id="I1_UNUSED_IMPORT",
            dd_category="dead_code",
            file_path="src/utils.py",
            line_start=1,
            line_end=1,
            column_start=1,
            column_end=20,
            severity="MEDIUM",
            message="Unused import detected",
        )
        assert smell.severity == "MEDIUM"

    def test_smell_instance_preserves_code_snippet(self):
        """Test SmellInstance preserves code snippet with severity."""
        snippet = "except Exception:\n    pass"
        smell = SmellInstance(
            rule_id="empty-catch",
            dd_smell_id="D1_EMPTY_CATCH",
            dd_category="error_handling",
            file_path="src/handler.py",
            line_start=10,
            line_end=11,
            column_start=1,
            column_end=8,
            severity="HIGH",
            message="Empty catch block",
            code_snippet=snippet,
        )
        assert smell.code_snippet == snippet
        assert smell.severity == "HIGH"


class TestSeverityPriority:
    """Tests for severity priority ordering."""

    def test_severity_priority_order(self):
        """Test severity levels can be sorted by priority."""
        severities = ["MEDIUM", "CRITICAL", "HIGH", "LOW"]
        priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_sevs = sorted(severities, key=lambda s: priority.get(s, 99))
        assert sorted_sevs == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_critical_is_highest_priority(self):
        """Test CRITICAL has highest priority (lowest sort key)."""
        priority = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        assert priority["CRITICAL"] < priority["HIGH"]
        assert priority["CRITICAL"] < priority["MEDIUM"]
        assert priority["CRITICAL"] < priority["LOW"]

    def test_severity_counts_aggregation(self):
        """Test severity counts can be aggregated correctly."""
        smells = [
            SmellInstance(
                rule_id="r1", dd_smell_id="S1", dd_category="c1",
                file_path="f.py", line_start=1, line_end=1,
                column_start=1, column_end=1, severity="CRITICAL",
                message="m1"
            ),
            SmellInstance(
                rule_id="r2", dd_smell_id="S2", dd_category="c2",
                file_path="f.py", line_start=2, line_end=2,
                column_start=1, column_end=1, severity="HIGH",
                message="m2"
            ),
            SmellInstance(
                rule_id="r3", dd_smell_id="S3", dd_category="c3",
                file_path="f.py", line_start=3, line_end=3,
                column_start=1, column_end=1, severity="HIGH",
                message="m3"
            ),
            SmellInstance(
                rule_id="r4", dd_smell_id="S4", dd_category="c4",
                file_path="f.py", line_start=4, line_end=4,
                column_start=1, column_end=1, severity="MEDIUM",
                message="m4"
            ),
        ]

        severity_counts: dict[str, int] = {}
        for smell in smells:
            severity_counts[smell.severity] = severity_counts.get(smell.severity, 0) + 1

        assert severity_counts["CRITICAL"] == 1
        assert severity_counts["HIGH"] == 2
        assert severity_counts["MEDIUM"] == 1
