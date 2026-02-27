"""Tests for report formatters."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from insights.formatters.html import HtmlFormatter
from insights.formatters.markdown import MarkdownFormatter
from insights.sections.base import SectionData


class TestHtmlFormatter:
    """Tests for HtmlFormatter."""

    def test_format_number_filter(self):
        """Test number formatting filter."""
        assert HtmlFormatter._format_number(1234567) == "1,234,567"
        assert HtmlFormatter._format_number(1234.56) == "1,234.56"
        assert HtmlFormatter._format_number(None) == "N/A"

    def test_format_percent_filter(self):
        """Test percentage formatting filter."""
        assert HtmlFormatter._format_percent(45.678) == "45.7%"
        assert HtmlFormatter._format_percent(None) == "N/A"

    def test_severity_class_filter(self):
        """Test severity CSS class filter."""
        assert HtmlFormatter._severity_class("CRITICAL") == "severity-critical"
        assert HtmlFormatter._severity_class("HIGH") == "severity-high"
        assert HtmlFormatter._severity_class("Medium") == "severity-medium"
        assert HtmlFormatter._severity_class(None) == "severity-unknown"

    def test_grade_class_filter(self):
        """Test grade CSS class filter."""
        assert HtmlFormatter._grade_class("A") == "grade-a"
        assert HtmlFormatter._grade_class("F") == "grade-f"
        assert HtmlFormatter._grade_class(None) == "grade-unknown"

    def test_truncate_path_filter(self):
        """Test path truncation filter."""
        short_path = "src/file.py"
        long_path = "very/long/path/to/some/deeply/nested/file.py"

        assert HtmlFormatter._truncate_path(short_path) == short_path
        assert HtmlFormatter._truncate_path(long_path, max_length=30).startswith("...")
        assert len(HtmlFormatter._truncate_path(long_path, max_length=30)) == 30


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_severity_emoji_filter(self):
        """Test severity emoji filter."""
        assert MarkdownFormatter._severity_emoji("critical") == "🔴"
        assert MarkdownFormatter._severity_emoji("HIGH") == "🟠"
        assert MarkdownFormatter._severity_emoji("medium") == "🟡"
        assert MarkdownFormatter._severity_emoji("low") == "🟢"
        assert MarkdownFormatter._severity_emoji(None) == "⚪"

    def test_grade_emoji_filter(self):
        """Test grade emoji filter."""
        assert MarkdownFormatter._grade_emoji("A") == "🟢"
        assert MarkdownFormatter._grade_emoji("c") == "🟡"
        assert MarkdownFormatter._grade_emoji("F") == "🔴"
        assert MarkdownFormatter._grade_emoji(None) == "⚪"

    def test_md_table_filter(self):
        """Test Markdown table generation."""
        rows = [
            {"name": "file1.py", "loc": 100},
            {"name": "file2.py", "loc": 200},
        ]

        table = MarkdownFormatter._md_table(rows)

        assert "| name | loc |" in table
        assert "|---|" in table or "| --- |" in table
        assert "| file1.py | 100 |" in table
        assert "| file2.py | 200 |" in table

    def test_md_table_empty(self):
        """Test Markdown table with empty data."""
        table = MarkdownFormatter._md_table([])
        assert table == "*No data available*"

    def test_md_table_with_columns(self):
        """Test Markdown table with specific columns."""
        rows = [
            {"name": "file.py", "loc": 100, "ccn": 5},
        ]

        table = MarkdownFormatter._md_table(rows, columns=["name", "loc"])

        assert "| name | loc |" in table
        assert "ccn" not in table

    def test_severity_emoji_info(self):
        """Test severity emoji for 'info' level."""
        assert MarkdownFormatter._severity_emoji("info") == "\U0001f535"


class TestHtmlFormatterFalsyEdgeCase:
    """Edge case tests for HtmlFormatter."""

    def test_format_number_zero(self):
        """_format_number(0) should return '0', not 'N/A' (falsy edge case)."""
        result = HtmlFormatter._format_number(0)
        assert result == "0"

    def test_format_number_zero_float(self):
        """_format_number(0.0) should return '0.00', not 'N/A'."""
        result = HtmlFormatter._format_number(0.0)
        assert result == "0.00"


class TestMarkdownFormatterFalsyEdgeCase:
    """Edge case tests for MarkdownFormatter."""

    def test_format_number_zero(self):
        """_format_number(0) should return '0', not 'N/A'."""
        result = MarkdownFormatter._format_number(0)
        assert result == "0"

    def test_format_number_zero_float(self):
        """_format_number(0.0) should return '0.00', not 'N/A'."""
        result = MarkdownFormatter._format_number(0.0)
        assert result == "0.00"
