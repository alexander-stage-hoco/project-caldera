-- Aggregate health statistics summary
-- Overall distribution of health scores and grades

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
health_scores AS (
    SELECT
        directory_path,
        metric,
        -- Calculate health score
        100 * (
            0.25 * GREATEST(0, 1 - gini_value) +
            0.15 * GREATEST(0, 1 - LEAST(cv_value, 2) / 2) +
            0.15 * GREATEST(0, 1 - LEAST(ABS(skewness_value), 3) / 3) +
            0.25 * GREATEST(0, 1 - top_10_pct_share) +
            0.20 * GREATEST(0, 1 - LEAST(CASE WHEN avg_value > 0 THEN p99_value / avg_value ELSE 0 END, 20) / 20)
        ) AS health_score
    FROM combined
),
graded AS (
    SELECT
        directory_path,
        metric,
        health_score,
        CASE
            WHEN health_score >= 90 THEN 'A'
            WHEN health_score >= 80 THEN 'B'
            WHEN health_score >= 70 THEN 'C'
            WHEN health_score >= 60 THEN 'D'
            ELSE 'F'
        END AS grade
    FROM health_scores
)
SELECT
    COUNT(*) AS total_directories,
    COUNT(DISTINCT directory_path) AS unique_directories,
    ROUND(AVG(health_score), 1) AS avg_health_score,
    ROUND(MIN(health_score), 1) AS min_health_score,
    ROUND(MAX(health_score), 1) AS max_health_score,
    ROUND(STDDEV(health_score), 1) AS stddev_health_score,
    COUNT(CASE WHEN grade = 'A' THEN 1 END) AS grade_a_count,
    COUNT(CASE WHEN grade = 'B' THEN 1 END) AS grade_b_count,
    COUNT(CASE WHEN grade = 'C' THEN 1 END) AS grade_c_count,
    COUNT(CASE WHEN grade = 'D' THEN 1 END) AS grade_d_count,
    COUNT(CASE WHEN grade = 'F' THEN 1 END) AS grade_f_count,
    ROUND(100.0 * COUNT(CASE WHEN grade = 'A' THEN 1 END) / COUNT(*), 1) AS pct_grade_a,
    ROUND(100.0 * COUNT(CASE WHEN grade IN ('A', 'B') THEN 1 END) / COUNT(*), 1) AS pct_passing,
    ROUND(100.0 * COUNT(CASE WHEN grade = 'F' THEN 1 END) / COUNT(*), 1) AS pct_failing
FROM graded
