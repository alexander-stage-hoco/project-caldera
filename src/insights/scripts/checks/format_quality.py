"""
Format quality checks (IN-FQ-*) for Insights reports.

These checks verify HTML/Markdown output quality.
"""

import re
from typing import Any

from . import register_check, CheckOutput, CheckResult


@register_check(
    check_id="IN-FQ-1",
    name="HTML Well-Formed",
    description="Verify HTML output is well-formed",
    dimension="format_quality",
    weight=1.0,
)
def check_html_wellformed(
    report_content: str,
    format: str = "html",
    **kwargs: Any,
) -> CheckOutput:
    """Check that HTML output is well-formed."""
    if format != "html":
        return CheckOutput(
            check_id="IN-FQ-1",
            name="HTML Well-Formed",
            result=CheckResult.SKIP,
            score=1.0,
            message="Not an HTML report",
        )

    # Basic structural checks
    issues = []

    if "<!DOCTYPE html>" not in report_content:
        issues.append("Missing DOCTYPE declaration")

    if "<html" not in report_content:
        issues.append("Missing <html> tag")

    if "</html>" not in report_content:
        issues.append("Missing </html> closing tag")

    if "<head>" not in report_content or "</head>" not in report_content:
        issues.append("Missing or unclosed <head> section")

    if "<body>" not in report_content or "</body>" not in report_content:
        issues.append("Missing or unclosed <body> section")

    # Check for unclosed tags (basic check)
    open_tags = re.findall(r"<(section|div|table|thead|tbody|tr|th|td)[^>]*>", report_content)
    close_tags = re.findall(r"</(section|div|table|thead|tbody|tr|th|td)>", report_content)

    if len(open_tags) != len(close_tags):
        issues.append(f"Mismatched tags: {len(open_tags)} open, {len(close_tags)} close")

    if not issues:
        return CheckOutput(
            check_id="IN-FQ-1",
            name="HTML Well-Formed",
            result=CheckResult.PASS,
            score=1.0,
            message="HTML is well-formed",
        )

    score = max(0.0, 1.0 - (len(issues) * 0.2))

    return CheckOutput(
        check_id="IN-FQ-1",
        name="HTML Well-Formed",
        result=CheckResult.FAIL,
        score=score,
        message=f"{len(issues)} structural issues found",
        details={"issues": issues},
    )


@register_check(
    check_id="IN-FQ-2",
    name="Required HTML Elements Present",
    description="Verify required HTML elements are present",
    dimension="format_quality",
    weight=0.8,
)
def check_html_elements(
    report_content: str,
    format: str = "html",
    **kwargs: Any,
) -> CheckOutput:
    """Check that required HTML elements are present."""
    if format != "html":
        return CheckOutput(
            check_id="IN-FQ-2",
            name="Required HTML Elements Present",
            result=CheckResult.SKIP,
            score=1.0,
            message="Not an HTML report",
        )

    required_elements = [
        ("<title>", "Title tag"),
        ("<header>", "Header element"),
        ("<main>", "Main content element"),
        ("<footer>", "Footer element"),
        ('id="toc"', "Table of contents"),
        ("class=\"report-section\"", "Report section"),
    ]

    missing = []
    for pattern, name in required_elements:
        if pattern not in report_content:
            missing.append(name)

    if not missing:
        return CheckOutput(
            check_id="IN-FQ-2",
            name="Required HTML Elements Present",
            result=CheckResult.PASS,
            score=1.0,
            message="All required elements present",
        )

    score = (len(required_elements) - len(missing)) / len(required_elements)

    return CheckOutput(
        check_id="IN-FQ-2",
        name="Required HTML Elements Present",
        result=CheckResult.FAIL,
        score=score,
        message=f"Missing: {', '.join(missing)}",
        details={"missing": missing},
    )


@register_check(
    check_id="IN-FQ-3",
    name="No Forbidden HTML Patterns",
    description="Verify no forbidden patterns in HTML",
    dimension="format_quality",
    weight=0.6,
)
def check_no_forbidden_patterns(
    report_content: str,
    format: str = "html",
    **kwargs: Any,
) -> CheckOutput:
    """Check that no forbidden patterns appear in HTML."""
    if format != "html":
        return CheckOutput(
            check_id="IN-FQ-3",
            name="No Forbidden HTML Patterns",
            result=CheckResult.SKIP,
            score=1.0,
            message="Not an HTML report",
        )

    forbidden_patterns = [
        (r"<script\b", "Inline script tags"),
        (r"onclick=", "Inline event handlers"),
        (r"javascript:", "JavaScript URLs"),
        (r"{{.*}}", "Unrendered template syntax"),
        (r"\bNone\b", "Python None values"),
        (r"\bNaN\b", "NaN values"),
    ]

    found = []
    for pattern, name in forbidden_patterns:
        if re.search(pattern, report_content):
            found.append(name)

    if not found:
        return CheckOutput(
            check_id="IN-FQ-3",
            name="No Forbidden HTML Patterns",
            result=CheckResult.PASS,
            score=1.0,
            message="No forbidden patterns found",
        )

    score = max(0.0, 1.0 - (len(found) * 0.2))

    return CheckOutput(
        check_id="IN-FQ-3",
        name="No Forbidden HTML Patterns",
        result=CheckResult.FAIL,
        score=score,
        message=f"Found: {', '.join(found)}",
        details={"found": found},
    )


@register_check(
    check_id="IN-FQ-4",
    name="Markdown Headers Valid",
    description="Verify Markdown headers are properly formatted",
    dimension="format_quality",
    weight=1.0,
)
def check_markdown_headers(
    report_content: str,
    format: str = "md",
    **kwargs: Any,
) -> CheckOutput:
    """Check that Markdown headers are valid."""
    if format != "md":
        return CheckOutput(
            check_id="IN-FQ-4",
            name="Markdown Headers Valid",
            result=CheckResult.SKIP,
            score=1.0,
            message="Not a Markdown report",
        )

    issues = []

    # Check for H1 header
    if not re.search(r"^# .+", report_content, re.MULTILINE):
        issues.append("Missing H1 header")

    # Check for H2 headers (sections)
    h2_count = len(re.findall(r"^## .+", report_content, re.MULTILINE))
    if h2_count == 0:
        issues.append("No H2 section headers")

    # Check for malformed headers (no space after #)
    malformed = re.findall(r"^#{1,6}[^# \n]", report_content, re.MULTILINE)
    if malformed:
        issues.append(f"{len(malformed)} malformed headers")

    if not issues:
        return CheckOutput(
            check_id="IN-FQ-4",
            name="Markdown Headers Valid",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Valid headers with {h2_count} sections",
        )

    return CheckOutput(
        check_id="IN-FQ-4",
        name="Markdown Headers Valid",
        result=CheckResult.FAIL,
        score=0.5 if issues else 1.0,
        message="; ".join(issues),
        details={"issues": issues, "h2_count": h2_count},
    )


@register_check(
    check_id="IN-FQ-5",
    name="Markdown Tables Valid",
    description="Verify Markdown tables are properly formatted",
    dimension="format_quality",
    weight=0.8,
)
def check_markdown_tables(
    report_content: str,
    format: str = "md",
    **kwargs: Any,
) -> CheckOutput:
    """Check that Markdown tables are valid."""
    if format != "md":
        return CheckOutput(
            check_id="IN-FQ-5",
            name="Markdown Tables Valid",
            result=CheckResult.SKIP,
            score=1.0,
            message="Not a Markdown report",
        )

    # Find all table patterns (header | separator | rows)
    table_pattern = r"(\|[^\n]+\|\n\|[-:\|\s]+\|\n(?:\|[^\n]+\|\n)+)"
    tables = re.findall(table_pattern, report_content)

    if not tables:
        return CheckOutput(
            check_id="IN-FQ-5",
            name="Markdown Tables Valid",
            result=CheckResult.SKIP,
            score=1.0,
            message="No tables found in report",
        )

    issues = []
    for i, table in enumerate(tables):
        lines = table.strip().split("\n")
        if len(lines) < 3:
            continue

        header_cols = lines[0].count("|") - 1
        sep_cols = lines[1].count("|") - 1

        if header_cols != sep_cols:
            issues.append(f"Table {i+1}: header ({header_cols}) vs separator ({sep_cols}) mismatch")

        # Check separator format
        if not re.match(r"^\|(\s*[-:]+\s*\|)+$", lines[1]):
            issues.append(f"Table {i+1}: invalid separator format")

    if not issues:
        return CheckOutput(
            check_id="IN-FQ-5",
            name="Markdown Tables Valid",
            result=CheckResult.PASS,
            score=1.0,
            message=f"All {len(tables)} tables are valid",
        )

    score = (len(tables) - len(issues)) / len(tables)

    return CheckOutput(
        check_id="IN-FQ-5",
        name="Markdown Tables Valid",
        result=CheckResult.FAIL,
        score=max(0.0, score),
        message=f"{len(issues)} table issues found",
        details={"issues": issues, "table_count": len(tables)},
    )


# Export list of checks
FORMAT_QUALITY_CHECKS = [
    "IN-FQ-1",
    "IN-FQ-2",
    "IN-FQ-3",
    "IN-FQ-4",
    "IN-FQ-5",
]
