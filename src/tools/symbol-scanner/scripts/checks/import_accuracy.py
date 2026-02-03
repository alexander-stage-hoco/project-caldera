"""Import accuracy checks for programmatic evaluation."""

from __future__ import annotations


def check_import_count(actual: list, expected: list) -> dict:
    """Check that import counts match."""
    return {
        "name": "import_count",
        "passed": len(actual) == len(expected),
        "expected": len(expected),
        "actual": len(actual),
    }


def check_import_paths(actual: list, expected: list) -> dict:
    """Check that import paths are accurate."""
    actual_paths = {(i.get("file"), i.get("imported_path")) for i in actual}
    expected_paths = {(i.get("file"), i.get("imported_path")) for i in expected}

    matches = len(actual_paths & expected_paths)
    total = len(expected_paths)

    return {
        "name": "import_paths",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def check_import_symbols(actual: list, expected: list) -> dict:
    """Check that imported symbols are accurate."""
    actual_symbols = {
        (i.get("file"), i.get("imported_path")): i.get("imported_symbols")
        for i in actual
    }
    expected_symbols = {
        (i.get("file"), i.get("imported_path")): i.get("imported_symbols")
        for i in expected
    }

    matches = sum(1 for k in expected_symbols if actual_symbols.get(k) == expected_symbols[k])
    total = len(expected_symbols)

    return {
        "name": "import_symbols",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def run_checks(actual_data: dict, expected_data: dict) -> list[dict]:
    """Run all import accuracy checks."""
    actual_imports = actual_data.get("imports", [])
    expected_imports = expected_data.get("expected", {}).get("imports", [])

    return [
        check_import_count(actual_imports, expected_imports),
        check_import_paths(actual_imports, expected_imports),
        check_import_symbols(actual_imports, expected_imports),
    ]
