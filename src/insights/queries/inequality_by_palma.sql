-- Top directories by Palma ratio for code inequality analysis
-- Palma ratio = top 10% / bottom 40% (higher = more inequality)
-- A ratio >= 2.0 indicates significant concentration at the top

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
scc_palma AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        palma_value,
        gini_value,
        value_count AS file_count,
        top_10_pct_share,
        bottom_50_pct_share
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric IN ('lines_total', 'complexity')
      AND palma_value >= 2.0
      AND value_count >= 10  -- Need at least 10 files for meaningful Palma
),
lizard_palma AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        palma_value,
        gini_value,
        value_count AS file_count,
        top_10_pct_share,
        bottom_50_pct_share
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric IN ('total_ccn', 'nloc')
      AND palma_value >= 2.0
      AND value_count >= 10
),
combined AS (
    SELECT * FROM scc_palma
    UNION ALL
    SELECT * FROM lizard_palma
)
SELECT
    directory_path,
    metric,
    ROUND(palma_value, 2) AS palma_ratio,
    ROUND(gini_value, 3) AS gini,
    file_count,
    ROUND(top_10_pct_share * 100, 1) AS top_10_pct,
    ROUND(bottom_50_pct_share * 100, 1) AS bottom_50_pct
FROM combined
ORDER BY palma_value DESC, directory_path
LIMIT 30
