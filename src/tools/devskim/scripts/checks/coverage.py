"""
Coverage checks (CV-1 to CV-8) for DevSkim security detection.

Tests language and category coverage:
- CV-1: C# coverage
- CV-2: Python coverage
- CV-3: JavaScript coverage
- CV-4: Java coverage
- CV-5: Go coverage
- CV-6: C/C++ coverage
- CV-7: Multi-language support
- CV-8: DD security category coverage
"""

from . import (
    CheckResult,
    CheckCategory,
    get_language_stats,
    load_all_ground_truth,
    SECURITY_CATEGORIES,
)


TARGET_LANGUAGES = ["csharp", "python", "javascript", "java", "go", "c", "cpp"]


def run_coverage_checks(
    analysis: dict,
    ground_truth_dir: str | None = None,
) -> list[CheckResult]:
    """Run all coverage checks (CV-1 to CV-8)."""
    results = []
    lang_stats = get_language_stats(analysis)
    expected_languages = set(TARGET_LANGUAGES)
    expected_categories = list(SECURITY_CATEGORIES)

    if ground_truth_dir:
        ground_truth = load_all_ground_truth(ground_truth_dir)
        if ground_truth:
            expected_languages = set(ground_truth.keys())
            expected_categories = _collect_expected_categories(ground_truth) or expected_categories

    # CV-1 to CV-6: Per-language coverage
    language_checks = [
        ("CV-1", "C# coverage", "csharp"),
        ("CV-2", "Python coverage", "python"),
        ("CV-3", "JavaScript coverage", "javascript"),
        ("CV-4", "Java coverage", "java"),
        ("CV-5", "Go coverage", "go"),
        ("CV-6", "C/C++ coverage", "cpp"),
    ]

    for check_id, name, lang in language_checks:
        if lang not in expected_languages:
            results.append(_skipped_check(
                check_id=check_id,
                name=name,
                reason=f"{lang} not present in ground truth",
            ))
            continue

        # Try both the exact name and common variations
        lang_variants = [lang]
        if lang == "cpp":
            lang_variants.extend(["c", "c++"])
        elif lang == "javascript":
            lang_variants.extend(["js", "typescript", "ts"])

        stats = {}
        for variant in lang_variants:
            if variant in lang_stats:
                stats = lang_stats[variant]
                break

        files = stats.get("files", 0)
        issues = stats.get("issues", 0)
        categories = stats.get("categories_covered", [])

        # Score based on:
        # - 0.4: Language files were analyzed
        # - 0.3: At least one issue was detected (DevSkim is security-focused)
        # - 0.3: Multiple categories covered
        score = 0.0
        if files > 0:
            score += 0.4
        if issues > 0:
            score += 0.3
        if len(categories) > 0:
            score += 0.3 * min(len(categories) / 3, 1.0)

        # Passed if language was analyzed
        passed = files > 0

        results.append(CheckResult(
            check_id=check_id,
            name=name,
            category=CheckCategory.COVERAGE,
            passed=passed,
            score=score,
            message=f"{files} files, {issues} issues, {len(categories)} categories",
            evidence={
                "files_analyzed": files,
                "issues_detected": issues,
                "categories_covered": categories,
            },
        ))

    # CV-7: Multi-language support
    languages_with_files = [lang for lang, stats in lang_stats.items() if stats.get("files", 0) > 0]
    expected_lang_count = max(len(expected_languages), 1)
    if expected_lang_count <= 1:
        multi_lang_score = 1.0 if languages_with_files else 0.0
        multi_lang_passed = bool(languages_with_files)
    else:
        multi_lang_score = min(len(languages_with_files) / expected_lang_count, 1.0)
        multi_lang_passed = len(languages_with_files) >= expected_lang_count

    results.append(CheckResult(
        check_id="CV-7",
        name="Multi-language support",
        category=CheckCategory.COVERAGE,
        passed=multi_lang_passed,
        score=multi_lang_score,
        message=f"Analyzed {len(languages_with_files)} of {expected_lang_count} expected languages",
        evidence={
            "languages": languages_with_files,
            "count": len(languages_with_files),
        },
    ))

    # CV-8: DD security category coverage
    issues_by_category = analysis.get("summary", {}).get("issues_by_category", {})
    if not expected_categories:
        results.append(_skipped_check(
            check_id="CV-8",
            name="DD security category coverage",
            reason="No security categories defined in ground truth",
        ))
        return results

    categories_with_detections = [cat for cat in expected_categories if issues_by_category.get(cat, 0) > 0]
    coverage_pct = len(categories_with_detections) / len(expected_categories) if expected_categories else 0

    # Weight key security categories higher
    high_priority = [cat for cat in ["sql_injection", "hardcoded_secret", "insecure_crypto", "xss", "command_injection"] if cat in expected_categories]
    priority_covered = sum(1 for cat in high_priority if cat in categories_with_detections)
    priority_score = (priority_covered / len(high_priority) * 0.6) if high_priority else 0.0

    other_covered = len(categories_with_detections) - priority_covered
    other_denominator = len(expected_categories) - len(high_priority)
    other_score = (other_covered / other_denominator) * 0.4 if other_denominator > 0 else 0.0

    category_score = priority_score + other_score

    results.append(CheckResult(
        check_id="CV-8",
        name="DD security category coverage",
        category=CheckCategory.COVERAGE,
        passed=len(categories_with_detections) > 0,
        score=min(category_score, 1.0),
        message=f"Covered {len(categories_with_detections)}/{len(expected_categories)} security categories",
        evidence={
            "total_categories": len(expected_categories),
            "categories_detected": categories_with_detections,
            "coverage_percentage": coverage_pct * 100,
            "high_priority_covered": priority_covered,
            "by_category": issues_by_category,
        },
    ))

    return results


def _collect_expected_categories(ground_truth: dict[str, dict]) -> list[str]:
    """Collect expected security categories from ground truth definitions."""
    categories = set()
    for gt in ground_truth.values():
        aggregate = gt.get("aggregate_expectations") or gt.get("expected", {}).get("aggregate_expectations", {})
        categories.update(aggregate.get("required_categories", []))
        for file_info in gt.get("files", {}).values():
            for expected in file_info.get("expected_issues", []):
                category = expected.get("category")
                if category:
                    categories.add(category)
    return sorted(categories)


def _skipped_check(check_id: str, name: str, reason: str) -> CheckResult:
    """Return a skipped coverage check result."""
    return CheckResult(
        check_id=check_id,
        name=name,
        category=CheckCategory.COVERAGE,
        passed=True,
        score=1.0,
        message=f"Skipped: {reason}",
        evidence={
            "skipped": True,
            "reason": reason,
        },
    )
