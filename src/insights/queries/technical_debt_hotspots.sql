-- Top technical debt files with multi-dimensional scoring

WITH run_info AS (
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
)
SELECT
    file_id,
    relative_path,
    loc_code,
    complexity_max,
    COALESCE(pmd_cpd_duplicate_lines, 0) AS duplicate_lines,
    COALESCE(semgrep_severity_high_plus, 0) + COALESCE(roslyn_severity_high_plus, 0) AS high_plus_issues,
    coverage_statement_pct,
    -- Debt score: weighted sum of normalized indicators
    ROUND(
        COALESCE(complexity_max, 0) * 0.30 +
        COALESCE(pmd_cpd_duplicate_lines, 0) * 0.20 +
        (COALESCE(semgrep_severity_high_plus, 0) + COALESCE(roslyn_severity_high_plus, 0)) * 10 * 0.25 +
        CASE WHEN coverage_statement_pct IS NOT NULL THEN (100 - coverage_statement_pct) * 0.15 ELSE 0 END +
        loc_code / 100.0 * 0.10
    , 1) AS debt_score,
    -- Primary debt type
    CASE
        WHEN complexity_max >= 20 THEN 'complexity'
        WHEN pmd_cpd_duplicate_lines >= 50 THEN 'duplication'
        WHEN (COALESCE(semgrep_severity_high_plus, 0) + COALESCE(roslyn_severity_high_plus, 0)) >= 3 THEN 'code_smells'
        WHEN coverage_statement_pct < 60 AND complexity_max >= 10 THEN 'coverage_gap'
        WHEN loc_code >= 500 THEN 'size'
        ELSE 'mixed'
    END AS primary_debt_type
FROM unified_file_metrics
WHERE collection_run_id = (SELECT collection_run_id FROM run_info)
  AND (
    complexity_max >= 10 OR
    pmd_cpd_duplicate_lines >= 20 OR
    (COALESCE(semgrep_severity_high_plus, 0) + COALESCE(roslyn_severity_high_plus, 0)) >= 1 OR
    (coverage_statement_pct < 80 AND complexity_max >= 5) OR
    loc_code >= 200
  )
ORDER BY debt_score DESC
LIMIT {{ limit | default(25) }}
