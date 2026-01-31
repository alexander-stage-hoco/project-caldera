"""
Classification Checks (CL-1 to CL-6).

Validates file type detection accuracy.
"""

from typing import Any, Dict, List, Optional

from . import CheckCategory, CheckResult, register_check


def run_classification_checks(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> List[CheckResult]:
    """Run all classification checks."""
    checks = []

    checks.append(check_test_detection(output, ground_truth))
    checks.append(check_config_detection(output, ground_truth))
    checks.append(check_generated_detection(output, ground_truth))
    checks.append(check_vendor_detection(output, ground_truth))
    checks.append(check_docs_detection(output, ground_truth))
    checks.append(check_language_detection(output, ground_truth))
    checks.append(check_shebang_detection(output, ground_truth))
    checks.append(check_content_disambiguation(output, ground_truth))
    checks.append(check_detection_capabilities(output, ground_truth))

    return checks


def _get_files_with_classification(output: Dict[str, Any], category: str) -> List[str]:
    """Get all file paths with a specific classification."""
    files = output.get("files", {})
    return [
        path for path, file_obj in files.items()
        if file_obj.get("classification") == category
    ]


def _check_expected_classifications(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]],
    category: str,
) -> tuple[List[str], List[str]]:
    """
    Check expected classifications from ground truth.

    Returns (false_negatives, false_positives).
    """
    if not ground_truth:
        return [], []

    expected_files = ground_truth.get("expected", {}).get("specific_files", {})
    files = output.get("files", {})

    false_negatives = []  # Expected to be category but isn't
    false_positives = []  # Classified as category but shouldn't be

    for path, expected in expected_files.items():
        expected_class = expected.get("classification")
        actual_class = files.get(path, {}).get("classification")

        if expected_class == category and actual_class != category:
            false_negatives.append(path)
        elif expected_class != category and actual_class == category:
            false_positives.append(path)

    return false_negatives, false_positives


@register_check("CL-1")
def check_test_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-1: Test files correctly classified."""
    test_files = _get_files_with_classification(output, "test")

    # Check for obvious test patterns that should be detected
    files = output.get("files", {})
    missed_tests = []

    test_patterns = [
        "test_", "_test.py", ".test.js", ".test.ts",
        ".spec.js", ".spec.ts", "Tests.cs", "Test.cs",
        "_test.go", "_test.rs", "_spec.rb",
    ]

    for path, file_obj in files.items():
        classification = file_obj.get("classification")
        name = file_obj.get("name", "")

        # Check if file matches test pattern but not classified as test
        if classification != "test":
            for pattern in test_patterns:
                if pattern in name or pattern in path:
                    # Check if it's in tests/ directory
                    if "tests/" in path or "test/" in path or "__tests__/" in path:
                        missed_tests.append(path)
                        break

    false_neg, false_pos = _check_expected_classifications(output, ground_truth, "test")

    if missed_tests or false_neg:
        all_missed = list(set(missed_tests + false_neg))
        return CheckResult(
            check_id="CL-1",
            name="Test Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(all_missed)} test files not detected",
            evidence={"missed_tests": all_missed[:10]},
        )

    return CheckResult(
        check_id="CL-1",
        name="Test Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(test_files)} test files correctly detected",
        evidence={"test_count": len(test_files)},
    )


@register_check("CL-2")
def check_config_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-2: Config files correctly classified."""
    config_files = _get_files_with_classification(output, "config")

    # Check for obvious config patterns
    files = output.get("files", {})
    missed_configs = []

    config_names = [
        "Makefile", "Dockerfile", ".gitignore", ".editorconfig",
        "package.json", "tsconfig.json", "pyproject.toml",
        ".eslintrc", ".prettierrc", "docker-compose.yml",
    ]

    for path, file_obj in files.items():
        classification = file_obj.get("classification")
        name = file_obj.get("name", "")

        if classification != "config" and name in config_names:
            missed_configs.append(path)

    false_neg, false_pos = _check_expected_classifications(output, ground_truth, "config")

    if missed_configs or false_neg:
        all_missed = list(set(missed_configs + false_neg))
        return CheckResult(
            check_id="CL-2",
            name="Config Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(all_missed)} config files not detected",
            evidence={"missed_configs": all_missed[:10]},
        )

    return CheckResult(
        check_id="CL-2",
        name="Config Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(config_files)} config files correctly detected",
        evidence={"config_count": len(config_files)},
    )


@register_check("CL-3")
def check_generated_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-3: Generated files correctly classified."""
    generated_files = _get_files_with_classification(output, "generated")

    # Check for obvious generated patterns
    files = output.get("files", {})
    missed_generated = []

    generated_patterns = [
        ".g.cs", ".generated.", ".min.js", ".min.css",
        "_pb2.py", ".pb.go", ".d.ts", "package-lock.json",
        "yarn.lock", "Cargo.lock", ".designer.cs",
    ]

    for path, file_obj in files.items():
        classification = file_obj.get("classification")
        name = file_obj.get("name", "")

        if classification != "generated":
            for pattern in generated_patterns:
                if pattern in name:
                    missed_generated.append(path)
                    break

    false_neg, false_pos = _check_expected_classifications(output, ground_truth, "generated")

    if missed_generated or false_neg:
        all_missed = list(set(missed_generated + false_neg))
        return CheckResult(
            check_id="CL-3",
            name="Generated Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(all_missed)} generated files not detected",
            evidence={"missed_generated": all_missed[:10]},
        )

    return CheckResult(
        check_id="CL-3",
        name="Generated Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(generated_files)} generated files correctly detected",
        evidence={"generated_count": len(generated_files)},
    )


@register_check("CL-4")
def check_vendor_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-4: Vendor directories correctly classified."""
    directories = output.get("directories", {})
    files = output.get("files", {})

    vendor_dirs = [
        path for path, dir_obj in directories.items()
        if dir_obj.get("classification") == "vendor"
    ]

    vendor_files = _get_files_with_classification(output, "vendor")

    # Check for obvious vendor patterns
    missed_vendor_paths = []

    vendor_patterns = [
        "node_modules/", "vendor/", "third_party/",
        ".nuget/", "bower_components/",
    ]

    for path in files.keys():
        file_class = files[path].get("classification")
        if file_class != "vendor":
            for pattern in vendor_patterns:
                if pattern in path:
                    missed_vendor_paths.append(path)
                    break

    false_neg, false_pos = _check_expected_classifications(output, ground_truth, "vendor")

    if missed_vendor_paths or false_neg:
        all_missed = list(set(missed_vendor_paths + false_neg))
        return CheckResult(
            check_id="CL-4",
            name="Vendor Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(all_missed)} vendor files not detected",
            evidence={"missed_vendor": all_missed[:10]},
        )

    return CheckResult(
        check_id="CL-4",
        name="Vendor Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(vendor_dirs)} vendor dirs, {len(vendor_files)} vendor files detected",
        evidence={"vendor_dirs": len(vendor_dirs), "vendor_files": len(vendor_files)},
    )


@register_check("CL-5")
def check_docs_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-5: Documentation files correctly classified."""
    doc_files = _get_files_with_classification(output, "docs")

    # Check for obvious doc patterns
    files = output.get("files", {})
    missed_docs = []

    doc_names = [
        "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
        "LICENSE", "LICENSE.md", "AUTHORS", "CODE_OF_CONDUCT.md",
    ]

    for path, file_obj in files.items():
        classification = file_obj.get("classification")
        name = file_obj.get("name", "")

        if classification != "docs":
            # Check exact match for common doc files
            if name.upper() in [d.upper() for d in doc_names]:
                missed_docs.append(path)
            # Check docs/ directory
            elif "docs/" in path or "documentation/" in path:
                extension = file_obj.get("extension", "")
                if extension in [".md", ".rst", ".txt", ".adoc"]:
                    missed_docs.append(path)

    false_neg, false_pos = _check_expected_classifications(output, ground_truth, "docs")

    if missed_docs or false_neg:
        all_missed = list(set(missed_docs + false_neg))
        return CheckResult(
            check_id="CL-5",
            name="Docs Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(all_missed)} doc files not detected",
            evidence={"missed_docs": all_missed[:10]},
        )

    return CheckResult(
        check_id="CL-5",
        name="Docs Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(doc_files)} doc files correctly detected",
        evidence={"doc_count": len(doc_files)},
    )


@register_check("CL-6")
def check_language_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-6: Languages correctly detected from extensions."""
    files = output.get("files", {})

    # Expected extension -> language mappings
    expected_langs = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".cs": "csharp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
    }

    mismatches = []

    for path, file_obj in files.items():
        extension = file_obj.get("extension", "")
        language = file_obj.get("language", "")

        if extension in expected_langs:
            expected = expected_langs[extension]
            if language != expected:
                mismatches.append({
                    "path": path,
                    "extension": extension,
                    "expected": expected,
                    "actual": language,
                })

    # Also check ground truth if provided
    if ground_truth:
        expected_files = ground_truth.get("expected", {}).get("specific_files", {})
        for path, expected in expected_files.items():
            expected_lang = expected.get("language")
            if expected_lang and path in files:
                actual_lang = files[path].get("language")
                if actual_lang != expected_lang:
                    mismatches.append({
                        "path": path,
                        "expected": expected_lang,
                        "actual": actual_lang,
                    })

    if mismatches:
        return CheckResult(
            check_id="CL-6",
            name="Language Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=0.5,
            message=f"{len(mismatches)} language detection errors",
            evidence={"mismatches": mismatches[:10]},
        )

    # Count detected languages
    lang_counts = {}
    for file_obj in files.values():
        lang = file_obj.get("language", "unknown")
        if lang != "unknown":
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    return CheckResult(
        check_id="CL-6",
        name="Language Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"{len(lang_counts)} languages detected correctly",
        evidence={"languages": lang_counts},
    )


@register_check("CL-7")
def check_shebang_detection(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-7: Shebang-based language detection.

    Tests that files with shebangs but no extension are detected correctly.
    This requires the enhanced language_detector with enry support.
    """
    # Check if we have shebang detection capability
    try:
        from ..language_detector import ENRY_AVAILABLE, detect_language
    except ImportError:
        return CheckResult(
            check_id="CL-7",
            name="Shebang Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=True,
            score=0.5,
            message="Shebang detection not available (enry not installed)",
            evidence={"enry_available": False},
        )

    if not ENRY_AVAILABLE:
        return CheckResult(
            check_id="CL-7",
            name="Shebang Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=True,
            score=0.5,
            message="Shebang detection not available (enry not installed)",
            evidence={"enry_available": False},
        )

    # Test cases: (filename, content, expected_language)
    test_cases = [
        ("script", b"#!/usr/bin/env python\nprint('hello')", "python"),
        ("run.sh", b"#!/bin/bash\necho hello", "shell"),
        ("script2", b"#!/usr/bin/env ruby\nputs 'hello'", "ruby"),
        ("script3", b"#!/usr/bin/env node\nconsole.log('hello')", "javascript"),
        ("script4", b"#!/usr/bin/perl\nprint 'hello'", "perl"),
    ]

    failures = []
    successes = []

    for filename, content, expected in test_cases:
        result = detect_language(filename, content)
        detected = result.language.lower() if result.language else "unknown"

        if detected == expected.lower():
            successes.append({"filename": filename, "expected": expected, "detected": detected})
        else:
            failures.append({"filename": filename, "expected": expected, "detected": detected})

    if failures:
        return CheckResult(
            check_id="CL-7",
            name="Shebang Detection",
            category=CheckCategory.CLASSIFICATION,
            passed=False,
            score=len(successes) / len(test_cases),
            message=f"{len(failures)} shebang detection failures",
            evidence={"failures": failures, "successes": successes},
        )

    return CheckResult(
        check_id="CL-7",
        name="Shebang Detection",
        category=CheckCategory.CLASSIFICATION,
        passed=True,
        score=1.0,
        message=f"All {len(test_cases)} shebang tests passed",
        evidence={"test_count": len(test_cases), "successes": successes},
    )


@register_check("CL-8")
def check_content_disambiguation(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-8: Content-based language disambiguation.

    Tests that ambiguous file extensions (like .h) are resolved correctly
    using content inspection.
    """
    try:
        from ..language_detector import ENRY_AVAILABLE, detect_language
    except ImportError:
        return CheckResult(
            check_id="CL-8",
            name="Content Disambiguation",
            category=CheckCategory.CLASSIFICATION,
            passed=True,
            score=0.5,
            message="Content disambiguation not available (enry not installed)",
            evidence={"enry_available": False},
        )

    if not ENRY_AVAILABLE:
        return CheckResult(
            check_id="CL-8",
            name="Content Disambiguation",
            category=CheckCategory.CLASSIFICATION,
            passed=True,
            score=0.5,
            message="Content disambiguation not available (enry not installed)",
            evidence={"enry_available": False},
        )

    # Test cases for ambiguous extensions
    test_cases = [
        # .h files can be C, C++, or Objective-C
        ("header.h", b"#include <stdio.h>\nvoid foo() {}", "c"),
        ("header.h", b"#include <iostream>\nclass Foo {};", "c++"),
        ("header.h", b"#import <Foundation/Foundation.h>\n@interface Foo", "objective-c"),
        # .m files can be Objective-C or MATLAB (context-dependent)
        ("code.m", b"#import <UIKit/UIKit.h>\n@implementation", "objective-c"),
    ]

    results = []
    passed_count = 0

    for filename, content, expected in test_cases:
        result = detect_language(filename, content)
        detected = result.language.lower() if result.language else "unknown"

        # For ambiguous cases, check if expected is in alternatives or main result
        is_correct = (
            detected == expected.lower() or
            expected.lower() in [a.lower() for a in getattr(result, 'alternatives', [])]
        )

        results.append({
            "filename": filename,
            "expected": expected,
            "detected": detected,
            "confidence": result.confidence,
            "is_correct": is_correct,
        })

        if is_correct:
            passed_count += 1

    score = passed_count / len(test_cases) if test_cases else 1.0
    passed = score >= 0.75  # Allow some tolerance for ambiguous cases

    return CheckResult(
        check_id="CL-8",
        name="Content Disambiguation",
        category=CheckCategory.CLASSIFICATION,
        passed=passed,
        score=score,
        message=f"{passed_count}/{len(test_cases)} disambiguation tests passed",
        evidence={"results": results},
    )


@register_check("CL-9")
def check_detection_capabilities(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """CL-9: Language detection capabilities check.

    Verifies what detection strategies are available and provides
    a summary of the detection system's capabilities.
    """
    try:
        from ..language_detector import get_detection_capabilities
        capabilities = get_detection_capabilities()
    except ImportError:
        capabilities = {
            "enry_available": False,
            "treesitter_available": False,
            "strategies": ["filename", "extension"],
            "fallback_only": True,
        }

    available_strategies = [s for s in capabilities.get("strategies", []) if s]

    # Score based on available capabilities
    if capabilities.get("enry_available") and capabilities.get("treesitter_available"):
        score = 1.0
        message = "Full detection capabilities available"
    elif capabilities.get("enry_available"):
        score = 0.9
        message = "Enry available, tree-sitter validation disabled"
    elif capabilities.get("fallback_only"):
        score = 0.5
        message = "Fallback mode only (extension-based detection)"
    else:
        score = 0.7
        message = "Partial detection capabilities"

    return CheckResult(
        check_id="CL-9",
        name="Detection Capabilities",
        category=CheckCategory.CLASSIFICATION,
        passed=True,  # Informational check
        score=score,
        message=message,
        evidence={
            "enry_available": capabilities.get("enry_available", False),
            "treesitter_available": capabilities.get("treesitter_available", False),
            "strategies": available_strategies,
        },
    )
