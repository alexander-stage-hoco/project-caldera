"""Unit tests for the evaluation harness."""

from __future__ import annotations

import pytest

import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from evaluate import (
    Metrics,
    CategoryMetrics,
    DetailedResult,
    EvaluationResult,
    compare_symbols,
    compare_calls,
    compare_imports,
    _symbol_key,
    _call_key,
    _import_key,
)


class TestMetrics:
    """Tests for the Metrics dataclass."""

    def test_precision_perfect(self) -> None:
        """Test precision with perfect results."""
        m = Metrics(true_positives=10, false_positives=0, false_negatives=0)
        assert m.precision == 1.0

    def test_precision_partial(self) -> None:
        """Test precision with some false positives."""
        m = Metrics(true_positives=8, false_positives=2, false_negatives=0)
        assert m.precision == 0.8

    def test_precision_zero_found(self) -> None:
        """Test precision when nothing found and nothing expected."""
        m = Metrics(true_positives=0, false_positives=0, false_negatives=0)
        assert m.precision == 1.0  # Nothing to find, nothing found = perfect

    def test_precision_zero_found_with_expected(self) -> None:
        """Test precision when nothing found but items were expected."""
        m = Metrics(true_positives=0, false_positives=0, false_negatives=5)
        assert m.precision == 0.0

    def test_recall_perfect(self) -> None:
        """Test recall with perfect results."""
        m = Metrics(true_positives=10, false_positives=0, false_negatives=0)
        assert m.recall == 1.0

    def test_recall_partial(self) -> None:
        """Test recall with some misses."""
        m = Metrics(true_positives=8, false_positives=0, false_negatives=2)
        assert m.recall == 0.8

    def test_recall_zero_expected(self) -> None:
        """Test recall when nothing expected."""
        m = Metrics(true_positives=0, false_positives=0, false_negatives=0)
        assert m.recall == 1.0

    def test_recall_zero_found(self) -> None:
        """Test recall when nothing found but items expected."""
        m = Metrics(true_positives=0, false_positives=0, false_negatives=5)
        assert m.recall == 0.0

    def test_f1_perfect(self) -> None:
        """Test F1 with perfect results."""
        m = Metrics(true_positives=10, false_positives=0, false_negatives=0)
        assert m.f1 == 1.0

    def test_f1_balanced(self) -> None:
        """Test F1 with balanced precision and recall."""
        m = Metrics(true_positives=8, false_positives=2, false_negatives=2)
        # P = 8/10 = 0.8, R = 8/10 = 0.8, F1 = 0.8
        assert abs(m.f1 - 0.8) < 0.001

    def test_f1_zero(self) -> None:
        """Test F1 when nothing found."""
        m = Metrics(true_positives=0, false_positives=0, false_negatives=5)
        assert m.f1 == 0.0

    def test_f1_zero_precision_recall(self) -> None:
        """Test F1 when both P and R are zero."""
        m = Metrics(true_positives=0, false_positives=5, false_negatives=5)
        assert m.f1 == 0.0

    def test_add_metrics(self) -> None:
        """Test adding two Metrics objects."""
        m1 = Metrics(true_positives=5, false_positives=1, false_negatives=2)
        m2 = Metrics(true_positives=3, false_positives=2, false_negatives=1)
        combined = m1 + m2
        assert combined.true_positives == 8
        assert combined.false_positives == 3
        assert combined.false_negatives == 3


class TestCategoryMetrics:
    """Tests for CategoryMetrics."""

    def test_add_single_category(self) -> None:
        """Test adding a single category."""
        cm = CategoryMetrics()
        cm.add("function", Metrics(5, 1, 2))
        assert "function" in cm.by_type
        assert cm.total.true_positives == 5

    def test_add_multiple_categories(self) -> None:
        """Test adding multiple categories."""
        cm = CategoryMetrics()
        cm.add("function", Metrics(5, 1, 2))
        cm.add("class", Metrics(3, 0, 1))
        cm.add("method", Metrics(10, 2, 3))
        assert cm.total.true_positives == 18
        assert cm.total.false_positives == 3
        assert cm.total.false_negatives == 6


class TestCompareSymbols:
    """Tests for symbol comparison."""

    def test_perfect_match(self) -> None:
        """Test perfect symbol match."""
        expected = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
            {"path": "main.py", "symbol_name": "bar", "symbol_type": "function", "line_start": 5},
        ]
        actual = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
            {"path": "main.py", "symbol_name": "bar", "symbol_type": "function", "line_start": 5},
        ]
        metrics, details = compare_symbols(expected, actual)
        assert metrics.total.precision == 1.0
        assert metrics.total.recall == 1.0
        assert metrics.total.f1 == 1.0
        assert len(details.missing) == 0
        assert len(details.extra) == 0

    def test_missing_symbols(self) -> None:
        """Test with missing symbols."""
        expected = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
            {"path": "main.py", "symbol_name": "bar", "symbol_type": "function", "line_start": 5},
        ]
        actual = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
        ]
        metrics, details = compare_symbols(expected, actual)
        assert metrics.total.true_positives == 1
        assert metrics.total.false_negatives == 1
        assert metrics.total.recall == 0.5
        assert len(details.missing) == 1
        assert details.missing[0]["symbol_name"] == "bar"

    def test_extra_symbols(self) -> None:
        """Test with extra symbols."""
        expected = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
        ]
        actual = [
            {"path": "main.py", "symbol_name": "foo", "symbol_type": "function", "line_start": 1},
            {"path": "main.py", "symbol_name": "extra", "symbol_type": "function", "line_start": 10},
        ]
        metrics, details = compare_symbols(expected, actual)
        assert metrics.total.true_positives == 1
        assert metrics.total.false_positives == 1
        assert metrics.total.precision == 0.5
        assert len(details.extra) == 1
        assert details.extra[0]["symbol_name"] == "extra"

    def test_metrics_by_type(self) -> None:
        """Test that metrics are correctly grouped by symbol type."""
        expected = [
            {"path": "main.py", "symbol_name": "Foo", "symbol_type": "class", "line_start": 1},
            {"path": "main.py", "symbol_name": "bar", "symbol_type": "function", "line_start": 10},
            {"path": "main.py", "symbol_name": "baz", "symbol_type": "method", "line_start": 5},
        ]
        actual = [
            {"path": "main.py", "symbol_name": "Foo", "symbol_type": "class", "line_start": 1},
            {"path": "main.py", "symbol_name": "bar", "symbol_type": "function", "line_start": 10},
        ]
        metrics, _ = compare_symbols(expected, actual)
        assert "class" in metrics.by_type
        assert "function" in metrics.by_type
        assert "method" in metrics.by_type
        assert metrics.by_type["class"].f1 == 1.0
        assert metrics.by_type["function"].f1 == 1.0
        assert metrics.by_type["method"].f1 == 0.0


class TestCompareCalls:
    """Tests for call comparison."""

    def test_perfect_match(self) -> None:
        """Test perfect call match."""
        expected = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
        ]
        actual = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
        ]
        metrics, details = compare_calls(expected, actual)
        assert metrics.total.f1 == 1.0
        assert len(details.missing) == 0
        assert len(details.extra) == 0

    def test_missing_calls(self) -> None:
        """Test with missing calls."""
        expected = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "baz",
             "line_number": 6, "call_type": "direct"},
        ]
        actual = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
        ]
        metrics, details = compare_calls(expected, actual)
        assert metrics.total.false_negatives == 1
        assert len(details.missing) == 1

    def test_metrics_by_call_type(self) -> None:
        """Test that metrics are grouped by call type."""
        expected = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "baz",
             "line_number": 6, "call_type": "dynamic"},
        ]
        actual = [
            {"caller_file": "main.py", "caller_symbol": "foo", "callee_symbol": "bar",
             "line_number": 5, "call_type": "direct"},
        ]
        metrics, _ = compare_calls(expected, actual)
        assert "direct" in metrics.by_type
        assert "dynamic" in metrics.by_type
        assert metrics.by_type["direct"].f1 == 1.0
        assert metrics.by_type["dynamic"].f1 == 0.0


class TestCompareImports:
    """Tests for import comparison."""

    def test_perfect_match(self) -> None:
        """Test perfect import match."""
        expected = [
            {"file": "main.py", "imported_path": "os", "import_type": "static", "line_number": 1},
        ]
        actual = [
            {"file": "main.py", "imported_path": "os", "import_type": "static", "line_number": 1},
        ]
        metrics, details = compare_imports(expected, actual)
        assert metrics.total.f1 == 1.0
        assert len(details.missing) == 0
        assert len(details.extra) == 0

    def test_missing_imports(self) -> None:
        """Test with missing imports."""
        expected = [
            {"file": "main.py", "imported_path": "os", "import_type": "static", "line_number": 1},
            {"file": "main.py", "imported_path": "sys", "import_type": "static", "line_number": 2},
        ]
        actual = [
            {"file": "main.py", "imported_path": "os", "import_type": "static", "line_number": 1},
        ]
        metrics, details = compare_imports(expected, actual)
        assert metrics.total.false_negatives == 1
        assert len(details.missing) == 1
        assert details.missing[0]["imported_path"] == "sys"


class TestEvaluationResult:
    """Tests for EvaluationResult."""

    def test_overall_f1(self) -> None:
        """Test overall F1 calculation."""
        result = EvaluationResult(repo_name="test", strategy="ast")
        result.symbols.add("function", Metrics(10, 0, 0))  # F1 = 1.0
        result.calls.add("direct", Metrics(5, 0, 5))  # F1 = 0.666...
        result.imports.add("static", Metrics(3, 0, 0))  # F1 = 1.0
        # Combined: TP=18, FP=0, FN=5 -> P=1.0, R=18/23, F1 = 2*(1*0.78)/(1+0.78)
        assert result.overall_f1 > 0.8


class TestKeyFunctions:
    """Tests for key generation functions."""

    def test_symbol_key(self) -> None:
        """Test symbol key generation."""
        s = {"path": "main.py", "symbol_name": "foo", "line_start": 10}
        key = _symbol_key(s)
        assert key == ("main.py", "foo", 10)

    def test_call_key(self) -> None:
        """Test call key generation."""
        c = {"caller_file": "main.py", "caller_symbol": "foo",
             "callee_symbol": "bar", "line_number": 5}
        key = _call_key(c)
        assert key == ("main.py", "foo", "bar", 5)

    def test_import_key(self) -> None:
        """Test import key generation."""
        i = {"file": "main.py", "imported_path": "os", "line_number": 1}
        key = _import_key(i)
        assert key == ("main.py", "os", 1)

    def test_key_with_missing_optional(self) -> None:
        """Test key with missing optional field."""
        s = {"path": "main.py", "symbol_name": "foo"}
        key = _symbol_key(s)
        assert key == ("main.py", "foo", None)
