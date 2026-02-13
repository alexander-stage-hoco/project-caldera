"""
Coverage checks (CV-1 to CV-8) for PMD CPD evaluation.

These checks validate language and file coverage.
"""

from __future__ import annotations

from . import (
    CheckResult,
    CheckCategory,
    SUPPORTED_LANGUAGES,
    load_all_ground_truth,
    get_file_from_analysis,
    get_language_stats,
)


def run_coverage_checks(analysis: dict, ground_truth_dir: str) -> list[CheckResult]:
    """Run all coverage checks."""
    ground_truth = load_all_ground_truth(ground_truth_dir)
    results = []

    results.append(_cv1_python_coverage(analysis, ground_truth))
    results.append(_cv2_javascript_coverage(analysis, ground_truth))
    results.append(_cv3_typescript_coverage(analysis, ground_truth))
    results.append(_cv4_csharp_coverage(analysis, ground_truth))
    results.append(_cv5_java_coverage(analysis, ground_truth))
    results.append(_cv6_go_coverage(analysis, ground_truth))
    results.append(_cv7_rust_coverage(analysis, ground_truth))
    results.append(_cv8_multi_language_detection(analysis, ground_truth))

    return results


def _check_language_coverage(
    analysis: dict,
    ground_truth: dict[str, dict],
    language: str,
    check_id: str,
    check_name: str,
) -> CheckResult:
    """Generic language coverage check."""
    gt = ground_truth.get(language, {})
    files_gt = gt.get("files", {})

    if not files_gt:
        return CheckResult(
            check_id=check_id,
            name=check_name,
            category=CheckCategory.COVERAGE,
            passed=True,
            score=1.0,
            message=f"No {language} files in ground truth",
            evidence={}
        )

    covered = 0
    total = len(files_gt)
    evidence_files = []

    for filename in files_gt:
        file_info = get_file_from_analysis(analysis, filename)
        if file_info is not None:
            covered += 1
            evidence_files.append({"file": filename, "status": "found"})
        else:
            evidence_files.append({"file": filename, "status": "not_found"})

    score = covered / total if total > 0 else 1.0
    passed = score >= 0.8  # 80% coverage threshold

    return CheckResult(
        check_id=check_id,
        name=check_name,
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"Analyzed {covered}/{total} {language} files from ground truth",
        evidence={"files": evidence_files}
    )


def _cv1_python_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-1: Python files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "python", "CV-1", "Python file coverage"
    )


def _cv2_javascript_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-2: JavaScript files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "javascript", "CV-2", "JavaScript file coverage"
    )


def _cv3_typescript_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-3: TypeScript files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "typescript", "CV-3", "TypeScript file coverage"
    )


def _cv4_csharp_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-4: C# files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "csharp", "CV-4", "C# file coverage"
    )


def _cv5_java_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-5: Java files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "java", "CV-5", "Java file coverage"
    )


def _cv6_go_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-6: Go files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "go", "CV-6", "Go file coverage"
    )


def _cv7_rust_coverage(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-7: Rust files should be analyzed."""
    return _check_language_coverage(
        analysis, ground_truth, "rust", "CV-7", "Rust file coverage"
    )


def _cv8_multi_language_detection(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """CV-8: Multiple languages should be detected and analyzed."""
    lang_stats = get_language_stats(analysis)
    detected_languages = set(lang_stats.keys())

    # Expected languages from ground truth
    expected_languages = set(ground_truth.keys())

    if not expected_languages:
        return CheckResult(
            check_id="CV-8",
            name="Multi-language detection",
            category=CheckCategory.COVERAGE,
            passed=True,
            score=1.0,
            message="No languages in ground truth",
            evidence={}
        )

    # Map CPD language names to our standard names
    lang_mapping = {
        "ecmascript": "javascript",
        "cs": "csharp",
    }
    normalized_detected = set()
    for lang in detected_languages:
        normalized_detected.add(lang_mapping.get(lang, lang))

    covered = len(normalized_detected & expected_languages)
    total = len(expected_languages)

    score = covered / total if total > 0 else 1.0
    passed = score >= 0.7  # 70% of languages should be covered

    return CheckResult(
        check_id="CV-8",
        name="Multi-language detection",
        category=CheckCategory.COVERAGE,
        passed=passed,
        score=score,
        message=f"Detected {covered}/{total} expected languages",
        evidence={
            "detected": list(normalized_detected),
            "expected": list(expected_languages),
            "covered": list(normalized_detected & expected_languages),
            "missing": list(expected_languages - normalized_detected),
        }
    )
