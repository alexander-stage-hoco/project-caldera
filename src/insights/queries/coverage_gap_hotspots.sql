-- Coverage gap hotspots - files with high complexity but low coverage
-- These represent the highest-risk untested code paths

WITH run_info AS (
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
)
SELECT
    file_id,
    relative_path,
    complexity_max,
    complexity_total_ccn,
    complexity_avg,
    coverage_statement_pct,
    coverage_covered_statements,
    coverage_total_statements,
    loc_code,
    -- Gap calculation: how far from 80% target
    80.0 - coverage_statement_pct AS gap_to_target,
    -- Statements needed to reach 80%
    ROUND((0.80 * coverage_total_statements) - coverage_covered_statements) AS statements_needed,
    -- Risk score: complexity * coverage gap (higher = worse)
    ROUND(complexity_total_ccn * (100 - coverage_statement_pct) / 100.0, 1) AS risk_score,
    -- Risk level classification
    CASE
        WHEN complexity_max >= 30 AND coverage_statement_pct < 40 THEN 'critical'
        WHEN complexity_max >= 20 AND coverage_statement_pct < 60 THEN 'high'
        WHEN complexity_max >= 10 AND coverage_statement_pct < 80 THEN 'medium'
        ELSE 'low'
    END AS gap_risk_level
FROM unified_file_metrics
WHERE collection_run_id = (SELECT collection_run_id FROM run_info)
  AND complexity_max IS NOT NULL
  AND coverage_statement_pct IS NOT NULL
  AND coverage_statement_pct < 80.0
  AND complexity_max >= 5
ORDER BY risk_score DESC
LIMIT {{ limit | default(30) }}
