"""
Coverage checks (CV-1 to CV-8) for Semgrep smell detection.

Tests language and category coverage:
- CV-1: Python coverage
- CV-2: JavaScript coverage
- CV-3: TypeScript coverage
- CV-4: C# coverage
- CV-5: Java coverage
- CV-6: Go coverage
- CV-7: Rust coverage
- CV-8: DD category coverage
"""

from . import (
    CheckResult,
    CheckCategory,
    get_language_stats,
    SMELL_CATEGORIES,
)


TARGET_LANGUAGES = ["python", "javascript", "typescript", "csharp", "java", "go", "rust"]


def run_coverage_checks(
    analysis: dict,
) -> list[CheckResult]:
    """Run all coverage checks (CV-1 to CV-8)."""
    results = []
    lang_stats = get_language_stats(analysis)

    # CV-1 to CV-7: Per-language coverage
    language_checks = [
        ("CV-1", "Python coverage", "python"),
        ("CV-2", "JavaScript coverage", "javascript"),
        ("CV-3", "TypeScript coverage", "typescript"),
        ("CV-4", "C# coverage", "csharp"),
        ("CV-5", "Java coverage", "java"),
        ("CV-6", "Go coverage", "go"),
        ("CV-7", "Rust coverage", "rust"),
    ]

    for check_id, name, lang in language_checks:
        stats = lang_stats.get(lang, {})
        files = stats.get("files", 0)
        smells = stats.get("smells", 0)
        categories = stats.get("categories_covered", [])

        # Score based on:
        # - 0.4: Language files were analyzed
        # - 0.3: At least one smell was detected
        # - 0.3: Multiple categories covered
        score = 0.0
        if files > 0:
            score += 0.4
        if smells > 0:
            score += 0.3
        if len(categories) > 0:
            score += 0.3 * min(len(categories) / 3, 1.0)

        # Passed if language was analyzed and has potential for detection
        passed = files > 0

        results.append(CheckResult(
            check_id=check_id,
            name=name,
            category=CheckCategory.COVERAGE,
            passed=passed,
            score=score,
            message=f"{files} files, {smells} smells, {len(categories)} categories",
            evidence={
                "files_analyzed": files,
                "smells_detected": smells,
                "categories_covered": categories,
            },
        ))

    # CV-8: DD category coverage
    smells_by_category = analysis.get("summary", {}).get("smells_by_category", {})
    categories_with_detections = [cat for cat in SMELL_CATEGORIES if smells_by_category.get(cat, 0) > 0]
    coverage_pct = len(categories_with_detections) / len(SMELL_CATEGORIES) if SMELL_CATEGORIES else 0

    # Semgrep primarily covers security, so weight accordingly
    security_weight = 0.4  # Security is 40% of score
    other_weight = 0.6 / (len(SMELL_CATEGORIES) - 1) if len(SMELL_CATEGORIES) > 1 else 0

    category_score = 0.0
    if "security" in smells_by_category or any(
        "sql" in cat.lower() or "injection" in cat.lower()
        for cat in smells_by_category.keys()
    ):
        category_score += security_weight

    for cat in SMELL_CATEGORIES:
        if cat != "security" and smells_by_category.get(cat, 0) > 0:
            category_score += other_weight

    # Also count 'unknown' category if it has findings
    if smells_by_category.get("unknown", 0) > 0:
        category_score += 0.1  # Small bonus for any additional detection

    results.append(CheckResult(
        check_id="CV-8",
        name="DD category coverage",
        category=CheckCategory.COVERAGE,
        passed=len(categories_with_detections) > 0,
        score=min(category_score, 1.0),
        message=f"Covered {len(categories_with_detections)}/{len(SMELL_CATEGORIES)} DD categories",
        evidence={
            "total_categories": len(SMELL_CATEGORIES),
            "categories_detected": categories_with_detections,
            "coverage_percentage": coverage_pct * 100,
            "by_category": smells_by_category,
        },
    ))

    return results
