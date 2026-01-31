"""Coverage checks (SQ-CV-*) for SonarQube evaluation."""

from . import (
    CheckCategory,
    CheckResult,
    get_nested,
)


REQUIRED_METRICS = [
    "ncloc",
    "complexity",
    "violations",
    "bugs",
    "vulnerabilities",
    "code_smells",
]


def check_metric_presence(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CV-1: Check that all required metrics are present in the catalog."""
    results = data.get("results", data)
    catalog = results.get("metric_catalog", [])
    available_keys = {m.get("key") for m in catalog}

    missing = [m for m in REQUIRED_METRICS if m not in available_keys]
    passed = len(missing) == 0
    score = (len(REQUIRED_METRICS) - len(missing)) / len(REQUIRED_METRICS)

    return CheckResult(
        check_id="SQ-CV-1",
        name="Metric presence",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Missing'} {len(REQUIRED_METRICS)} required metrics"
                + (f": {missing}" if missing else ""),
        evidence={
            "required": REQUIRED_METRICS,
            "available_count": len(available_keys),
            "missing": missing,
        },
    )


def check_rule_coverage(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CV-2: Check that triggered rules have metadata."""
    results = data.get("results", data)
    issues = results.get("issues", {}).get("items", [])
    rules = results.get("rules", {}).get("by_key", {})

    triggered_rules = {i.get("rule") for i in issues if i.get("rule")}
    covered_rules = [r for r in triggered_rules if r in rules]
    coverage_pct = len(covered_rules) / len(triggered_rules) * 100 if triggered_rules else 100

    threshold = 95.0
    passed = coverage_pct >= threshold
    score = min(coverage_pct / 100, 1.0)

    missing = [r for r in triggered_rules if r not in rules][:10]

    return CheckResult(
        check_id="SQ-CV-2",
        name="Rule coverage",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"Rule coverage {coverage_pct:.1f}% {'meets' if passed else 'below'} threshold {threshold}%",
        evidence={
            "triggered_rules": len(triggered_rules),
            "covered_rules": len(covered_rules),
            "coverage_pct": round(coverage_pct, 2),
            "missing_rules": missing,
        },
    )


def check_file_coverage(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CV-3: Check that files have measures."""
    results = data.get("results", data)
    components = results.get("components", {}).get("by_key", {})
    measures = results.get("measures", {}).get("by_component_key", {})

    files = [k for k, v in components.items() if v.get("qualifier") == "FIL"]
    files_with_measures = [f for f in files if f in measures]

    coverage_pct = len(files_with_measures) / len(files) * 100 if files else 100
    threshold = 95.0
    passed = coverage_pct >= threshold
    score = min(coverage_pct / 100, 1.0)

    return CheckResult(
        check_id="SQ-CV-3",
        name="File coverage",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"File measure coverage {coverage_pct:.1f}% {'meets' if passed else 'below'} threshold {threshold}%",
        evidence={
            "total_files": len(files),
            "files_with_measures": len(files_with_measures),
            "coverage_pct": round(coverage_pct, 2),
        },
    )


def check_language_coverage(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CV-4: Check that expected languages are detected."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-CV-4",
            name="Language coverage",
            category=CheckCategory.COVERAGE,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected_languages = ground_truth.get("expected_languages", [])
    if not expected_languages:
        return CheckResult(
            check_id="SQ-CV-4",
            name="Language coverage",
            category=CheckCategory.COVERAGE,
            passed=True,
            score=0.5,
            message="No expected languages in ground truth",
            evidence={"skipped": True},
        )

    results = data.get("results", data)
    components = results.get("components", {}).get("by_key", {})
    detected_languages = {
        v.get("language")
        for v in components.values()
        if v.get("language")
    }

    missing = [lang for lang in expected_languages if lang not in detected_languages]
    passed = len(missing) == 0
    score = (len(expected_languages) - len(missing)) / len(expected_languages)

    return CheckResult(
        check_id="SQ-CV-4",
        name="Language coverage",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Missing'} expected languages detected"
                + (f": {missing}" if missing else ""),
        evidence={
            "expected": expected_languages,
            "detected": list(detected_languages),
            "missing": missing,
        },
    )


def run_coverage_checks(data: dict, ground_truth: dict | None) -> list[CheckResult]:
    """Run all coverage checks and return results."""
    return [
        check_metric_presence(data, ground_truth),
        check_rule_coverage(data, ground_truth),
        check_file_coverage(data, ground_truth),
        check_language_coverage(data, ground_truth),
    ]
