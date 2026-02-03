"""Call accuracy checks for programmatic evaluation."""

from __future__ import annotations


def check_call_count(actual: list, expected: list) -> dict:
    """Check that call counts match."""
    return {
        "name": "call_count",
        "passed": len(actual) == len(expected),
        "expected": len(expected),
        "actual": len(actual),
    }


def check_caller_callee_pairs(actual: list, expected: list) -> dict:
    """Check that caller/callee pairs are accurate."""
    actual_pairs = {
        (c.get("caller_file"), c.get("caller_symbol"), c.get("callee_symbol"))
        for c in actual
    }
    expected_pairs = {
        (c.get("caller_file"), c.get("caller_symbol"), c.get("callee_symbol"))
        for c in expected
    }

    matches = len(actual_pairs & expected_pairs)
    total = len(expected_pairs)

    return {
        "name": "caller_callee_pairs",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def check_call_types(actual: list, expected: list) -> dict:
    """Check that call types are accurate."""
    actual_types = {
        (c.get("caller_file"), c.get("caller_symbol"), c.get("callee_symbol")): c.get("call_type")
        for c in actual
    }
    expected_types = {
        (c.get("caller_file"), c.get("caller_symbol"), c.get("callee_symbol")): c.get("call_type")
        for c in expected
    }

    matches = sum(1 for k in expected_types if actual_types.get(k) == expected_types[k])
    total = len(expected_types)

    return {
        "name": "call_types",
        "passed": matches == total,
        "expected": total,
        "actual": matches,
    }


def run_checks(actual_data: dict, expected_data: dict) -> list[dict]:
    """Run all call accuracy checks."""
    actual_calls = actual_data.get("calls", [])
    expected_calls = expected_data.get("expected", {}).get("calls", [])

    return [
        check_call_count(actual_calls, expected_calls),
        check_caller_callee_pairs(actual_calls, expected_calls),
        check_call_types(actual_calls, expected_calls),
    ]
