"""Tests for DataFetcher."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from insights.data_fetcher import DataFetcher


class TestDataFetcher:
    """Tests for the DataFetcher class."""

    def test_render_template_simple(self):
        """Test simple template variable substitution."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = "SELECT * FROM table WHERE run_pk = {{ run_pk }}"
        result = fetcher._render_template(template, run_pk=123)

        assert result == "SELECT * FROM table WHERE run_pk = 123"

    def test_render_template_with_default(self):
        """Test template with default value."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = "LIMIT {{ limit | default(10) }}"

        # Without providing limit
        result = fetcher._render_template(template)
        assert result == "LIMIT 10"

        # With providing limit
        result = fetcher._render_template(template, limit=20)
        assert result == "LIMIT 20"

    def test_render_template_with_quoted_default(self):
        """Test template with quoted default value."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = "ORDER BY {{ order_by | default('complexity') }}"

        result = fetcher._render_template(template)
        assert result == "ORDER BY complexity"

    def test_render_template_missing_required(self):
        """Test that missing required variables raise ValueError."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = "SELECT * FROM table WHERE run_pk = {{ run_pk }}"

        with pytest.raises(ValueError, match="Missing required parameter"):
            fetcher._render_template(template)

    def test_queries_dir_exists(self):
        """Test that queries directory path is set correctly."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        assert fetcher.queries_dir.name == "queries"
        assert fetcher.queries_dir.parent.name == "insights"


class TestDataFetcherQueries:
    """Tests for query loading."""

    def test_load_query_not_found(self):
        """Test loading a non-existent query raises FileNotFoundError."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        with pytest.raises(FileNotFoundError):
            fetcher._load_query("nonexistent_query")
