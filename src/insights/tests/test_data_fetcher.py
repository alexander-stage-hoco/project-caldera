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


class TestRenderTemplateMultipleVariables:
    """Tests for _render_template with multiple variables."""

    def test_multiple_variables_in_same_template(self):
        """Test rendering a template with multiple distinct variables."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = (
            "SELECT * FROM t WHERE run_pk = {{ run_pk }} "
            "AND tool = '{{ tool_name }}' LIMIT {{ limit }}"
        )
        result = fetcher._render_template(template, run_pk=42, tool_name="scc", limit=10)

        assert result == "SELECT * FROM t WHERE run_pk = 42 AND tool = 'scc' LIMIT 10"

    def test_variable_with_default_and_required_mixed(self):
        """Test template with both a required variable and a default-valued one."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        template = (
            "SELECT * FROM t WHERE run_pk = {{ run_pk }} "
            "ORDER BY {{ order | default('id') }}"
        )
        # Only supply run_pk, let order use default
        result = fetcher._render_template(template, run_pk=7)
        assert result == "SELECT * FROM t WHERE run_pk = 7 ORDER BY id"


class TestFetchMart:
    """Tests for fetch_mart SQL construction."""

    def test_fetch_mart_with_mixed_filters(self, tmp_path):
        """Test fetch_mart builds correct SQL with string, numeric, and None filters."""
        db_path = tmp_path / "test_mart.duckdb"
        import duckdb
        conn = duckdb.connect(str(db_path))
        conn.execute("""
            CREATE TABLE my_mart (
                run_pk BIGINT,
                language VARCHAR,
                severity VARCHAR,
                score INTEGER
            )
        """)
        conn.execute("""
            INSERT INTO my_mart VALUES
                (1, 'Python', 'high', 10),
                (1, 'Python', NULL, 5),
                (1, 'Java', 'low', 3)
        """)
        conn.close()

        fetcher = DataFetcher(db_path=db_path)
        # string filter + None filter
        results = fetcher.fetch_mart(
            "my_mart",
            run_pk=1,
            filters={"language": "Python", "severity": None},
        )
        assert len(results) == 1
        assert results[0]["score"] == 5

    def test_fetch_mart_with_numeric_filter(self, tmp_path):
        """Test fetch_mart with numeric filter value."""
        db_path = tmp_path / "test_mart2.duckdb"
        import duckdb
        conn = duckdb.connect(str(db_path))
        conn.execute("""
            CREATE TABLE my_mart (run_pk BIGINT, score INTEGER)
        """)
        conn.execute("INSERT INTO my_mart VALUES (1, 10), (1, 20), (1, 30)")
        conn.close()

        fetcher = DataFetcher(db_path=db_path)
        results = fetcher.fetch_mart("my_mart", run_pk=1, filters={"score": 20})
        assert len(results) == 1
        assert results[0]["score"] == 20

    def test_fetch_mart_with_limit_and_order_by(self, tmp_path):
        """Test fetch_mart with limit and order_by parameters."""
        db_path = tmp_path / "test_mart3.duckdb"
        import duckdb
        conn = duckdb.connect(str(db_path))
        conn.execute("""
            CREATE TABLE my_mart (run_pk BIGINT, name VARCHAR, score INTEGER)
        """)
        conn.execute("""
            INSERT INTO my_mart VALUES (1, 'a', 30), (1, 'b', 10), (1, 'c', 20)
        """)
        conn.close()

        fetcher = DataFetcher(db_path=db_path)
        results = fetcher.fetch_mart(
            "my_mart",
            run_pk=1,
            order_by="score DESC",
            limit=2,
        )
        assert len(results) == 2
        assert results[0]["score"] == 30
        assert results[1]["score"] == 20


class TestGetRunInfoNotFound:
    """Test get_run_info error handling."""

    def test_raises_for_nonexistent_run_pk(self, tmp_path):
        """get_run_info with non-existent run_pk should raise ValueError."""
        db_path = tmp_path / "test_runinfo.duckdb"
        import duckdb
        conn = duckdb.connect(str(db_path))
        conn.execute("""
            CREATE TABLE stg_lz_tool_runs (
                run_pk BIGINT,
                collection_run_id VARCHAR,
                repo_id VARCHAR,
                run_id VARCHAR,
                tool_name VARCHAR,
                branch VARCHAR,
                commit VARCHAR,
                timestamp TIMESTAMP
            )
        """)
        conn.close()

        fetcher = DataFetcher(db_path=db_path)
        with pytest.raises(ValueError, match="No tool run found"):
            fetcher.get_run_info(run_pk=9999)


class TestDataFetcherQueries:
    """Tests for query loading."""

    def test_load_query_not_found(self):
        """Test loading a non-existent query raises FileNotFoundError."""
        fetcher = DataFetcher(db_path=Path("/tmp/test.db"))

        with pytest.raises(FileNotFoundError):
            fetcher._load_query("nonexistent_query")
