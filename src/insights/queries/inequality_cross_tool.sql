-- Cross-tool inequality correlation: LOC Gini vs CCN Gini
-- Identifies directories with mismatched inequality patterns
-- High LOC inequality + low CCN inequality = few large but simple files
-- Low LOC inequality + high CCN inequality = evenly sized but complexity hotspots

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
scc_loc AS (
    SELECT
        directory_path,
        gini_value AS loc_gini,
        top_20_pct_share AS loc_top_20,
        value_count AS loc_file_count,
        avg_value AS loc_avg
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric = 'lines_total'
      AND value_count >= 5
),
lizard_ccn AS (
    SELECT
        directory_path,
        gini_value AS ccn_gini,
        top_20_pct_share AS ccn_top_20,
        value_count AS ccn_file_count,
        avg_value AS ccn_avg
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric = 'total_ccn'
      AND value_count >= 5
),
correlated AS (
    SELECT
        COALESCE(l.directory_path, c.directory_path) AS directory_path,
        l.loc_gini,
        c.ccn_gini,
        l.loc_top_20,
        c.ccn_top_20,
        l.loc_file_count,
        c.ccn_file_count,
        l.loc_avg,
        c.ccn_avg,
        ABS(COALESCE(l.loc_gini, 0) - COALESCE(c.ccn_gini, 0)) AS gini_diff
    FROM scc_loc l
    FULL OUTER JOIN lizard_ccn c
        ON l.directory_path = c.directory_path
    WHERE l.directory_path IS NOT NULL
      AND c.directory_path IS NOT NULL
)
SELECT
    directory_path,
    ROUND(loc_gini, 3) AS loc_gini,
    ROUND(ccn_gini, 3) AS ccn_gini,
    ROUND(gini_diff, 3) AS gini_difference,
    ROUND(loc_top_20 * 100, 1) AS loc_top_20_pct,
    ROUND(ccn_top_20 * 100, 1) AS ccn_top_20_pct,
    loc_file_count,
    ROUND(loc_avg, 1) AS avg_loc,
    ROUND(ccn_avg, 1) AS avg_ccn,
    CASE
        WHEN loc_gini >= 0.5 AND ccn_gini < 0.3 THEN 'size_concentrated'
        WHEN loc_gini < 0.3 AND ccn_gini >= 0.5 THEN 'complexity_concentrated'
        WHEN loc_gini >= 0.5 AND ccn_gini >= 0.5 THEN 'both_concentrated'
        ELSE 'balanced'
    END AS pattern
FROM correlated
WHERE gini_diff > 0.1  -- Only show directories with notable divergence
   OR (loc_gini >= 0.5 OR ccn_gini >= 0.5)  -- Or high inequality in either
ORDER BY
    CASE
        WHEN loc_gini >= 0.5 AND ccn_gini >= 0.5 THEN 0  -- Both concentrated first
        ELSE 1
    END,
    gini_diff DESC,
    directory_path
LIMIT 30
