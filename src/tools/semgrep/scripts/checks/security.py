"""
Security checks (SC-1 to SC-6) for Semgrep security analysis.

Tests security-specific detection and taxonomy mapping:
- SC-1: CWE ID presence on security findings
- SC-2: OWASP Top 10 category coverage
- SC-3: SQL injection detection rate (critical)
- SC-4: XSS detection rate
- SC-5: Command injection detection rate
- SC-6: Security finding severity distribution
"""

import re
from pathlib import Path

from . import (
    CheckResult,
    CheckCategory,
    load_all_ground_truth,
    normalize_path,
)


# OWASP Top 10 2021 categories
OWASP_TOP_10 = {
    "A01": "Broken Access Control",
    "A02": "Cryptographic Failures",
    "A03": "Injection",
    "A04": "Insecure Design",
    "A05": "Security Misconfiguration",
    "A06": "Vulnerable Components",
    "A07": "Authentication Failures",
    "A08": "Software and Data Integrity",
    "A09": "Security Logging Failures",
    "A10": "SSRF",
}

# Security smell IDs and their OWASP mappings
SECURITY_SMELL_OWASP_MAP = {
    "SQL_INJECTION": "A03",
    "COMMAND_INJECTION": "A03",
    "XSS": "A03",
    "CODE_INJECTION": "A03",
    "LDAP_INJECTION": "A03",
    "XPATH_INJECTION": "A03",
    "SSRF": "A10",
    "WEAK_HASH": "A02",
    "WEAK_CIPHER": "A02",
    "HARDCODED_SECRET": "A07",
    "HARDCODED_CREDENTIAL": "A07",
    "UNSAFE_DESERIALIZATION": "A08",
    "PATH_TRAVERSAL": "A01",
    "INSECURE_RANDOM": "A02",
}

# Keywords that indicate security issues (for identification)
SECURITY_KEYWORDS = [
    "injection", "xss", "ssrf", "csrf", "traversal", "deserialization",
    "hardcoded", "secret", "credential", "cipher", "crypto", "hash",
    "random", "auth", "privilege", "escalation", "vulnerability",
]


def _is_security_finding(smell: dict) -> bool:
    """Determine if a smell is a security finding."""
    dd_category = smell.get("dd_category", "").lower()
    rule_id = smell.get("rule_id", "").lower()
    message = smell.get("message", "").lower()
    dd_smell_id = smell.get("dd_smell_id", "").upper()

    if dd_category == "security":
        return True

    for keyword in SECURITY_KEYWORDS:
        if keyword in rule_id or keyword in message or keyword in dd_smell_id.lower():
            return True

    return False


def _extract_cwe_id(smell: dict) -> str | None:
    """Extract CWE ID from smell metadata."""
    rule_id = smell.get("rule_id", "")
    message = smell.get("message", "")
    metadata = smell.get("metadata", {})

    # Check metadata first (most reliable)
    if isinstance(metadata, dict):
        cwe = metadata.get("cwe")
        if cwe:
            if isinstance(cwe, list):
                return cwe[0] if cwe else None
            return str(cwe)

    # Check common CWE patterns in rule_id and message
    cwe_pattern = r"CWE[-_]?(\d+)"

    for text in [rule_id, message]:
        match = re.search(cwe_pattern, text, re.IGNORECASE)
        if match:
            return f"CWE-{match.group(1)}"

    return None


def _map_to_owasp(smell: dict) -> str | None:
    """Map a finding to an OWASP Top 10 category code (A01-A10)."""
    dd_smell_id = smell.get("dd_smell_id", "").upper()
    rule_id = smell.get("rule_id", "").lower()
    message = smell.get("message", "").lower()

    # Check known smell ID mappings first
    for smell_key, owasp_code in SECURITY_SMELL_OWASP_MAP.items():
        if smell_key in dd_smell_id:
            return owasp_code

    # Keyword-based mapping
    combined = f"{rule_id} {message}"

    if any(kw in combined for kw in ["sql injection", "sqli"]):
        return "A03"
    if any(kw in combined for kw in ["xss", "cross-site scripting"]):
        return "A03"
    if any(kw in combined for kw in ["command injection", "os.system", "subprocess"]):
        return "A03"
    if any(kw in combined for kw in ["ssrf", "server-side request"]):
        return "A10"
    if any(kw in combined for kw in ["hardcoded", "secret", "credential"]):
        return "A07"
    if any(kw in combined for kw in ["deserialization", "pickle", "yaml.load"]):
        return "A08"
    if any(kw in combined for kw in ["weak hash", "md5", "sha1"]):
        return "A02"
    if any(kw in combined for kw in ["path traversal", "directory traversal"]):
        return "A01"

    return None


def check_cwe_presence(analysis: dict) -> CheckResult:
    """SC-1: Check CWE ID presence on security findings.

    At least 80% of security findings should have CWE IDs for proper
    vulnerability classification and tracking.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    total_security = 0
    with_cwe = 0
    missing_cwe_samples = []

    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            if _is_security_finding(smell):
                total_security += 1
                cwe_id = _extract_cwe_id(smell)
                if cwe_id:
                    with_cwe += 1
                elif len(missing_cwe_samples) < 5:
                    missing_cwe_samples.append({
                        "file": file_info.get("path"),
                        "rule_id": smell.get("rule_id"),
                        "dd_smell_id": smell.get("dd_smell_id"),
                    })

    if total_security == 0:
        return CheckResult(
            check_id="SC-1",
            name="CWE ID presence",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No security findings to evaluate for CWE presence",
            evidence={"total_security": 0},
        )

    cwe_rate = with_cwe / total_security * 100
    passed = cwe_rate >= 80

    return CheckResult(
        check_id="SC-1",
        name="CWE ID presence",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=cwe_rate / 100,
        message=f"{cwe_rate:.1f}% of security findings have CWE IDs ({with_cwe}/{total_security})",
        evidence={
            "total_security_findings": total_security,
            "findings_with_cwe": with_cwe,
            "cwe_rate": round(cwe_rate, 1),
            "missing_cwe_samples": missing_cwe_samples,
        },
    )


def check_owasp_coverage(analysis: dict) -> CheckResult:
    """SC-2: Check OWASP Top 10 category coverage.

    Security findings should map to OWASP Top 10 categories for
    standardized vulnerability classification.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    owasp_counts: dict[str, int] = {code: 0 for code in OWASP_TOP_10}
    total_security = 0
    total_mapped = 0

    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            if _is_security_finding(smell):
                total_security += 1
                owasp_code = _map_to_owasp(smell)
                if owasp_code and owasp_code in owasp_counts:
                    owasp_counts[owasp_code] += 1
                    total_mapped += 1

    categories_detected = sum(1 for count in owasp_counts.values() if count > 0)

    if total_security == 0:
        return CheckResult(
            check_id="SC-2",
            name="OWASP Top 10 coverage",
            category=CheckCategory.COVERAGE,
            passed=True,
            score=1.0,
            message="No security findings to evaluate for OWASP coverage",
            evidence={"total_security": 0},
        )

    # Expect at least 2 OWASP categories if there are security findings
    passed = categories_detected >= 2 or total_security < 5

    return CheckResult(
        check_id="SC-2",
        name="OWASP Top 10 coverage",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=min(1.0, categories_detected / 3),  # Max score at 3+ categories
        message=f"{categories_detected} OWASP categories detected, {total_mapped}/{total_security} findings mapped",
        evidence={
            "total_security_findings": total_security,
            "findings_mapped_to_owasp": total_mapped,
            "owasp_categories_detected": categories_detected,
            "owasp_breakdown": {
                f"{code}: {OWASP_TOP_10[code]}": count
                for code, count in owasp_counts.items()
                if count > 0
            },
        },
    )


def check_sql_injection_detection(
    analysis: dict,
    ground_truth: dict[str, dict],
) -> CheckResult:
    """SC-3: Check SQL injection detection rate.

    SQL injection is a critical vulnerability (OWASP A03). Detection rate
    should be >= 80% for production readiness.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis

    expected = 0
    detected = 0

    # Count expected SQL injection from ground truth
    for lang, lang_gt in ground_truth.items():
        for filename, file_gt in lang_gt.get("files", {}).items():
            for expected_smell in file_gt.get("expected_smells", []):
                smell_id = expected_smell.get("smell_id", "").upper()
                if "SQL_INJECTION" in smell_id:
                    expected += expected_smell.get("count", 0)

    # Count detected SQL injection
    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            dd_smell_id = smell.get("dd_smell_id", "").upper()
            rule_id = smell.get("rule_id", "").lower()
            message = smell.get("message", "").lower()

            if (
                "SQL_INJECTION" in dd_smell_id
                or "sql-injection" in rule_id
                or "sql injection" in message
            ):
                detected += 1

    if expected == 0:
        return CheckResult(
            check_id="SC-3",
            name="SQL injection detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0 if detected == 0 else 0.5,
            message=f"No SQL injection expected in ground truth, found {detected}",
            evidence={"expected": 0, "detected": detected},
        )

    detection_rate = detected / expected * 100 if expected > 0 else 0
    passed = detection_rate >= 80

    return CheckResult(
        check_id="SC-3",
        name="SQL injection detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=min(1.0, detection_rate / 100),
        message=f"SQL injection detection rate: {detection_rate:.1f}% ({detected}/{expected})",
        evidence={
            "expected": expected,
            "detected": detected,
            "detection_rate": round(detection_rate, 1),
        },
    )


def check_xss_detection(
    analysis: dict,
    ground_truth: dict[str, dict],
) -> CheckResult:
    """SC-4: Check XSS detection rate.

    XSS is a critical injection vulnerability (OWASP A03). Detection rate
    should be >= 70% for production readiness.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis

    expected = 0
    detected = 0

    # Count expected XSS from ground truth
    for lang, lang_gt in ground_truth.items():
        for filename, file_gt in lang_gt.get("files", {}).items():
            for expected_smell in file_gt.get("expected_smells", []):
                smell_id = expected_smell.get("smell_id", "").upper()
                if "XSS" in smell_id:
                    expected += expected_smell.get("count", 0)

    # Count detected XSS
    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            dd_smell_id = smell.get("dd_smell_id", "").upper()
            rule_id = smell.get("rule_id", "").lower()
            message = smell.get("message", "").lower()

            if (
                "XSS" in dd_smell_id
                or "xss" in rule_id
                or "cross-site scripting" in message
            ):
                detected += 1

    if expected == 0:
        return CheckResult(
            check_id="SC-4",
            name="XSS detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0 if detected == 0 else 0.5,
            message=f"No XSS expected in ground truth, found {detected}",
            evidence={"expected": 0, "detected": detected},
        )

    detection_rate = detected / expected * 100 if expected > 0 else 0
    passed = detection_rate >= 70

    return CheckResult(
        check_id="SC-4",
        name="XSS detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=min(1.0, detection_rate / 100),
        message=f"XSS detection rate: {detection_rate:.1f}% ({detected}/{expected})",
        evidence={
            "expected": expected,
            "detected": detected,
            "detection_rate": round(detection_rate, 1),
        },
    )


def check_command_injection_detection(
    analysis: dict,
    ground_truth: dict[str, dict],
) -> CheckResult:
    """SC-5: Check command injection detection rate.

    Command injection is a critical vulnerability (OWASP A03). Detection rate
    should be >= 70% for production readiness.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis

    expected = 0
    detected = 0

    # Count expected command injection from ground truth
    for lang, lang_gt in ground_truth.items():
        for filename, file_gt in lang_gt.get("files", {}).items():
            for expected_smell in file_gt.get("expected_smells", []):
                smell_id = expected_smell.get("smell_id", "").upper()
                if "COMMAND_INJECTION" in smell_id or "CMD_INJECTION" in smell_id:
                    expected += expected_smell.get("count", 0)

    # Count detected command injection
    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            dd_smell_id = smell.get("dd_smell_id", "").upper()
            rule_id = smell.get("rule_id", "").lower()
            message = smell.get("message", "").lower()

            if (
                "COMMAND_INJECTION" in dd_smell_id
                or "CMD_INJECTION" in dd_smell_id
                or "command-injection" in rule_id
                or "command injection" in message
                or ("subprocess" in message and "user" in message)
                or ("os.system" in message)
            ):
                detected += 1

    if expected == 0:
        return CheckResult(
            check_id="SC-5",
            name="Command injection detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0 if detected == 0 else 0.5,
            message=f"No command injection expected in ground truth, found {detected}",
            evidence={"expected": 0, "detected": detected},
        )

    detection_rate = detected / expected * 100 if expected > 0 else 0
    passed = detection_rate >= 70

    return CheckResult(
        check_id="SC-5",
        name="Command injection detection",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=min(1.0, detection_rate / 100),
        message=f"Command injection detection rate: {detection_rate:.1f}% ({detected}/{expected})",
        evidence={
            "expected": expected,
            "detected": detected,
            "detection_rate": round(detection_rate, 1),
        },
    )


def check_severity_distribution(analysis: dict) -> CheckResult:
    """SC-6: Check security finding severity distribution.

    Security findings should have proper severity classification (ERROR, WARNING, INFO).
    At least 80% should have severity assigned.
    """
    results = analysis.get("results", analysis) if "results" in analysis else analysis

    severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0, "UNKNOWN": 0}
    total_security = 0

    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            if _is_security_finding(smell):
                total_security += 1
                severity = smell.get("severity", "UNKNOWN").upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
                else:
                    severity_counts["UNKNOWN"] += 1

    if total_security == 0:
        return CheckResult(
            check_id="SC-6",
            name="Security severity distribution",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="No security findings to evaluate severity",
            evidence={"total_security": 0},
        )

    known_severity = total_security - severity_counts["UNKNOWN"]
    severity_rate = known_severity / total_security * 100

    passed = severity_rate >= 80

    return CheckResult(
        check_id="SC-6",
        name="Security severity distribution",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=severity_rate / 100,
        message=f"{severity_rate:.1f}% of security findings have severity ({known_severity}/{total_security})",
        evidence={
            "total_security_findings": total_security,
            "severity_distribution": severity_counts,
            "severity_assignment_rate": round(severity_rate, 1),
        },
    )


def run_security_checks(
    analysis: dict,
    ground_truth_dir: str | Path,
) -> list[CheckResult]:
    """Run all security checks (SC-1 to SC-6)."""
    results = []
    ground_truth = load_all_ground_truth(ground_truth_dir)

    # SC-1: CWE ID presence
    results.append(check_cwe_presence(analysis))

    # SC-2: OWASP coverage
    results.append(check_owasp_coverage(analysis))

    # SC-3: SQL injection detection
    results.append(check_sql_injection_detection(analysis, ground_truth))

    # SC-4: XSS detection
    results.append(check_xss_detection(analysis, ground_truth))

    # SC-5: Command injection detection
    results.append(check_command_injection_detection(analysis, ground_truth))

    # SC-6: Severity distribution
    results.append(check_severity_distribution(analysis))

    return results
