"""Tests targeting uncovered paths in license_analyzer.py for coverage improvement."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.license_analyzer import get_category_with_exception, get_category


class TestGetCategoryWithException:
    """Tests for SPDX exception-aware category determination."""

    def test_gpl_with_classpath_is_weak_copyleft(self) -> None:
        result = get_category_with_exception("GPL-2.0-only WITH Classpath-exception-2.0")
        assert result == "weak-copyleft"

    def test_gpl_with_gcc_is_weak_copyleft(self) -> None:
        result = get_category_with_exception("GPL-3.0-only WITH GCC-exception-3.1")
        assert result == "weak-copyleft"

    def test_apache_with_llvm_is_permissive(self) -> None:
        result = get_category_with_exception("Apache-2.0 WITH LLVM-exception")
        assert result == "permissive"

    def test_plain_mit_is_permissive(self) -> None:
        result = get_category_with_exception("MIT")
        assert result == "permissive"

    def test_unknown_exception_falls_back_to_base(self) -> None:
        result = get_category_with_exception("GPL-3.0-only WITH unknown-exception")
        # Falls back to base license category
        assert result == "copyleft"
