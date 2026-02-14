"""Tests for security checks (SC-1 to SC-6) in scripts/checks/security.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.security import (
    _is_security_finding,
    _extract_cwe_id,
    _map_to_owasp,
    check_cwe_presence,
    check_owasp_coverage,
    check_sql_injection_detection,
    check_xss_detection,
    check_command_injection_detection,
    check_severity_distribution,
    run_security_checks,
    OWASP_TOP_10,
    SECURITY_SMELL_OWASP_MAP,
    SECURITY_KEYWORDS,
)
from checks import CheckCategory


# ---------------------------------------------------------------------------
# Helpers to build analysis dicts
# ---------------------------------------------------------------------------

def _analysis_with_smells(smells: list[dict], file_path: str = "src/app.py") -> dict:
    """Build a minimal analysis dict containing one file with the given smells."""
    return {
        "files": [
            {
                "path": file_path,
                "smells": smells,
            }
        ]
    }


def _make_security_smell(
    dd_category: str = "security",
    rule_id: str = "sql-injection-test",
    dd_smell_id: str = "SQL_INJECTION",
    severity: str = "ERROR",
    message: str = "SQL injection found",
    metadata: dict | None = None,
) -> dict:
    """Build a single smell dict."""
    smell: dict = {
        "dd_category": dd_category,
        "rule_id": rule_id,
        "dd_smell_id": dd_smell_id,
        "severity": severity,
        "message": message,
    }
    if metadata is not None:
        smell["metadata"] = metadata
    return smell


def _ground_truth_with(
    smells: list[dict],
    lang: str = "python",
    filename: str = "app.py",
) -> dict[str, dict]:
    """Build a minimal ground truth dict."""
    return {
        lang: {
            "language": lang,
            "files": {
                filename: {
                    "expected_smells": smells,
                }
            },
        }
    }


# ===========================================================================
# _is_security_finding
# ===========================================================================

class TestIsSecurityFinding:
    def test_category_security(self):
        assert _is_security_finding({"dd_category": "security"}) is True

    def test_category_not_security(self):
        assert _is_security_finding({"dd_category": "error_handling", "rule_id": "", "message": "", "dd_smell_id": ""}) is False

    def test_keyword_in_rule_id(self):
        assert _is_security_finding({"dd_category": "", "rule_id": "sql-injection-check", "message": "", "dd_smell_id": ""}) is True

    def test_keyword_in_message(self):
        assert _is_security_finding({"dd_category": "", "rule_id": "", "message": "found a hardcoded secret", "dd_smell_id": ""}) is True

    def test_keyword_in_dd_smell_id(self):
        assert _is_security_finding({"dd_category": "", "rule_id": "", "message": "", "dd_smell_id": "XSS_VULNERABILITY"}) is True

    def test_no_match(self):
        assert _is_security_finding({"dd_category": "dead_code", "rule_id": "unused-import", "message": "unused import", "dd_smell_id": "I1_UNUSED_IMPORT"}) is False


# ===========================================================================
# _extract_cwe_id
# ===========================================================================

class TestExtractCweId:
    def test_cwe_in_metadata_string(self):
        smell = {"rule_id": "", "message": "", "metadata": {"cwe": "CWE-89"}}
        assert _extract_cwe_id(smell) == "CWE-89"

    def test_cwe_in_metadata_list(self):
        smell = {"rule_id": "", "message": "", "metadata": {"cwe": ["CWE-79", "CWE-89"]}}
        assert _extract_cwe_id(smell) == "CWE-79"

    def test_cwe_in_metadata_empty_list(self):
        smell = {"rule_id": "", "message": "", "metadata": {"cwe": []}}
        assert _extract_cwe_id(smell) is None

    def test_cwe_in_rule_id(self):
        smell = {"rule_id": "rule-CWE-22-path-traversal", "message": "", "metadata": {}}
        assert _extract_cwe_id(smell) == "CWE-22"

    def test_cwe_in_message(self):
        smell = {"rule_id": "", "message": "Detected CWE-78 command injection", "metadata": {}}
        assert _extract_cwe_id(smell) == "CWE-78"

    def test_no_cwe(self):
        smell = {"rule_id": "empty-catch", "message": "empty catch", "metadata": {}}
        assert _extract_cwe_id(smell) is None

    def test_metadata_not_dict(self):
        smell = {"rule_id": "", "message": "", "metadata": "not_a_dict"}
        assert _extract_cwe_id(smell) is None


# ===========================================================================
# _map_to_owasp
# ===========================================================================

class TestMapToOwasp:
    def test_known_smell_id_mapping(self):
        smell = {"dd_smell_id": "SQL_INJECTION", "rule_id": "", "message": ""}
        assert _map_to_owasp(smell) == "A03"

    def test_known_smell_id_hardcoded_secret(self):
        smell = {"dd_smell_id": "HARDCODED_SECRET", "rule_id": "", "message": ""}
        assert _map_to_owasp(smell) == "A07"

    def test_keyword_sqli(self):
        smell = {"dd_smell_id": "", "rule_id": "some-sqli-rule", "message": ""}
        assert _map_to_owasp(smell) == "A03"

    def test_keyword_xss(self):
        smell = {"dd_smell_id": "", "rule_id": "detect-xss", "message": ""}
        assert _map_to_owasp(smell) == "A03"

    def test_keyword_command_injection(self):
        smell = {"dd_smell_id": "", "rule_id": "command injection check", "message": ""}
        assert _map_to_owasp(smell) == "A03"

    def test_keyword_ssrf(self):
        smell = {"dd_smell_id": "", "rule_id": "", "message": "ssrf detected"}
        assert _map_to_owasp(smell) == "A10"

    def test_keyword_deserialization(self):
        smell = {"dd_smell_id": "", "rule_id": "", "message": "insecure deserialization via pickle"}
        assert _map_to_owasp(smell) == "A08"

    def test_keyword_weak_hash(self):
        smell = {"dd_smell_id": "", "rule_id": "", "message": "use of md5 is weak hash"}
        assert _map_to_owasp(smell) == "A02"

    def test_keyword_path_traversal(self):
        smell = {"dd_smell_id": "", "rule_id": "path traversal check", "message": ""}
        assert _map_to_owasp(smell) == "A01"

    def test_keyword_hardcoded_secret(self):
        smell = {"dd_smell_id": "", "rule_id": "", "message": "hardcoded credential found"}
        assert _map_to_owasp(smell) == "A07"

    def test_no_mapping(self):
        smell = {"dd_smell_id": "", "rule_id": "unused-import", "message": "unused import"}
        assert _map_to_owasp(smell) is None


# ===========================================================================
# check_cwe_presence  (SC-1)
# ===========================================================================

class TestCheckCwePresence:
    def test_no_security_findings(self):
        analysis = _analysis_with_smells([])
        result = check_cwe_presence(analysis)
        assert result.check_id == "SC-1"
        assert result.passed is True
        assert result.score == 1.0

    def test_all_have_cwe(self):
        smells = [
            _make_security_smell(metadata={"cwe": "CWE-89"}),
            _make_security_smell(rule_id="xss-CWE-79", dd_smell_id="XSS_VULNERABILITY", metadata={}),
        ]
        analysis = _analysis_with_smells(smells)
        result = check_cwe_presence(analysis)
        assert result.passed is True
        assert result.score == 1.0

    def test_below_threshold(self):
        # 1 of 5 have CWE => 20% < 80%
        smells = [
            _make_security_smell(metadata={"cwe": "CWE-89"}),
        ]
        for i in range(4):
            smells.append(_make_security_smell(rule_id=f"sec-rule-{i}", metadata={}))
        analysis = _analysis_with_smells(smells)
        result = check_cwe_presence(analysis)
        assert result.passed is False
        assert result.evidence["cwe_rate"] == 20.0

    def test_missing_cwe_samples_capped_at_5(self):
        smells = [_make_security_smell(rule_id=f"rule-{i}", metadata={}) for i in range(10)]
        analysis = _analysis_with_smells(smells)
        result = check_cwe_presence(analysis)
        assert len(result.evidence.get("missing_cwe_samples", [])) <= 5


# ===========================================================================
# check_owasp_coverage  (SC-2)
# ===========================================================================

class TestCheckOwaspCoverage:
    def test_no_security_findings(self):
        result = check_owasp_coverage(_analysis_with_smells([]))
        assert result.check_id == "SC-2"
        assert result.passed is True

    def test_multiple_owasp_categories(self):
        smells = [
            _make_security_smell(dd_smell_id="SQL_INJECTION"),
            _make_security_smell(dd_smell_id="HARDCODED_SECRET", rule_id="hardcoded-secret"),
            _make_security_smell(dd_smell_id="SSRF_VULNERABILITY", rule_id="ssrf-check", message="ssrf"),
        ]
        analysis = _analysis_with_smells(smells)
        result = check_owasp_coverage(analysis)
        assert result.passed is True
        assert result.evidence["owasp_categories_detected"] >= 2

    def test_single_category_few_findings_still_passes(self):
        # With < 5 findings but only 1 category, it still passes
        smells = [_make_security_smell(dd_smell_id="SQL_INJECTION")]
        analysis = _analysis_with_smells(smells)
        result = check_owasp_coverage(analysis)
        assert result.passed is True  # total_security < 5

    def test_single_category_many_findings_fails(self):
        smells = [_make_security_smell(dd_smell_id="SQL_INJECTION", rule_id=f"sqli-{i}") for i in range(6)]
        analysis = _analysis_with_smells(smells)
        result = check_owasp_coverage(analysis)
        # Only 1 category detected (A03), with 6 findings, expects >= 2 categories
        assert result.passed is False


# ===========================================================================
# check_sql_injection_detection  (SC-3)
# ===========================================================================

class TestCheckSqlInjectionDetection:
    def test_no_expected(self):
        gt = _ground_truth_with([])
        result = check_sql_injection_detection(_analysis_with_smells([]), gt)
        assert result.check_id == "SC-3"
        assert result.passed is True

    def test_all_detected(self):
        gt = _ground_truth_with([{"smell_id": "SQL_INJECTION", "count": 2}])
        smells = [
            _make_security_smell(dd_smell_id="SQL_INJECTION"),
            _make_security_smell(dd_smell_id="SQL_INJECTION", rule_id="another-sqli"),
        ]
        result = check_sql_injection_detection(_analysis_with_smells(smells), gt)
        assert result.passed is True
        assert result.evidence["detection_rate"] == 100.0

    def test_partial_detection_below_threshold(self):
        gt = _ground_truth_with([{"smell_id": "SQL_INJECTION", "count": 10}])
        smells = [_make_security_smell(dd_smell_id="SQL_INJECTION")]
        result = check_sql_injection_detection(_analysis_with_smells(smells), gt)
        assert result.passed is False
        assert result.evidence["detection_rate"] == 10.0

    def test_detection_via_rule_id(self):
        gt = _ground_truth_with([{"smell_id": "SQL_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="sql-injection-python", dd_category="security")]
        result = check_sql_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_detection_via_message(self):
        gt = _ground_truth_with([{"smell_id": "SQL_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="other", message="possible sql injection")]
        result = check_sql_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_no_expected_but_found_gives_half_score(self):
        gt = _ground_truth_with([])
        smells = [_make_security_smell(dd_smell_id="SQL_INJECTION")]
        result = check_sql_injection_detection(_analysis_with_smells(smells), gt)
        assert result.score == 0.5


# ===========================================================================
# check_xss_detection  (SC-4)
# ===========================================================================

class TestCheckXssDetection:
    def test_no_expected(self):
        gt = _ground_truth_with([])
        result = check_xss_detection(_analysis_with_smells([]), gt)
        assert result.check_id == "SC-4"
        assert result.passed is True

    def test_detected_above_threshold(self):
        gt = _ground_truth_with([{"smell_id": "XSS", "count": 2}])
        smells = [
            _make_security_smell(dd_smell_id="XSS_VUL", rule_id="xss-check"),
            _make_security_smell(dd_smell_id="XSS_VUL", rule_id="xss-check-2"),
        ]
        result = check_xss_detection(_analysis_with_smells(smells), gt)
        assert result.passed is True
        assert result.evidence["detection_rate"] == 100.0

    def test_detected_via_message(self):
        gt = _ground_truth_with([{"smell_id": "XSS", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="other", message="cross-site scripting detected")]
        result = check_xss_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_below_threshold(self):
        gt = _ground_truth_with([{"smell_id": "XSS", "count": 10}])
        smells = [_make_security_smell(dd_smell_id="XSS_VUL", rule_id="xss-check")]
        result = check_xss_detection(_analysis_with_smells(smells), gt)
        assert result.passed is False

    def test_no_expected_but_found_gives_half_score(self):
        gt = _ground_truth_with([])
        smells = [_make_security_smell(dd_smell_id="XSS_FOUND", rule_id="xss-detect")]
        result = check_xss_detection(_analysis_with_smells(smells), gt)
        assert result.score == 0.5


# ===========================================================================
# check_command_injection_detection  (SC-5)
# ===========================================================================

class TestCheckCommandInjectionDetection:
    def test_no_expected(self):
        gt = _ground_truth_with([])
        result = check_command_injection_detection(_analysis_with_smells([]), gt)
        assert result.check_id == "SC-5"
        assert result.passed is True

    def test_detected_via_dd_smell_id(self):
        gt = _ground_truth_with([{"smell_id": "COMMAND_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="COMMAND_INJECTION", rule_id="cmd")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_detected_via_cmd_injection(self):
        gt = _ground_truth_with([{"smell_id": "CMD_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="CMD_INJECTION_FOUND", rule_id="a")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_detected_via_rule_id(self):
        gt = _ground_truth_with([{"smell_id": "COMMAND_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="command-injection-check")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_detected_via_message_subprocess_user(self):
        gt = _ground_truth_with([{"smell_id": "COMMAND_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="other", message="subprocess with user input")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_detected_via_message_os_system(self):
        gt = _ground_truth_with([{"smell_id": "COMMAND_INJECTION", "count": 1}])
        smells = [_make_security_smell(dd_smell_id="OTHER", rule_id="other", message="call to os.system is dangerous")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.evidence["detected"] == 1

    def test_below_threshold(self):
        gt = _ground_truth_with([{"smell_id": "COMMAND_INJECTION", "count": 10}])
        smells = [_make_security_smell(dd_smell_id="COMMAND_INJECTION")]
        result = check_command_injection_detection(_analysis_with_smells(smells), gt)
        assert result.passed is False


# ===========================================================================
# check_severity_distribution  (SC-6)
# ===========================================================================

class TestCheckSeverityDistribution:
    def test_no_security_findings(self):
        result = check_severity_distribution(_analysis_with_smells([]))
        assert result.check_id == "SC-6"
        assert result.passed is True

    def test_all_have_severity(self):
        smells = [
            _make_security_smell(severity="ERROR"),
            _make_security_smell(severity="WARNING"),
            _make_security_smell(severity="INFO"),
        ]
        result = check_severity_distribution(_analysis_with_smells(smells))
        assert result.passed is True
        assert result.score == 1.0

    def test_below_threshold_with_unknown(self):
        smells = [_make_security_smell(severity="UNKNOWN") for _ in range(5)]
        result = check_severity_distribution(_analysis_with_smells(smells))
        assert result.passed is False
        assert result.score == 0.0

    def test_mixed_severity_above_threshold(self):
        smells = [
            _make_security_smell(severity="ERROR"),
            _make_security_smell(severity="ERROR"),
            _make_security_smell(severity="ERROR"),
            _make_security_smell(severity="ERROR"),
            _make_security_smell(severity="UNKNOWN"),
        ]
        result = check_severity_distribution(_analysis_with_smells(smells))
        assert result.passed is True
        assert result.evidence["severity_assignment_rate"] == 80.0

    def test_custom_severity_classified_as_unknown(self):
        smells = [_make_security_smell(severity="CUSTOM_LEVEL")]
        result = check_severity_distribution(_analysis_with_smells(smells))
        assert result.evidence["severity_distribution"]["UNKNOWN"] == 1


# ===========================================================================
# run_security_checks
# ===========================================================================

class TestRunSecurityChecks:
    def test_returns_six_checks(self, tmp_path: Path):
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        (gt_dir / "python.json").write_text(json.dumps({
            "language": "python",
            "files": {},
        }))
        analysis = _analysis_with_smells([])
        results = run_security_checks(analysis, str(gt_dir))
        assert len(results) == 6
        ids = {r.check_id for r in results}
        assert ids == {"SC-1", "SC-2", "SC-3", "SC-4", "SC-5", "SC-6"}

    def test_all_pass_for_non_security_analysis(self, tmp_path: Path):
        gt_dir = tmp_path / "gt"
        gt_dir.mkdir()
        (gt_dir / "python.json").write_text(json.dumps({
            "language": "python",
            "files": {},
        }))
        smells = [{"dd_category": "error_handling", "rule_id": "empty-catch", "message": "empty", "dd_smell_id": "D1_EMPTY_CATCH", "severity": "WARNING"}]
        analysis = _analysis_with_smells(smells)
        results = run_security_checks(analysis, str(gt_dir))
        assert all(r.passed for r in results)
