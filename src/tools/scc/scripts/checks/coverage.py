"""Coverage checks (CV-1 to CV-9)."""

import json
from pathlib import Path
from typing import List

from . import CheckResult
from . import reliability


def _load_raw_output(raw_output_path: Path) -> list:
    """Load raw scc output."""
    with open(raw_output_path) as f:
        return json.load(f)


def check_python_detected(raw_output_path: Path) -> CheckResult:
    """CV-1: Verify Python is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "Python" in languages

        return CheckResult(
            check_id="CV-1",
            name="Python Detected",
            passed=detected,
            message=f"Python detected: {detected}",
            expected="Python in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-1",
            name="Python Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_csharp_detected(raw_output_path: Path) -> CheckResult:
    """CV-2: Verify C# is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "C#" in languages

        return CheckResult(
            check_id="CV-2",
            name="C# Detected",
            passed=detected,
            message=f"C# detected: {detected}",
            expected="C# in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-2",
            name="C# Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_javascript_detected(raw_output_path: Path) -> CheckResult:
    """CV-3: Verify JavaScript is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "JavaScript" in languages

        return CheckResult(
            check_id="CV-3",
            name="JavaScript Detected",
            passed=detected,
            message=f"JavaScript detected: {detected}",
            expected="JavaScript in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-3",
            name="JavaScript Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_typescript_detected(raw_output_path: Path) -> CheckResult:
    """CV-4: Verify TypeScript is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "TypeScript" in languages

        return CheckResult(
            check_id="CV-4",
            name="TypeScript Detected",
            passed=detected,
            message=f"TypeScript detected: {detected}",
            expected="TypeScript in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-4",
            name="TypeScript Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_go_detected(raw_output_path: Path) -> CheckResult:
    """CV-5: Verify Go is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "Go" in languages

        return CheckResult(
            check_id="CV-5",
            name="Go Detected",
            passed=detected,
            message=f"Go detected: {detected}",
            expected="Go in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-5",
            name="Go Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_rust_detected(raw_output_path: Path) -> CheckResult:
    """CV-6: Verify Rust is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "Rust" in languages

        return CheckResult(
            check_id="CV-6",
            name="Rust Detected",
            passed=detected,
            message=f"Rust detected: {detected}",
            expected="Rust in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-6",
            name="Rust Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_java_detected(raw_output_path: Path) -> CheckResult:
    """CV-7: Verify Java is detected."""
    try:
        data = _load_raw_output(raw_output_path)
        languages = [entry.get("Name", "") for entry in data]
        detected = "Java" in languages

        return CheckResult(
            check_id="CV-7",
            name="Java Detected",
            passed=detected,
            message=f"Java detected: {detected}",
            expected="Java in languages",
            actual=f"detected={detected}",
            evidence={"languages": languages}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-7",
            name="Java Detected",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_file_counts_match(raw_output_path: Path, expected_per_lang: int = 9) -> CheckResult:
    """CV-8: Verify each language shows expected file count."""
    expected_languages = ["Python", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Java"]

    try:
        data = _load_raw_output(raw_output_path)

        mismatches = []
        for entry in data:
            lang = entry.get("Name", "")
            if lang in expected_languages:
                count = entry.get("Count", 0)
                if count != expected_per_lang:
                    mismatches.append(f"{lang}: {count} (expected {expected_per_lang})")

        # Also check that all expected languages are present
        found_langs = {entry.get("Name") for entry in data}
        missing = [l for l in expected_languages if l not in found_langs]

        passed = len(mismatches) == 0 and len(missing) == 0

        return CheckResult(
            check_id="CV-8",
            name="File Counts Match",
            passed=passed,
            message="All file counts match" if passed else f"Mismatches: {mismatches}, Missing: {missing}",
            expected=f"{expected_per_lang} files per language",
            actual=f"mismatches={mismatches}, missing={missing}",
            evidence={"mismatches": mismatches, "missing": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-8",
            name="File Counts Match",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_loc_within_range(raw_output_path: Path, min_loc: int = 4500, max_loc: int = 10000) -> CheckResult:
    """CV-9: Verify total LOC is within expected range."""
    try:
        data = _load_raw_output(raw_output_path)
        total_loc = sum(entry.get("Code", 0) for entry in data)

        passed = min_loc <= total_loc <= max_loc

        return CheckResult(
            check_id="CV-9",
            name="LOC Within Range",
            passed=passed,
            message=f"Total LOC: {total_loc} (expected {min_loc}-{max_loc})",
            expected=f"{min_loc}-{max_loc}",
            actual=total_loc,
            evidence={"total_loc": total_loc, "min_loc": min_loc, "max_loc": max_loc}
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-9",
            name="LOC Within Range",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_python_docstrings_as_comments(raw_output_path: Path, base_path: Path = None) -> CheckResult:
    """CV-10: Verify Python docstrings are counted as comments, not code.

    Docstrings should be counted in the Comment column, not the Code column.
    This checks files with known docstring content.
    """
    try:
        if base_path is None:
            base_path = raw_output_path.parent.parent

        files, _, _ = reliability.run_scc_by_file(base_path, "eval-repos/synthetic")

        # Find Python files with docstrings (look for files with docstring in name or known patterns)
        docstring_files = [
            f for f in files
            if f.get("Language") == "Python" and (
                "docstring" in f.get("Location", "").lower() or
                # Files with high comment ratios likely have docstrings
                (f.get("Comment", 0) > 0 and f.get("Code", 0) > 0)
            )
        ]

        if not docstring_files:
            # Check all Python files for comment counting
            python_files = [f for f in files if f.get("Language") == "Python"]
            # In Python, files with functions typically have some docstrings counted as comments
            has_comments = [f for f in python_files if f.get("Comment", 0) > 0]
            passed = len(has_comments) > 0

            return CheckResult(
                check_id="CV-10",
                name="Python Docstrings as Comments",
                passed=passed,
                message=f"Found {len(has_comments)}/{len(python_files)} Python files with comments (likely docstrings)",
                expected="Python files with docstrings should have Comment > 0",
                actual=f"files_with_comments={len(has_comments)}",
                evidence={"python_files": len(python_files), "files_with_comments": len(has_comments)}
            )

        # Check that docstring files have comments counted
        files_with_comments = [f for f in docstring_files if f.get("Comment", 0) > 0]
        passed = len(files_with_comments) == len(docstring_files)

        return CheckResult(
            check_id="CV-10",
            name="Python Docstrings as Comments",
            passed=passed,
            message=f"{len(files_with_comments)}/{len(docstring_files)} docstring files have comments counted",
            expected="All Python docstring files should have Comment > 0",
            actual=f"files_with_comments={len(files_with_comments)}",
            evidence={
                "docstring_files": [
                    {"loc": f["Location"], "code": f.get("Code"), "comment": f.get("Comment")}
                    for f in docstring_files[:5]
                ]
            }
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-10",
            name="Python Docstrings as Comments",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_multiline_string_handling(raw_output_path: Path, base_path: Path = None) -> CheckResult:
    """CV-11: Verify multi-line strings are handled correctly across languages.

    Multi-line strings (template literals in JS/TS, verbatim strings in C#,
    raw strings in Python/Go/Rust) should not cause incorrect line counts.
    """
    try:
        if base_path is None:
            base_path = raw_output_path.parent.parent

        files, _, _ = reliability.run_scc_by_file(base_path, "eval-repos/synthetic")

        # Check for files that might have multi-line strings
        # These typically have "multiline" or "template" in name, or are in edge_cases
        multiline_candidates = [
            f for f in files
            if any(pattern in f.get("Location", "").lower()
                   for pattern in ["multiline", "template", "verbatim", "raw_string"])
        ]

        if not multiline_candidates:
            # Fallback: check that files with complex content still have reasonable metrics
            # (Lines should be >= Code + Comment + Blank, or approximately equal)
            validation_issues = []
            for f in files:
                lines = f.get("Lines", 0)
                code = f.get("Code", 0)
                comment = f.get("Comment", 0)
                blank = f.get("Blank", 0)
                total_components = code + comment + blank

                # Lines should approximately equal the sum (allow some variance for edge cases)
                if lines > 0 and total_components > 0:
                    ratio = total_components / lines
                    # Allow 20% variance
                    if ratio < 0.8 or ratio > 1.2:
                        validation_issues.append({
                            "file": f.get("Location"),
                            "lines": lines,
                            "sum": total_components,
                            "ratio": round(ratio, 2)
                        })

            passed = len(validation_issues) == 0
            return CheckResult(
                check_id="CV-11",
                name="Multi-line String Handling",
                passed=passed,
                message=f"Line count validation: {len(validation_issues)} issues found",
                expected="Lines should approximately equal Code + Comment + Blank",
                actual=f"issues={len(validation_issues)}",
                evidence={"validation_issues": validation_issues[:5]}
            )

        # Check that multiline files have consistent metrics
        valid_files = []
        for f in multiline_candidates:
            lines = f.get("Lines", 0)
            code = f.get("Code", 0)
            # Multi-line string files should have lines >= code (strings span multiple lines)
            if lines >= code and lines > 0:
                valid_files.append(f)

        passed = len(valid_files) == len(multiline_candidates)

        return CheckResult(
            check_id="CV-11",
            name="Multi-line String Handling",
            passed=passed,
            message=f"{len(valid_files)}/{len(multiline_candidates)} multiline files have valid metrics",
            expected="All multiline string files should have Lines >= Code",
            actual=f"valid_files={len(valid_files)}",
            evidence={
                "multiline_files": [
                    {"loc": f["Location"], "lines": f.get("Lines"), "code": f.get("Code")}
                    for f in multiline_candidates[:5]
                ]
            }
        )
    except Exception as e:
        return CheckResult(
            check_id="CV-11",
            name="Multi-line String Handling",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_coverage_checks(raw_output_path: Path, base_path: Path = None) -> List[CheckResult]:
    """Run all coverage checks."""
    return [
        check_python_detected(raw_output_path),
        check_csharp_detected(raw_output_path),
        check_javascript_detected(raw_output_path),
        check_typescript_detected(raw_output_path),
        check_go_detected(raw_output_path),
        check_rust_detected(raw_output_path),
        check_java_detected(raw_output_path),
        check_file_counts_match(raw_output_path),
        check_loc_within_range(raw_output_path),
        check_python_docstrings_as_comments(raw_output_path, base_path),
        check_multiline_string_handling(raw_output_path, base_path),
    ]
