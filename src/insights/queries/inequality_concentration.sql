-- Concentration analysis: directories where top 20% holds >= 50% of total
-- Identifies "god file" syndrome where a few files dominate the directory

-- Resolve tool-specific run_pks from collection
WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
),
scc_concentration AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        top_10_pct_share,
        top_20_pct_share,
        bottom_50_pct_share,
        gini_value,
        hoover_value,
        value_count AS file_count,
        avg_value,
        max_value,
        p99_value
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric IN ('lines_total', 'complexity')
      AND top_20_pct_share >= 0.50  -- Top 20% has at least 50%
      AND value_count >= 5
),
lizard_concentration AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        top_10_pct_share,
        top_20_pct_share,
        bottom_50_pct_share,
        gini_value,
        hoover_value,
        value_count AS file_count,
        avg_value,
        max_value,
        p99_value
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric IN ('total_ccn', 'nloc')
      AND top_20_pct_share >= 0.50
      AND value_count >= 5
),
combined AS (
    SELECT * FROM scc_concentration
    UNION ALL
    SELECT * FROM lizard_concentration
)
SELECT
    directory_path,
    metric,
    ROUND(top_10_pct_share * 100, 1) AS top_10_share,
    ROUND(top_20_pct_share * 100, 1) AS top_20_share,
    ROUND(bottom_50_pct_share * 100, 1) AS bottom_50_share,
    ROUND(gini_value, 3) AS gini,
    ROUND(hoover_value, 3) AS hoover,
    file_count,
    ROUND(avg_value, 1) AS avg_value,
    ROUND(max_value, 1) AS max_value,
    ROUND(p99_value, 1) AS p99_value,
    ROUND(max_value / NULLIF(avg_value, 0), 1) AS max_to_avg_ratio
FROM combined
ORDER BY top_20_pct_share DESC, directory_path
LIMIT 30
