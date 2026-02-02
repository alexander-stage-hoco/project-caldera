-- Risk factor breakdown per directory
-- Identifies which specific metrics are causing low health scores

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
scc_metrics AS (
    SELECT
        directory_path,
        'lines_total' AS metric,
        gini_value,
        cv_value,
        skewness_value,
        top_10_pct_share,
        avg_value,
        p99_value,
        value_count AS file_count
    FROM rollup_scc_directory_recursive_distributions
    WHERE run_pk = (SELECT scc_run_pk FROM run_map)
      AND metric = 'lines_total'
      AND value_count >= 3
),
lizard_metrics AS (
    SELECT
        directory_path,
        'total_ccn' AS metric,
        gini_value,
        cv_value,
        skewness_value,
        top_10_pct_share,
        avg_value,
        p99_value,
        value_count AS file_count
    FROM rollup_lizard_directory_recursive_distributions
    WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
      AND metric = 'total_ccn'
      AND value_count >= 3
),
combined AS (
    SELECT * FROM scc_metrics
    UNION ALL
    SELECT * FROM lizard_metrics
),
risk_analysis AS (
    SELECT
        directory_path,
        metric,
        file_count,
        -- Risk flags (true if metric exceeds threshold)
        CASE WHEN gini_value >= 0.5 THEN 1 ELSE 0 END AS high_inequality,
        CASE WHEN cv_value >= 1.5 THEN 1 ELSE 0 END AS high_variability,
        CASE WHEN ABS(skewness_value) >= 2.0 THEN 1 ELSE 0 END AS skewed_distribution,
        CASE WHEN top_10_pct_share >= 0.5 THEN 1 ELSE 0 END AS concentrated_top_10,
        CASE WHEN avg_value > 0 AND p99_value / avg_value >= 10 THEN 1 ELSE 0 END AS extreme_outliers,
        -- Metric values for display
        ROUND(gini_value, 3) AS gini,
        ROUND(cv_value, 3) AS cv,
        ROUND(skewness_value, 3) AS skewness,
        ROUND(top_10_pct_share * 100, 1) AS top_10_pct,
        ROUND(CASE WHEN avg_value > 0 THEN p99_value / avg_value ELSE 0 END, 1) AS p99_ratio
    FROM combined
),
with_risk_count AS (
    SELECT
        *,
        high_inequality + high_variability + skewed_distribution +
        concentrated_top_10 + extreme_outliers AS risk_factor_count
    FROM risk_analysis
)
SELECT
    directory_path,
    metric,
    file_count,
    risk_factor_count,
    -- Individual risk flags
    high_inequality,
    high_variability,
    skewed_distribution,
    concentrated_top_10,
    extreme_outliers,
    -- Metric values
    gini,
    cv,
    skewness,
    top_10_pct,
    p99_ratio,
    -- Human-readable risk factors list
    CASE
        WHEN risk_factor_count = 0 THEN 'None'
        ELSE CONCAT_WS(', ',
            CASE WHEN high_inequality = 1 THEN 'High inequality (Gini>0.5)' END,
            CASE WHEN high_variability = 1 THEN 'High variability (CV>1.5)' END,
            CASE WHEN skewed_distribution = 1 THEN 'Skewed distribution' END,
            CASE WHEN concentrated_top_10 = 1 THEN 'Top 10% concentration' END,
            CASE WHEN extreme_outliers = 1 THEN 'Extreme outliers (P99/avg>10)' END
        )
    END AS risk_factors_list
FROM with_risk_count
WHERE risk_factor_count >= 2  -- Show directories with 2+ risk factors
ORDER BY risk_factor_count DESC, directory_path
LIMIT 30
