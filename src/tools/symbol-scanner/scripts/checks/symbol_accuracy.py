"""Symbol accuracy checks for programmatic evaluation."""

from __future__ import annotations


def check_symbol_count(actual: list, expected: list) -> dict:
    """Check that symbol counts match."""
    return {
        "name": "symbol_count",
        "passed": len(actual) == len(expected),
        "expected": len(expected),
        "actual": len(actual),
    }


def check_symbol_types(actual: list, expected: list) -> dict:
    """Check that symbol types are accurate."""
    actual_types = {(s.get("path"), s.get("symbol_name")): s.get("symbol_type") for s in actual}
    expected_types = {(s.get("path"), s.get("symbol_name")): s.get("symbol_type") for s in expected}

    matches = sum(1 for k in expected_types if actual_types.get(k) == expected_types[k])
    total = len(expected_types)

    return {
        "name": "symbol_types",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def check_line_numbers(actual: list, expected: list) -> dict:
    """Check that line numbers are accurate."""
    actual_lines = {(s.get("path"), s.get("symbol_name")): s.get("line_start") for s in actual}
    expected_lines = {(s.get("path"), s.get("symbol_name")): s.get("line_start") for s in expected}

    matches = sum(1 for k in expected_lines if actual_lines.get(k) == expected_lines[k])
    total = len(expected_lines)

    return {
        "name": "line_numbers",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def run_checks(actual_data: dict, expected_data: dict) -> list[dict]:
    """Run all symbol accuracy checks."""
    actual_symbols = actual_data.get("symbols", [])
    expected_symbols = expected_data.get("expected", {}).get("symbols", [])

    return [
        check_symbol_count(actual_symbols, expected_symbols),
        check_symbol_types(actual_symbols, expected_symbols),
        check_line_numbers(actual_symbols, expected_symbols),
    ]
