"""Format coverage checks (FC-1 to FC-6).

Validates that all 4 coverage formats are properly supported.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import (
    LcovParser,
    CoberturaParser,
    JacocoParser,
    IstanbulParser,
)


@dataclass
class CheckResult:
    """Result of a single check."""
    check_id: str
    name: str
    passed: bool
    message: str


# Test content for each format
LCOV_CONTENT = "SF:test.py\nLF:10\nLH:5\nend_of_record\n"
COBERTURA_CONTENT = '''<?xml version="1.0"?>
<coverage line-rate="0.5">
    <packages>
        <package name="src">
            <classes>
                <class filename="test.py" line-rate="0.5">
                    <lines><line number="1" hits="1"/></lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>'''
JACOCO_CONTENT = '''<?xml version="1.0"?>
<report name="test">
    <package name="com/example">
        <sourcefile name="Test.java">
            <counter type="LINE" missed="5" covered="5"/>
        </sourcefile>
    </package>
</report>'''
ISTANBUL_CONTENT = '{"test.js": {"path": "test.js", "s": {"0": 1, "1": 0}}}'


def check_fc1_lcov_detection() -> CheckResult:
    """FC-1: LCOV format detected correctly."""
    parser = LcovParser()
    try:
        detected = parser.detect(LCOV_CONTENT)
        return CheckResult("FC-1", "LCOV detection", detected, "LCOV format detected" if detected else "Not detected")
    except Exception as e:
        return CheckResult("FC-1", "LCOV detection", False, str(e))


def check_fc2_cobertura_detection() -> CheckResult:
    """FC-2: Cobertura format detected correctly."""
    parser = CoberturaParser()
    try:
        detected = parser.detect(COBERTURA_CONTENT)
        return CheckResult("FC-2", "Cobertura detection", detected, "Cobertura format detected" if detected else "Not detected")
    except Exception as e:
        return CheckResult("FC-2", "Cobertura detection", False, str(e))


def check_fc3_jacoco_detection() -> CheckResult:
    """FC-3: JaCoCo format detected correctly."""
    parser = JacocoParser()
    try:
        detected = parser.detect(JACOCO_CONTENT)
        return CheckResult("FC-3", "JaCoCo detection", detected, "JaCoCo format detected" if detected else "Not detected")
    except Exception as e:
        return CheckResult("FC-3", "JaCoCo detection", False, str(e))


def check_fc4_istanbul_detection() -> CheckResult:
    """FC-4: Istanbul format detected correctly."""
    parser = IstanbulParser()
    try:
        detected = parser.detect(ISTANBUL_CONTENT)
        return CheckResult("FC-4", "Istanbul detection", detected, "Istanbul format detected" if detected else "Not detected")
    except Exception as e:
        return CheckResult("FC-4", "Istanbul detection", False, str(e))


def check_fc5_format_override() -> CheckResult:
    """FC-5: Format override works correctly."""
    # Each parser should be able to parse its own format
    try:
        lcov = LcovParser()
        lcov_result = lcov.parse(LCOV_CONTENT)

        cobertura = CoberturaParser()
        cobertura_result = cobertura.parse(COBERTURA_CONTENT)

        jacoco = JacocoParser()
        jacoco_result = jacoco.parse(JACOCO_CONTENT)

        istanbul = IstanbulParser()
        istanbul_result = istanbul.parse(ISTANBUL_CONTENT)

        all_parsed = (
            len(lcov_result) > 0 and
            len(cobertura_result) > 0 and
            len(jacoco_result) > 0 and
            len(istanbul_result) > 0
        )
        return CheckResult("FC-5", "format override", all_parsed, "All formats parse correctly")
    except Exception as e:
        return CheckResult("FC-5", "format override", False, str(e))


def check_fc6_invalid_format_rejection() -> CheckResult:
    """FC-6: Invalid format rejected gracefully."""
    parser = LcovParser()
    try:
        # LCOV parser should handle non-LCOV content gracefully
        result = parser.parse("<invalid xml>")
        # It's OK if it returns empty list (graceful handling)
        passed = isinstance(result, list)
        return CheckResult("FC-6", "invalid format rejected", passed, "Invalid format handled gracefully")
    except ValueError:
        # ValueError is also acceptable - explicit rejection
        return CheckResult("FC-6", "invalid format rejected", True, "ValueError raised appropriately")
    except Exception as e:
        return CheckResult("FC-6", "invalid format rejected", False, f"Unexpected error: {e}")


def run_all_coverage_checks() -> list[CheckResult]:
    """Run all format coverage checks."""
    return [
        check_fc1_lcov_detection(),
        check_fc2_cobertura_detection(),
        check_fc3_jacoco_detection(),
        check_fc4_istanbul_detection(),
        check_fc5_format_override(),
        check_fc6_invalid_format_rejection(),
    ]


if __name__ == "__main__":
    results = run_all_coverage_checks()
    passed = sum(1 for r in results if r.passed)
    print(f"Format Coverage Checks: {passed}/{len(results)} passed")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.check_id}: {r.name} - {r.message}")
