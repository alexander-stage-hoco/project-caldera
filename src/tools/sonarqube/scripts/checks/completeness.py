"""Completeness checks (SQ-CM-*) for SonarQube evaluation."""

from . import (
    CheckCategory,
    CheckResult,
    get_nested,
)


def check_component_tree(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-1: Check that component tree has TRK, DIR, and FIL qualifiers."""
    results = data.get("results", data)
    components = results.get("components", {}).get("by_key", {})

    qualifiers = {v.get("qualifier") for v in components.values()}
    required_qualifiers = {"TRK", "DIR", "FIL"}
    present = required_qualifiers & qualifiers
    missing = required_qualifiers - qualifiers

    passed = len(missing) == 0
    score = len(present) / len(required_qualifiers)

    return CheckResult(
        check_id="SQ-CM-1",
        name="Component tree complete",
        category=CheckCategory.COMPLETENESS,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Missing'} required component types"
                + (f": {missing}" if missing else f": {required_qualifiers}"),
        evidence={
            "required": list(required_qualifiers),
            "present": list(qualifiers),
            "missing": list(missing),
        },
    )


def check_issue_locations(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-2: Check that issues have file and line information."""
    results = data.get("results", data)
    issues = results.get("issues", {}).get("items", [])

    if not issues:
        return CheckResult(
            check_id="SQ-CM-2",
            name="Issue locations",
            category=CheckCategory.COMPLETENESS,
            passed=True,
            score=1.0,
            message="No issues to check",
            evidence={"skipped": True},
        )

    issues_with_location = [
        i for i in issues
        if i.get("component") and (i.get("line") or i.get("text_range"))
    ]

    coverage_pct = len(issues_with_location) / len(issues) * 100
    threshold = 90.0
    passed = coverage_pct >= threshold
    score = min(coverage_pct / 100, 1.0)

    return CheckResult(
        check_id="SQ-CM-2",
        name="Issue locations",
        category=CheckCategory.COMPLETENESS,
        passed=passed,
        score=score,
        message=f"{coverage_pct:.1f}% of issues have location info"
                + (f" (threshold: {threshold}%)" if not passed else ""),
        evidence={
            "total_issues": len(issues),
            "with_location": len(issues_with_location),
            "coverage_pct": round(coverage_pct, 2),
        },
    )


def check_rules_hydrated(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-3: Check that rule metadata is fully hydrated."""
    results = data.get("results", data)
    rules = results.get("rules", {}).get("by_key", {})

    if not rules:
        return CheckResult(
            check_id="SQ-CM-3",
            name="Rules hydrated",
            category=CheckCategory.COMPLETENESS,
            passed=True,
            score=1.0,
            message="No rules to check",
            evidence={"skipped": True},
        )

    required_fields = ["key", "name", "type", "severity"]
    fully_hydrated = sum(
        1 for rule in rules.values()
        if all(rule.get(f) for f in required_fields)
    )

    coverage_pct = fully_hydrated / len(rules) * 100
    threshold = 95.0
    passed = coverage_pct >= threshold
    score = min(coverage_pct / 100, 1.0)

    return CheckResult(
        check_id="SQ-CM-3",
        name="Rules hydrated",
        category=CheckCategory.COMPLETENESS,
        passed=passed,
        score=score,
        message=f"{coverage_pct:.1f}% of rules fully hydrated"
                + (f" (threshold: {threshold}%)" if not passed else ""),
        evidence={
            "total_rules": len(rules),
            "fully_hydrated": fully_hydrated,
            "coverage_pct": round(coverage_pct, 2),
        },
    )


def check_duplications_present(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-4: Check that duplication data is present when expected."""
    results = data.get("results", data)
    duplications = results.get("duplications", {})
    project_summary = duplications.get("project_summary", {})
    by_file = duplications.get("by_file_key", {})

    dup_density = project_summary.get("duplicated_lines_density", 0)

    if dup_density > 0:
        passed = bool(by_file)
        return CheckResult(
            check_id="SQ-CM-4",
            name="Duplications present",
            category=CheckCategory.COMPLETENESS,
            passed=passed,
            score=1.0 if passed else 0.0,
            message=f"Duplication data {'present' if passed else 'missing'} "
                    f"({len(by_file)} files, {dup_density}% density)",
            evidence={
                "files_with_duplications": len(by_file),
                "density": dup_density,
            },
        )
    else:
        return CheckResult(
            check_id="SQ-CM-4",
            name="Duplications present",
            category=CheckCategory.COMPLETENESS,
            passed=True,
            score=1.0,
            message="No duplications detected (0% density)",
            evidence={
                "files_with_duplications": len(by_file),
                "density": dup_density,
            },
        )


def check_quality_gate_conditions(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-5: Check that quality gate has condition details."""
    results = data.get("results", data)
    quality_gate = results.get("quality_gate", {})
    status = quality_gate.get("status")
    conditions = quality_gate.get("conditions", [])

    if not status:
        return CheckResult(
            check_id="SQ-CM-5",
            name="Quality gate conditions",
            category=CheckCategory.COMPLETENESS,
            passed=False,
            score=0.0,
            message="No quality gate status present",
            evidence={"status": None},
        )

    if status == "NONE":
        return CheckResult(
            check_id="SQ-CM-5",
            name="Quality gate conditions",
            category=CheckCategory.COMPLETENESS,
            passed=True,
            score=0.5,
            message="No quality gate configured",
            evidence={"status": "NONE"},
        )

    passed = bool(conditions)
    return CheckResult(
        check_id="SQ-CM-5",
        name="Quality gate conditions",
        category=CheckCategory.COMPLETENESS,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Quality gate has {len(conditions)} conditions" if passed else
                "Quality gate has status but no conditions returned",
        evidence={
            "status": status,
            "conditions_count": len(conditions),
        },
    )


def check_derived_insights(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-CM-6: Check that derived insights are computed."""
    results = data.get("results", data)
    insights = results.get("derived_insights", {})
    hotspots = insights.get("hotspots", [])
    dir_rollups = insights.get("directory_rollups", {})

    issues = []
    if not hotspots:
        issues.append("No hotspots computed")
    if not dir_rollups:
        issues.append("No directory rollups computed")

    passed = len(issues) == 0
    score = (2 - len(issues)) / 2

    return CheckResult(
        check_id="SQ-CM-6",
        name="Derived insights present",
        category=CheckCategory.COMPLETENESS,
        passed=passed,
        score=score,
        message=f"Derived insights {'present' if passed else 'missing'}"
                + (f" ({len(hotspots)} hotspots, {len(dir_rollups)} directories)" if passed else f": {', '.join(issues)}"),
        evidence={
            "hotspots_count": len(hotspots),
            "directory_rollups_count": len(dir_rollups),
            "issues": issues,
        },
    )


def run_completeness_checks(data: dict, ground_truth: dict | None) -> list[CheckResult]:
    """Run all completeness checks and return results."""
    return [
        check_component_tree(data, ground_truth),
        check_issue_locations(data, ground_truth),
        check_rules_hydrated(data, ground_truth),
        check_duplications_present(data, ground_truth),
        check_quality_gate_conditions(data, ground_truth),
        check_derived_insights(data, ground_truth),
    ]
