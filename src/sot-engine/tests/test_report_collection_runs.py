import duckdb

from report_test_utils import load_sql, render_report_sql


REPORT_PATH = "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/dbt/analysis/report_collection_runs.sql"


def test_report_collection_runs_lists_runs() -> None:
    sql_text = render_report_sql(load_sql(REPORT_PATH), run_pk=1)

    conn = duckdb.connect(database=":memory:")
    conn.execute(
        """
        create table lz_collection_runs (
            collection_run_id varchar,
            repo_id varchar,
            run_id varchar,
            branch varchar,
            commit varchar,
            status varchar,
            started_at timestamp,
            completed_at timestamp
        )
        """
    )
    conn.execute(
        """
        create table lz_tool_runs (
            collection_run_id varchar,
            tool_name varchar,
            run_pk integer
        )
        """
    )
    conn.execute(
        """
        insert into lz_collection_runs values
            ('collection-1', 'repo-1', 'run-1', 'main', 'abc123', 'completed', now(), now())
        """
    )
    conn.execute(
        """
        insert into lz_tool_runs values
            ('collection-1', 'scc', 10),
            ('collection-1', 'lizard', 20)
        """
    )

    rows = conn.execute(sql_text).fetchall()
    assert rows
