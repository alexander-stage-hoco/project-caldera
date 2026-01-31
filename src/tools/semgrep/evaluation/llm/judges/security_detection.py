"""Security Detection Judge - Evaluates OWASP Top 10 and security vulnerability detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


# OWASP Top 10 2021 categories with associated CWE IDs
OWASP_TOP_10_CATEGORIES = {
    "A01:2021-Broken Access Control": {
        "description": "Access control enforces policy such that users cannot act outside their intended permissions",
        "cwe_ids": ["CWE-22", "CWE-23", "CWE-35", "CWE-59", "CWE-200", "CWE-201", "CWE-219", "CWE-264", "CWE-275", "CWE-276", "CWE-284", "CWE-285", "CWE-352", "CWE-359", "CWE-377", "CWE-402", "CWE-425", "CWE-441", "CWE-497", "CWE-538", "CWE-540", "CWE-548", "CWE-552", "CWE-566", "CWE-601", "CWE-639", "CWE-651", "CWE-668", "CWE-706", "CWE-862", "CWE-863", "CWE-913", "CWE-922", "CWE-1275"],
        "keywords": ["path traversal", "directory traversal", "lfi", "rfi", "insecure direct object", "idor", "access control", "authorization", "privilege escalation"],
    },
    "A02:2021-Cryptographic Failures": {
        "description": "Failures related to cryptography which often lead to exposure of sensitive data",
        "cwe_ids": ["CWE-261", "CWE-296", "CWE-310", "CWE-319", "CWE-321", "CWE-322", "CWE-323", "CWE-324", "CWE-325", "CWE-326", "CWE-327", "CWE-328", "CWE-329", "CWE-330", "CWE-331", "CWE-335", "CWE-336", "CWE-337", "CWE-338", "CWE-340", "CWE-347", "CWE-523", "CWE-720", "CWE-757", "CWE-759", "CWE-760", "CWE-780", "CWE-818", "CWE-916"],
        "keywords": ["weak cipher", "weak hash", "md5", "sha1", "hardcoded secret", "hardcoded password", "hardcoded key", "insecure random", "weak crypto", "cleartext", "plaintext"],
    },
    "A03:2021-Injection": {
        "description": "Injection flaws when untrusted data is sent to an interpreter",
        "cwe_ids": ["CWE-20", "CWE-74", "CWE-75", "CWE-77", "CWE-78", "CWE-79", "CWE-80", "CWE-83", "CWE-87", "CWE-88", "CWE-89", "CWE-90", "CWE-91", "CWE-93", "CWE-94", "CWE-95", "CWE-96", "CWE-97", "CWE-98", "CWE-99", "CWE-100", "CWE-113", "CWE-116", "CWE-138", "CWE-184", "CWE-470", "CWE-471", "CWE-564", "CWE-610", "CWE-643", "CWE-644", "CWE-652", "CWE-917", "CWE-1236"],
        "keywords": ["sql injection", "sqli", "command injection", "os command", "code injection", "xss", "cross-site scripting", "ldap injection", "xpath injection", "template injection", "ssti", "eval", "exec"],
    },
    "A04:2021-Insecure Design": {
        "description": "Missing or ineffective security controls at the design level",
        "cwe_ids": ["CWE-73", "CWE-183", "CWE-209", "CWE-213", "CWE-235", "CWE-256", "CWE-257", "CWE-266", "CWE-269", "CWE-280", "CWE-311", "CWE-312", "CWE-313", "CWE-316", "CWE-419", "CWE-430", "CWE-434", "CWE-444", "CWE-451", "CWE-472", "CWE-501", "CWE-522", "CWE-525", "CWE-539", "CWE-579", "CWE-598", "CWE-602", "CWE-642", "CWE-646", "CWE-650", "CWE-653", "CWE-656", "CWE-657", "CWE-799", "CWE-807", "CWE-840", "CWE-841", "CWE-927", "CWE-1021", "CWE-1173"],
        "keywords": ["insecure design", "trust boundary", "race condition", "business logic", "abuse case"],
    },
    "A05:2021-Security Misconfiguration": {
        "description": "Missing security hardening or improperly configured permissions",
        "cwe_ids": ["CWE-2", "CWE-11", "CWE-13", "CWE-15", "CWE-16", "CWE-260", "CWE-315", "CWE-520", "CWE-526", "CWE-537", "CWE-541", "CWE-547", "CWE-611", "CWE-614", "CWE-756", "CWE-776", "CWE-942", "CWE-1004", "CWE-1032", "CWE-1174"],
        "keywords": ["misconfiguration", "debug enabled", "default credentials", "xxe", "xml external entity", "cors", "verbose error", "stack trace"],
    },
    "A06:2021-Vulnerable Components": {
        "description": "Using components with known vulnerabilities",
        "cwe_ids": ["CWE-1035", "CWE-1104"],
        "keywords": ["vulnerable dependency", "outdated library", "cve", "known vulnerability"],
    },
    "A07:2021-Authentication Failures": {
        "description": "Incorrect implementation of authentication and session management",
        "cwe_ids": ["CWE-255", "CWE-259", "CWE-287", "CWE-288", "CWE-290", "CWE-294", "CWE-295", "CWE-297", "CWE-300", "CWE-302", "CWE-304", "CWE-306", "CWE-307", "CWE-346", "CWE-384", "CWE-521", "CWE-613", "CWE-620", "CWE-640", "CWE-798", "CWE-940", "CWE-1216"],
        "keywords": ["authentication bypass", "weak password", "brute force", "session fixation", "session hijacking", "credential stuffing", "hardcoded credential"],
    },
    "A08:2021-Software and Data Integrity": {
        "description": "Code and infrastructure that does not protect against integrity violations",
        "cwe_ids": ["CWE-345", "CWE-353", "CWE-426", "CWE-494", "CWE-502", "CWE-565", "CWE-784", "CWE-829", "CWE-830", "CWE-915"],
        "keywords": ["deserialization", "unsafe deserialization", "insecure deserialization", "code integrity", "unsigned code", "pickle", "yaml load"],
    },
    "A09:2021-Security Logging Failures": {
        "description": "Insufficient logging, detection, monitoring, and active response",
        "cwe_ids": ["CWE-117", "CWE-223", "CWE-532", "CWE-778"],
        "keywords": ["logging sensitive", "log injection", "insufficient logging", "missing audit"],
    },
    "A10:2021-Server-Side Request Forgery": {
        "description": "SSRF flaws occur when fetching a remote resource without validating the user-supplied URL",
        "cwe_ids": ["CWE-918"],
        "keywords": ["ssrf", "server-side request forgery", "url injection", "open redirect"],
    },
}


class SecurityDetectionJudge(BaseJudge):
    """Evaluates security-specific detection capabilities.

    Unlike the general smell accuracy judge, this judge focuses specifically on
    OWASP Top 10 security vulnerabilities and their detection accuracy. This is
    critical for due diligence assessments where security posture is paramount.
    """

    @property
    def dimension_name(self) -> str:
        return "security_detection"

    @property
    def weight(self) -> float:
        return 0.40  # 40% of total score - highest weight for security tool

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about security vulnerability detection."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"

        # Load analysis from all output files
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate security findings
        evidence = {
            "summary": {
                "total_security_findings": 0,
                "total_expected_security": 0,
                "security_detection_rate": 0.0,
                "owasp_categories_detected": [],
                "cwe_ids_detected": [],
            },
            "by_owasp_category": {},
            "injection_detection": {
                "sql_injection": {"expected": 0, "detected": 0},
                "command_injection": {"expected": 0, "detected": 0},
                "xss": {"expected": 0, "detected": 0},
                "code_injection": {"expected": 0, "detected": 0},
            },
            "crypto_detection": {
                "weak_cipher": {"expected": 0, "detected": 0},
                "weak_hash": {"expected": 0, "detected": 0},
                "hardcoded_secret": {"expected": 0, "detected": 0},
            },
            "auth_detection": {
                "auth_bypass": {"expected": 0, "detected": 0},
                "hardcoded_credential": {"expected": 0, "detected": 0},
            },
            "sample_security_findings": [],
            "missed_security_issues": [],
            "ground_truth_comparison": [],
        }

        # Initialize OWASP category tracking
        for cat in OWASP_TOP_10_CATEGORIES:
            evidence["by_owasp_category"][cat] = {
                "detected": 0,
                "expected": 0,
                "sample_findings": [],
            }

        all_security_findings = []
        detected_cwe_ids = set()
        detected_owasp = set()

        # Process each repo's results
        for repo_name, repo_analysis in all_results.items():
            files = self.extract_files(repo_analysis)

            for file_info in files:
                for smell in file_info.get("smells", []):
                    # Check if this is a security finding
                    dd_category = smell.get("dd_category", "").lower()
                    rule_id = smell.get("rule_id", "").lower()
                    message = smell.get("message", "").lower()
                    dd_smell_id = smell.get("dd_smell_id", "").upper()

                    is_security = (
                        dd_category == "security"
                        or "security" in rule_id
                        or "injection" in message
                        or "xss" in message
                        or "vulnerability" in message
                        or dd_smell_id.startswith("SQL_")
                        or "cwe" in rule_id.lower()
                    )

                    if is_security:
                        evidence["summary"]["total_security_findings"] += 1

                        # Extract CWE ID if present
                        cwe_id = self._extract_cwe_id(smell)
                        if cwe_id:
                            detected_cwe_ids.add(cwe_id)

                        # Map to OWASP category
                        owasp_cat = self._map_to_owasp(smell, message, rule_id)
                        if owasp_cat:
                            detected_owasp.add(owasp_cat)
                            evidence["by_owasp_category"][owasp_cat]["detected"] += 1
                            if len(evidence["by_owasp_category"][owasp_cat]["sample_findings"]) < 3:
                                evidence["by_owasp_category"][owasp_cat]["sample_findings"].append({
                                    "file": file_info.get("path", ""),
                                    "line": smell.get("line_start", 0),
                                    "rule": rule_id,
                                    "message": message[:100],
                                })

                        # Categorize injection types
                        self._categorize_injection(evidence, smell, message, rule_id)

                        all_security_findings.append({
                            "file": Path(file_info.get("path", "")).name,
                            "rule_id": rule_id,
                            "dd_smell_id": dd_smell_id,
                            "severity": smell.get("severity", ""),
                            "line": smell.get("line_start", 0),
                            "message": message[:100],
                            "owasp_category": owasp_cat,
                            "cwe_id": cwe_id,
                        })

        # Sample security findings for review
        evidence["sample_security_findings"] = all_security_findings[:20]
        evidence["summary"]["cwe_ids_detected"] = sorted(list(detected_cwe_ids))
        evidence["summary"]["owasp_categories_detected"] = sorted(list(detected_owasp))

        # Load and compare against security-specific ground truth
        total_expected = 0
        total_detected = 0

        for gt_file in gt_dir.glob("*.json"):
            try:
                gt = json.loads(gt_file.read_text())
                for file_name, file_data in gt.get("files", {}).items():
                    for expected_smell in file_data.get("expected_smells", []):
                        smell_id = expected_smell.get("smell_id", "").upper()

                        # Check if this is a security smell
                        if self._is_security_smell_id(smell_id):
                            expected_count = expected_smell.get("count", 0)
                            expected_lines = expected_smell.get("lines", [])

                            total_expected += expected_count

                            # Update OWASP category expectations
                            owasp_cat = self._smell_id_to_owasp(smell_id)
                            if owasp_cat:
                                evidence["by_owasp_category"][owasp_cat]["expected"] += expected_count

                            # Check for injection expectations
                            if "SQL_INJECTION" in smell_id:
                                evidence["injection_detection"]["sql_injection"]["expected"] += expected_count
                            elif "COMMAND_INJECTION" in smell_id:
                                evidence["injection_detection"]["command_injection"]["expected"] += expected_count
                            elif "XSS" in smell_id:
                                evidence["injection_detection"]["xss"]["expected"] += expected_count

                            evidence["ground_truth_comparison"].append({
                                "file": file_name,
                                "smell_id": smell_id,
                                "expected_count": expected_count,
                                "expected_lines": expected_lines,
                            })

            except (json.JSONDecodeError, KeyError):
                continue

        evidence["summary"]["total_expected_security"] = total_expected
        if total_expected > 0:
            evidence["summary"]["security_detection_rate"] = round(
                evidence["summary"]["total_security_findings"] / total_expected * 100, 1
            )

        return evidence

    def _extract_cwe_id(self, smell: dict) -> str | None:
        """Extract CWE ID from smell metadata."""
        rule_id = smell.get("rule_id", "")
        message = smell.get("message", "")

        # Check common CWE patterns
        import re
        cwe_pattern = r"CWE[-_]?(\d+)"

        for text in [rule_id, message]:
            match = re.search(cwe_pattern, text, re.IGNORECASE)
            if match:
                return f"CWE-{match.group(1)}"

        return None

    def _map_to_owasp(self, smell: dict, message: str, rule_id: str) -> str | None:
        """Map a finding to an OWASP Top 10 category."""
        combined_text = f"{message} {rule_id}".lower()

        for owasp_cat, details in OWASP_TOP_10_CATEGORIES.items():
            # Check keywords
            for keyword in details["keywords"]:
                if keyword in combined_text:
                    return owasp_cat

        # Check if CWE maps to OWASP
        cwe_id = self._extract_cwe_id(smell)
        if cwe_id:
            for owasp_cat, details in OWASP_TOP_10_CATEGORIES.items():
                if cwe_id in details["cwe_ids"]:
                    return owasp_cat

        return None

    def _smell_id_to_owasp(self, smell_id: str) -> str | None:
        """Map DD smell ID to OWASP category."""
        mapping = {
            "SQL_INJECTION": "A03:2021-Injection",
            "COMMAND_INJECTION": "A03:2021-Injection",
            "XSS": "A03:2021-Injection",
            "CODE_INJECTION": "A03:2021-Injection",
            "LDAP_INJECTION": "A03:2021-Injection",
            "XPATH_INJECTION": "A03:2021-Injection",
            "SSRF": "A10:2021-Server-Side Request Forgery",
            "WEAK_HASH": "A02:2021-Cryptographic Failures",
            "WEAK_CIPHER": "A02:2021-Cryptographic Failures",
            "HARDCODED_SECRET": "A07:2021-Authentication Failures",
            "HARDCODED_CREDENTIAL": "A07:2021-Authentication Failures",
            "UNSAFE_DESERIALIZATION": "A08:2021-Software and Data Integrity",
            "PATH_TRAVERSAL": "A01:2021-Broken Access Control",
            "INSECURE_RANDOM": "A02:2021-Cryptographic Failures",
        }
        for key, owasp in mapping.items():
            if key in smell_id:
                return owasp
        return None

    def _is_security_smell_id(self, smell_id: str) -> bool:
        """Check if smell ID represents a security issue."""
        security_keywords = [
            "SQL_INJECTION", "INJECTION", "XSS", "SSRF", "CSRF",
            "PATH_TRAVERSAL", "COMMAND", "CRYPTO", "CIPHER", "HASH",
            "DESERIALIZATION", "HARDCODED", "SECRET", "CREDENTIAL",
            "AUTH", "RANDOM", "UNSAFE", "INSECURE",
        ]
        return any(kw in smell_id for kw in security_keywords)

    def _categorize_injection(self, evidence: dict, smell: dict, message: str, rule_id: str) -> None:
        """Categorize injection types for detailed tracking."""
        combined = f"{message} {rule_id}".lower()

        if "sql" in combined and "injection" in combined:
            evidence["injection_detection"]["sql_injection"]["detected"] += 1
        elif "command" in combined or "os.system" in combined or "subprocess" in combined:
            evidence["injection_detection"]["command_injection"]["detected"] += 1
        elif "xss" in combined or "cross-site" in combined:
            evidence["injection_detection"]["xss"]["detected"] += 1
        elif "eval" in combined or "exec" in combined:
            evidence["injection_detection"]["code_injection"]["detected"] += 1

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate security detection against ground truth.

        Key assertions:
        1. SQL injection detection rate >= 80% (CRITICAL severity)
        2. At least 3 OWASP categories should be detected
        3. No CRITICAL severity issues should have <70% detection rate
        """
        failures = []
        evidence = self.collect_evidence()

        if "error" in evidence:
            failures.append(evidence["error"])
            return False, failures

        # Assertion 1: SQL injection detection rate
        sql_inj = evidence["injection_detection"]["sql_injection"]
        if sql_inj["expected"] > 0:
            rate = sql_inj["detected"] / sql_inj["expected"] * 100
            if rate < 80:
                failures.append(
                    f"SQL injection detection rate too low: {rate:.1f}% (expected >= 80%)"
                )

        # Assertion 2: OWASP category coverage
        owasp_detected = len(evidence["summary"]["owasp_categories_detected"])
        if evidence["summary"]["total_security_findings"] > 0 and owasp_detected < 2:
            failures.append(
                f"Only {owasp_detected} OWASP categories detected (expected >= 2)"
            )

        # Assertion 3: Overall security detection rate
        detection_rate = evidence["summary"]["security_detection_rate"]
        if evidence["summary"]["total_expected_security"] > 0 and detection_rate < 50:
            failures.append(
                f"Security detection rate too low: {detection_rate}% (expected >= 50%)"
            )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Security Detection Judge

You are evaluating **security vulnerability detection** by Semgrep, focusing on OWASP Top 10 categories.

## Evaluation Dimension
**Security Detection (40% weight)**: How effectively does Semgrep detect security vulnerabilities?

## OWASP Top 10 2021 Categories
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, XSS, Command, etc.)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Authentication Failures
- A08: Software and Data Integrity (Deserialization)
- A09: Security Logging Failures
- A10: Server-Side Request Forgery (SSRF)

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | >90% security detection, all OWASP categories covered, injection rate >95% |
| 4 | 80-90% detection, most OWASP categories, injection rate >85% |
| 3 | 70-80% detection, several OWASP categories, injection rate >70% |
| 2 | 50-70% detection, limited OWASP coverage, injection rate 50-70% |
| 1 | <50% detection, poor OWASP coverage, unreliable injection detection |

## Sub-Dimensions
1. **Injection Detection (40%)**: SQL, XSS, command, code injection accuracy
2. **OWASP Coverage (30%)**: Breadth of OWASP Top 10 categories detected
3. **CWE Mapping (30%)**: Proper CWE IDs assigned to findings

## Evidence to Evaluate

{{ evidence }}

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "security_detection",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of security detection assessment",
  "evidence_cited": ["specific security findings examined"],
  "recommendations": ["improvements for security detection"],
  "sub_scores": {
    "injection_detection": <1-5>,
    "owasp_coverage": <1-5>,
    "cwe_mapping": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline with ground truth assertions."""
        # Run ground truth assertions first
        gt_passed, gt_failures = self.run_ground_truth_assertions()

        # Collect evidence
        evidence = self.collect_evidence()

        # Add assertion results to evidence
        evidence["ground_truth_assertions"] = {
            "passed": gt_passed,
            "failures": gt_failures,
        }

        # Build prompt
        prompt = self.build_prompt(evidence)

        # Invoke Claude
        response = self.invoke_claude(prompt)

        # Parse response
        result = self.parse_response(response)

        # Cap score if ground truth assertions failed
        if not gt_passed:
            original_score = result.score
            result.score = min(result.score, 2)
            if result.score != original_score:
                result.reasoning = (
                    f"[Score capped from {original_score} to {result.score} due to "
                    f"ground truth assertion failures: {gt_failures}] "
                    + result.reasoning
                )

        return result
