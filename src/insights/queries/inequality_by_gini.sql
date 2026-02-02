-- Top directories by Gini coefficient for code inequality analysis
-- Shows directories with uneven code distribution (higher Gini = more inequality)
-- Classification: critical >= 0.7, warning >= 0.5, healthy < 0.5

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
scc_gini AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        gini_value,
        value_count AS file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric IN ('lines_total', 'complexity')
      AND gini_value >= 0.3
      AND value_count >= 3  -- Need at least 3 files for meaningful Gini
),
lizard_gini AS (
    SELECT
        run_pk,
        directory_path,
        metric,
        gini_value,
        value_count AS file_count,
        avg_value,
        max_value,
        top_10_pct_share,
        top_20_pct_share
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric IN ('total_ccn', 'nloc')
      AND gini_value >= 0.3
      AND value_count >= 3
),
combined AS (
    SELECT * FROM scc_gini
    UNION ALL
    SELECT * FROM lizard_gini
)
SELECT
    directory_path,
    metric,
    ROUND(gini_value, 3) AS gini,
    CASE
        WHEN gini_value >= 0.7 THEN 'critical'
        WHEN gini_value >= 0.5 THEN 'warning'
        ELSE 'healthy'
    END AS classification,
    file_count,
    ROUND(avg_value, 1) AS avg_value,
    ROUND(max_value, 1) AS max_value,
    ROUND(top_10_pct_share * 100, 1) AS top_10_pct,
    ROUND(top_20_pct_share * 100, 1) AS top_20_pct
FROM combined
ORDER BY gini_value DESC, directory_path
LIMIT 50
