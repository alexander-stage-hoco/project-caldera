"""
Data fetcher for executing SQL queries against DuckDB with Caldera dbt marts.
"""

from pathlib import Path
from typing import Any
import duckdb
import re


class DataFetcher:
    """Executes SQL queries against DuckDB with Caldera dbt marts."""

    def __init__(self, db_path: Path, dbt_project_dir: Path | None = None):
        """
        Initialize the data fetcher.

        Args:
            db_path: Path to the DuckDB database file (caldera_sot.duckdb).
            dbt_project_dir: Optional path to dbt project directory (unused, for future expansion).
        """
        self.db_path = Path(db_path)
        self.dbt_project_dir = Path(dbt_project_dir) if dbt_project_dir else None
        self.queries_dir = Path(__file__).parent / "queries"

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a DuckDB connection."""
        return duckdb.connect(str(self.db_path), read_only=True)

    def _load_query(self, query_name: str) -> str:
        """Load a SQL query from the queries directory."""
        query_file = self.queries_dir / f"{query_name}.sql"
        if not query_file.exists():
            raise FileNotFoundError(f"Query file not found: {query_file}")
        return query_file.read_text()

    def _render_template(self, template: str, **params) -> str:
        """
        Simple template rendering using Jinja2-style placeholders.

        Supports:
        - {{ variable }} - direct substitution
        - {{ variable | default(value) }} - with default value
        """
        # Handle default filter
        def replace_with_default(match: re.Match) -> str:
            var_name = match.group(1).strip()
            default_val = match.group(2).strip()
            value = params.get(var_name)
            if value is None:
                # Remove quotes from default value if present
                if (default_val.startswith("'") and default_val.endswith("'")) or \
                   (default_val.startswith('"') and default_val.endswith('"')):
                    default_val = default_val[1:-1]
                return str(default_val)
            return str(value)

        # Pattern for {{ var | default(value) }}
        default_pattern = r'\{\{\s*(\w+)\s*\|\s*default\(([^)]+)\)\s*\}\}'
        result = re.sub(default_pattern, replace_with_default, template)

        # Pattern for simple {{ var }}
        def replace_simple(match: re.Match) -> str:
            var_name = match.group(1).strip()
            value = params.get(var_name)
            if value is None:
                raise ValueError(f"Missing required parameter: {var_name}")
            return str(value)

        simple_pattern = r'\{\{\s*(\w+)\s*\}\}'
        result = re.sub(simple_pattern, replace_simple, result)

        return result

    def fetch(self, query_name: str, run_pk: int, **params) -> list[dict[str, Any]]:
        """
        Execute a named query and return results as dicts.

        Args:
            query_name: Name of the query file (without .sql extension).
            run_pk: The collection run primary key.
            **params: Additional parameters for the query template.

        Returns:
            List of dictionaries with query results.
        """
        template = self._load_query(query_name)
        sql = self._render_template(template, run_pk=run_pk, **params)

        with self._get_connection() as conn:
            result = conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def fetch_raw(self, sql: str, **params) -> list[dict[str, Any]]:
        """
        Execute a raw SQL query and return results as dicts.

        Args:
            sql: The SQL query string.
            **params: Parameters for the query template.

        Returns:
            List of dictionaries with query results.
        """
        rendered_sql = self._render_template(sql, **params)

        with self._get_connection() as conn:
            result = conn.execute(rendered_sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def fetch_mart(
        self,
        mart_name: str,
        run_pk: int,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        order_by: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query a mart table directly.

        Args:
            mart_name: Name of the mart table.
            run_pk: The collection run primary key.
            filters: Optional dictionary of column=value filters.
            limit: Optional limit on number of results.
            order_by: Optional ORDER BY clause.

        Returns:
            List of dictionaries with query results.
        """
        sql_parts = [f"SELECT * FROM {mart_name}"]
        conditions = [f"run_pk = {run_pk}"]

        if filters:
            for col, val in filters.items():
                if isinstance(val, str):
                    conditions.append(f"{col} = '{val}'")
                elif val is None:
                    conditions.append(f"{col} IS NULL")
                else:
                    conditions.append(f"{col} = {val}")

        sql_parts.append("WHERE " + " AND ".join(conditions))

        if order_by:
            sql_parts.append(f"ORDER BY {order_by}")

        if limit:
            sql_parts.append(f"LIMIT {limit}")

        sql = " ".join(sql_parts)

        with self._get_connection() as conn:
            result = conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        sql = f"""
        SELECT COUNT(*) as cnt
        FROM information_schema.tables
        WHERE table_name = '{table_name}'
        """
        with self._get_connection() as conn:
            result = conn.execute(sql).fetchone()
            return result[0] > 0 if result else False

    def get_run_info(self, run_pk: int) -> dict[str, Any]:
        """
        Get basic information about a tool run from Caldera's lz_tool_runs.

        Args:
            run_pk: The tool run primary key.

        Returns:
            Dictionary with run information.

        Raises:
            ValueError: If no tool run is found for the given run_pk.
        """
        sql = """
        SELECT
            run_pk,
            collection_run_id,
            repo_id,
            run_id,
            tool_name,
            branch,
            commit,
            timestamp,
            repo_id as repository_name
        FROM stg_lz_tool_runs
        WHERE run_pk = {{ run_pk }}
        """
        results = self.fetch_raw(sql, run_pk=run_pk)
        if results:
            return results[0]

        raise ValueError(
            f"No tool run found for run_pk={run_pk}. "
            f"Use 'insights runs --db <path>' to list available runs, "
            f"or use '--collection-run-id' to specify a collection run ID."
        )

    def get_scc_run_pk_for_collection(self, collection_run_id: str) -> int:
        """
        Get the SCC tool's run_pk for a given collection run.

        The SCC tool is the "anchor" for unified_file_metrics mart, so its run_pk
        should be used when generating collection-level reports.

        Args:
            collection_run_id: The collection run ID (UUID).

        Returns:
            The run_pk for the SCC tool run.

        Raises:
            ValueError: If no SCC run is found for the collection.
        """
        sql = """
        SELECT run_pk
        FROM stg_lz_tool_runs
        WHERE collection_run_id = '{{ collection_run_id }}'
          AND tool_name = 'scc'
        LIMIT 1
        """
        results = self.fetch_raw(sql, collection_run_id=collection_run_id)
        if results:
            return results[0]["run_pk"]

        raise ValueError(
            f"No SCC tool run found for collection_run_id={collection_run_id}. "
            f"The SCC tool run is required as the anchor for unified metrics."
        )

    def list_collection_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        List available collection runs.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of collection run info dictionaries.
        """
        sql = f"""
        SELECT
            collection_run_id,
            repo_id,
            branch,
            commit,
            started_at,
            completed_at,
            status
        FROM lz_collection_runs
        ORDER BY started_at DESC
        LIMIT {limit}
        """
        return self.fetch_raw(sql)
