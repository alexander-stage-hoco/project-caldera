"""Coverage checks for Lizard function analysis (CV-1 to CV-8).

These checks validate that Lizard correctly detects and analyzes
all 7 supported languages.
"""

from typing import Any, Dict, List, Set

from . import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    create_check_result,
    create_partial_check_result,
)


# Language detection patterns
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "csharp": [".cs"],
    "java": [".java"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "go": [".go"],
    "rust": [".rs"],
}

# Lizard's language names (may differ from our naming)
LIZARD_LANGUAGE_NAMES = {
    "python": ["Python", "python"],
    "csharp": ["C#", "CSharp", "csharp"],
    "java": ["Java", "java"],
    "javascript": ["JavaScript", "javascript", "Javascript", "JS", "js"],
    "typescript": ["TypeScript", "typescript", "Typescript", "TS", "ts"],
    "go": ["Go", "go", "Golang", "golang"],
    "rust": ["Rust", "rust"],
}


def _get_detected_languages(analysis: Dict[str, Any]) -> Set[str]:
    """Get set of detected languages from analysis.

    Returns normalized language names (lowercase).
    """
    languages = set()

    # Check by_language summary if available
    summary = analysis.get("summary", {})
    by_language = summary.get("by_language", {})
    for lang in by_language:
        languages.add(lang.lower())

    # Also check file extensions
    for file_data in analysis.get("files", []):
        file_path = file_data.get("path", "")
        lang = file_data.get("language", "")
        if lang:
            languages.add(lang.lower())

        # Infer from extension if language not specified
        for our_lang, extensions in LANGUAGE_EXTENSIONS.items():
            if any(file_path.endswith(ext) for ext in extensions):
                languages.add(our_lang)

    return languages


def _get_files_by_language(
    analysis: Dict[str, Any], language: str
) -> List[Dict[str, Any]]:
    """Get files for a specific language."""
    files = []
    extensions = LANGUAGE_EXTENSIONS.get(language, [])
    lizard_names = [n.lower() for n in LIZARD_LANGUAGE_NAMES.get(language, [])]

    for file_data in analysis.get("files", []):
        file_path = file_data.get("path", "")
        file_lang = file_data.get("language", "").lower()

        # Match by language name or extension
        if file_lang in lizard_names or any(
            file_path.endswith(ext) for ext in extensions
        ):
            files.append(file_data)

    return files


def _check_language_detected(
    analysis: Dict[str, Any],
    language: str,
    check_id: str,
    severity: CheckSeverity = CheckSeverity.HIGH,
) -> CheckResult:
    """Generic check for language detection."""
    files = _get_files_by_language(analysis, language)
    total_functions = sum(
        len(f.get("functions", [])) for f in files
    )

    passed = len(files) > 0 and total_functions > 0

    return create_check_result(
        check_id=check_id,
        name=f"{language.title()} language detected",
        category=CheckCategory.COVERAGE,
        severity=severity,
        passed=passed,
        message=f"Found {len(files)} {language} files with {total_functions} functions"
        if passed
        else f"No {language} files or functions detected",
        evidence={
            "files_found": len(files),
            "functions_found": total_functions,
            "file_paths": [f.get("path", "") for f in files[:5]],
        },
    )


def check_cv1_python_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-1: Python files and functions detected."""
    return _check_language_detected(analysis, "python", "CV-1")


def check_cv2_csharp_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-2: C# files and functions detected."""
    return _check_language_detected(analysis, "csharp", "CV-2")


def check_cv3_java_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-3: Java files and functions detected."""
    return _check_language_detected(analysis, "java", "CV-3")


def check_cv4_javascript_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-4: JavaScript files and functions detected."""
    return _check_language_detected(analysis, "javascript", "CV-4")


def check_cv5_typescript_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-5: TypeScript files and functions detected."""
    return _check_language_detected(analysis, "typescript", "CV-5")


def check_cv6_go_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-6: Go files and functions detected."""
    return _check_language_detected(analysis, "go", "CV-6")


def check_cv7_rust_detected(analysis: Dict[str, Any]) -> CheckResult:
    """CV-7: Rust files and functions detected."""
    return _check_language_detected(analysis, "rust", "CV-7")


def check_cv8_all_languages_in_summary(analysis: Dict[str, Any]) -> CheckResult:
    """CV-8: All 7 languages present in by_language summary.

    Validates that analysis covers all expected languages.
    """
    detected = _get_detected_languages(analysis)
    expected = set(LANGUAGE_EXTENSIONS.keys())

    missing = expected - detected
    present = expected & detected

    score = len(present) / len(expected)

    # Build detailed evidence
    language_stats = {}
    summary = analysis.get("summary", {})
    by_language = summary.get("by_language", {})

    for lang in expected:
        lang_files = _get_files_by_language(analysis, lang)
        lang_functions = sum(len(f.get("functions", [])) for f in lang_files)
        total_ccn = sum(
            sum(func.get("ccn", 0) for func in f.get("functions", []))
            for f in lang_files
        )

        language_stats[lang] = {
            "detected": lang in detected,
            "files": len(lang_files),
            "functions": lang_functions,
            "total_ccn": total_ccn,
        }

    return create_partial_check_result(
        check_id="CV-8",
        name="All languages in summary",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.CRITICAL,
        score=score,
        message=f"{len(present)}/7 languages detected"
        + (f", missing: {', '.join(missing)}" if missing else ""),
        evidence={
            "detected_languages": list(present),
            "missing_languages": list(missing),
            "language_stats": language_stats,
        },
    )


def run_coverage_checks(analysis: Dict[str, Any]) -> List[CheckResult]:
    """Run all coverage checks.

    Args:
        analysis: Parsed analysis JSON

    Returns:
        List of CheckResult objects
    """
    return [
        check_cv1_python_detected(analysis),
        check_cv2_csharp_detected(analysis),
        check_cv3_java_detected(analysis),
        check_cv4_javascript_detected(analysis),
        check_cv5_typescript_detected(analysis),
        check_cv6_go_detected(analysis),
        check_cv7_rust_detected(analysis),
        check_cv8_all_languages_in_summary(analysis),
    ]
