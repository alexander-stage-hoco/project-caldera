import duckdb

from report_test_utils import load_sql, render_report_sql


REPORT_PATH = "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/dbt/analysis/report_hotspot_directories.sql"


def test_report_hotspot_directories_returns_rows() -> None:
    sql_text = render_report_sql(load_sql(REPORT_PATH), run_pk=10)

    conn = duckdb.connect(database=":memory:")
    conn.execute(
        """
        create table unified_run_summary (
            run_pk integer,
            repo_id varchar,
            run_id varchar
        )
        """
    )
    conn.execute(
        """
        create table lz_layout_directories (
            run_pk integer,
            directory_id varchar,
            relative_path varchar
        )
        """
    )
    conn.execute(
        """
        create table rollup_scc_directory_recursive_distributions (
            run_pk integer,
            directory_id varchar,
            metric varchar,
            directory_path varchar,
            value_count integer,
            avg_value double,
            p95_value double,
            p99_value double,
            gini_value double,
            hoover_value double,
            palma_value double,
            top_20_pct_share double
        )
        """
    )
    conn.execute(
        """
        create table rollup_lizard_directory_recursive_distributions (
            run_pk integer,
            directory_id varchar,
            metric varchar,
            directory_path varchar,
            value_count integer,
            avg_value double,
            p95_value double,
            p99_value double,
            gini_value double,
            hoover_value double,
            palma_value double,
            top_20_pct_share double
        )
        """
    )
    conn.execute("insert into unified_run_summary values (10, 'repo-1', 'run-1')")
    conn.execute("insert into lz_layout_directories values (10, 'dir-1', 'src')")
    conn.execute(
        """
        insert into rollup_scc_directory_recursive_distributions values
            (10, 'dir-1', 'lines_total', 'src', 12, 10.0, 120.0, 140.0, 0.1, 0.2, 0.3, 0.4)
        """
    )
    conn.execute(
        """
        insert into rollup_lizard_directory_recursive_distributions values
            (10, 'dir-1', 'total_ccn', 'src', 12, 2.5, 8.0, 9.0, 0.4, 0.5, 0.6, 0.7)
        """
    )

    rows = conn.execute(sql_text).fetchall()
    assert rows
