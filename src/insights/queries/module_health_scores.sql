-- Module health scores per directory
-- Composite score (0-100) combining multiple distribution metrics
-- Formula:
--   Score = 100 * (
--       0.25 * (1 - gini) +           -- Inequality weight
--       0.15 * (1 - cv/2) +           -- Variability weight (CV capped at 2)
--       0.15 * (1 - |skewness|/3) +   -- Distribution shape weight (skewness capped at 3)
--       0.25 * (1 - top_10_share) +   -- Concentration weight
--       0.20 * (1 - p99_ratio/20)     -- Outlier weight (p99/avg ratio capped at 20)
--   )
-- Grades: A>=90, B>=80, C>=70, D>=60, F<60

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
        metric,
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
        metric,
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
scored AS (
    SELECT
        directory_path,
        metric,
        file_count,
        gini_value,
        cv_value,
        skewness_value,
        top_10_pct_share,
        avg_value,
        p99_value,
        CASE WHEN avg_value > 0 THEN p99_value / avg_value ELSE 0 END AS p99_ratio,
        -- Component scores (0-1 each, higher = healthier)
        GREATEST(0, 1 - gini_value) AS inequality_score,
        GREATEST(0, 1 - LEAST(cv_value, 2) / 2) AS variability_score,
        GREATEST(0, 1 - LEAST(ABS(skewness_value), 3) / 3) AS shape_score,
        GREATEST(0, 1 - top_10_pct_share) AS concentration_score,
        GREATEST(0, 1 - LEAST(CASE WHEN avg_value > 0 THEN p99_value / avg_value ELSE 0 END, 20) / 20) AS outlier_score
    FROM combined
),
health_scores AS (
    SELECT
        directory_path,
        metric,
        file_count,
        ROUND(gini_value, 3) AS gini,
        ROUND(cv_value, 3) AS cv,
        ROUND(skewness_value, 3) AS skewness,
        ROUND(top_10_pct_share * 100, 1) AS top_10_pct,
        ROUND(p99_ratio, 1) AS p99_ratio,
        -- Weighted health score (0-100)
        ROUND(100 * (
            0.25 * inequality_score +
            0.15 * variability_score +
            0.15 * shape_score +
            0.25 * concentration_score +
            0.20 * outlier_score
        ), 1) AS health_score,
        -- Component scores for transparency
        ROUND(inequality_score * 100, 1) AS inequality_component,
        ROUND(variability_score * 100, 1) AS variability_component,
        ROUND(shape_score * 100, 1) AS shape_component,
        ROUND(concentration_score * 100, 1) AS concentration_component,
        ROUND(outlier_score * 100, 1) AS outlier_component
    FROM scored
)
SELECT
    directory_path,
    metric,
    file_count,
    health_score,
    CASE
        WHEN health_score >= 90 THEN 'A'
        WHEN health_score >= 80 THEN 'B'
        WHEN health_score >= 70 THEN 'C'
        WHEN health_score >= 60 THEN 'D'
        ELSE 'F'
    END AS grade,
    gini,
    cv,
    skewness,
    top_10_pct,
    p99_ratio,
    inequality_component,
    variability_component,
    shape_component,
    concentration_component,
    outlier_component
FROM health_scores
ORDER BY health_score DESC, directory_path
