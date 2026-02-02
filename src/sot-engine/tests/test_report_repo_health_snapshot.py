import duckdb

from report_test_utils import load_sql, render_report_sql


REPORT_PATH = "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/dbt/analysis/report_repo_health_snapshot.sql"


def test_report_health_snapshot_joins_lizard_run() -> None:
    sql_text = render_report_sql(load_sql(REPORT_PATH), run_pk=10)

    conn = duckdb.connect(database=":memory:")
    conn.execute(
        """
        create table unified_run_summary (
            run_pk integer,
            collection_run_id varchar,
            repo_id varchar,
            run_id varchar,
            total_files integer,
            total_loc integer,
            total_code integer,
            total_comment integer,
            total_blank integer,
            total_ccn integer,
            avg_ccn double,
            max_ccn integer,
            avg_nloc double
        )
        """
    )
    conn.execute(
        """
        create table lz_tool_runs (
            run_pk integer,
            collection_run_id varchar,
            tool_name varchar
        )
        """
    )
    conn.execute(
        """
        create table rollup_scc_directory_recursive_distributions (
            run_pk integer,
            directory_path varchar,
            metric varchar,
            p95_value double,
            p99_value double,
            gini_value double,
            hoover_value double,
            top_20_pct_share double
        )
        """
    )
    conn.execute(
        """
        create table rollup_lizard_directory_recursive_distributions (
            run_pk integer,
            directory_path varchar,
            metric varchar,
            p95_value double,
            p99_value double,
            gini_value double,
            hoover_value double,
            top_20_pct_share double
        )
        """
    )
    conn.execute(
        """
        create table rollup_roslyn_directory_recursive_distributions (
            run_pk integer,
            directory_path varchar,
            metric varchar,
            p95_value double,
            p99_value double,
            gini_value double,
            hoover_value double,
            top_20_pct_share double
        )
        """
    )
    conn.execute(
        """
        create table repo_health_summary (
            run_pk integer,
            health_grade varchar,
            violation_count integer,
            max_violation_level integer,
            lfs_candidate_count integer,
            commit_count integer,
            blob_count integer,
            blob_total_size bigint,
            max_blob_size bigint,
            tree_count integer,
            max_tree_entries integer,
            max_path_depth integer,
            max_path_length integer,
            reference_count integer,
            branch_count integer,
            tag_count integer
        )
        """
    )
    conn.execute(
        """
        insert into unified_run_summary values
            (10, 'collection-1', 'repo-1', 'run-1', 2, 20, 10, 5, 5, 9, 1.5, 3, 42.0)
        """
    )
    conn.execute(
        """
        insert into lz_tool_runs values
            (10, 'collection-1', 'scc'),
            (20, 'collection-1', 'lizard')
        """
    )
    conn.execute(
        """
        insert into rollup_scc_directory_recursive_distributions values
            (10, '', 'lines_total', 12.0, 14.0, 0.1, 0.2, 0.3)
        """
    )
    conn.execute(
        """
        insert into rollup_lizard_directory_recursive_distributions values
            (20, '', 'total_ccn', 7.0, 8.0, 0.4, 0.5, 0.6)
        """
    )

    rows = conn.execute(sql_text).fetchall()
    assert rows
    assert rows[0][16] == 7.0
