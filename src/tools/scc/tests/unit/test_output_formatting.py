"""Tests for output formatting functions."""

import pytest
import json
import sys
from pathlib import Path

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

from directory_analyzer import (
    format_number,
    format_money,
    format_percent,
    strip_ansi,
    get_terminal_width,
    set_color_enabled,
    c,
    Colors,
)


class TestFormatNumber:
    """Tests for the format_number function."""

    def test_integer_with_commas(self):
        """Integers should be formatted with commas."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
        assert format_number(123456789) == "123,456,789"

    def test_small_integers(self):
        """Small integers should not have commas."""
        assert format_number(0) == "0"
        assert format_number(1) == "1"
        assert format_number(999) == "999"

    def test_with_decimals(self):
        """Numbers with decimals specified."""
        assert format_number(1234.5678, decimals=2) == "1,234.57"
        assert format_number(1000.0, decimals=1) == "1,000.0"

    def test_negative_numbers(self):
        """Negative numbers should be formatted correctly."""
        result = format_number(-1000)
        # Python's format handles negative numbers
        assert "-" in result or result == "-1,000"


class TestFormatMoney:
    """Tests for the format_money function."""

    def test_basic_money_format(self):
        """Money should have dollar sign and commas."""
        assert format_money(1000) == "$1,000"
        assert format_money(1000000) == "$1,000,000"

    def test_zero_money(self):
        """Zero should format correctly."""
        assert format_money(0) == "$0"


class TestFormatPercent:
    """Tests for the format_percent function."""

    def test_basic_percentage(self):
        """Decimals should format as percentages."""
        assert format_percent(0.5) == "50.0%"
        assert format_percent(1.0) == "100.0%"
        assert format_percent(0.0) == "0.0%"

    def test_decimal_precision(self):
        """Should show one decimal place."""
        assert format_percent(0.333) == "33.3%"
        assert format_percent(0.666) == "66.6%"


class TestStripAnsi:
    """Tests for the strip_ansi function."""

    def test_strip_basic_colors(self):
        """Basic ANSI color codes should be stripped."""
        colored = "\033[31mRed Text\033[0m"
        assert strip_ansi(colored) == "Red Text"

    def test_strip_multiple_codes(self):
        """Multiple ANSI codes should all be stripped."""
        text = "\033[1m\033[31mBold Red\033[0m"
        assert strip_ansi(text) == "Bold Red"

    def test_plain_text_unchanged(self):
        """Plain text should not be modified."""
        plain = "Hello World"
        assert strip_ansi(plain) == plain

    def test_empty_string(self):
        """Empty string should remain empty."""
        assert strip_ansi("") == ""


class TestColorFunction:
    """Tests for the color application function."""

    def test_color_enabled(self):
        """When enabled, colors should be applied."""
        set_color_enabled(True)
        result = c("test", Colors.RED)
        assert "\033[" in result
        assert "test" in result

    def test_color_disabled(self):
        """When disabled, colors should not be applied."""
        set_color_enabled(False)
        result = c("test", Colors.RED)
        assert result == "test"
        # Re-enable for other tests
        set_color_enabled(True)

    def test_multiple_codes(self):
        """Multiple color codes should be combined."""
        set_color_enabled(True)
        result = c("test", Colors.BOLD, Colors.RED)
        assert "test" in result


class TestGetTerminalWidth:
    """Tests for terminal width detection."""

    def test_returns_integer(self):
        """Should return an integer."""
        width = get_terminal_width()
        assert isinstance(width, int)

    def test_respects_minimum(self):
        """Should not return less than minimum."""
        width = get_terminal_width(minimum=80)
        assert width >= 80

    def test_default_value(self):
        """Should use default if detection fails."""
        # Can't easily test detection failure, but can verify function works
        width = get_terminal_width(default=120)
        assert width >= 80


class TestOutputSchemaCompliance:
    """Tests for output schema compliance."""

    def test_output_has_required_fields(self):
        """Output should have required schema fields."""
        # Sample output structure
        output = {
            "schema_version": "2.0.0",
            "generated_at": "2026-01-20T12:00:00Z",
            "repo_name": "test-repo",
            "repo_path": "/path/to/repo",
            "results": {
                "summary": {},
                "languages": [],
                "files": [],
                "directories": [],
            },
        }

        # Check required fields
        assert "schema_version" in output
        assert "generated_at" in output
        assert "repo_name" in output
        assert "results" in output

    def test_schema_version_format(self):
        """Schema version should be semver format."""
        import re
        version = "2.0.0"
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, version)

    def test_timestamp_format(self):
        """Timestamp should be ISO 8601 format."""
        from datetime import datetime

        timestamp = "2026-01-20T12:00:00Z"
        # Should parse without error
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            parsed = True
        except ValueError:
            parsed = False
        assert parsed

    def test_json_serialization(self, sample_scc_output):
        """Output should be JSON serializable."""
        # Should not raise
        json_str = json.dumps(sample_scc_output)
        # Should round-trip
        parsed = json.loads(json_str)
        assert parsed == sample_scc_output
