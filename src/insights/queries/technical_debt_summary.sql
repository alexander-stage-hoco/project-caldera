-- Technical debt summary - aggregates all debt indicators
-- Categories: complexity, duplication, smells, coverage_gaps, size

WITH run_info AS (
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
),
file_debt AS (
    SELECT
        file_id,
        relative_path,
        loc_code,
        -- Complexity debt
        complexity_max,
        CASE
            WHEN complexity_max >= 50 THEN 'critical'
            WHEN complexity_max >= 20 THEN 'high'
            WHEN complexity_max >= 10 THEN 'medium'
            ELSE 'low'
        END AS complexity_risk,
        -- Duplication debt
        COALESCE(pmd_cpd_duplicate_lines, 0) AS duplicate_lines,
        COALESCE(pmd_cpd_duplication_percentage, 0) AS duplication_pct,
        CASE
            WHEN pmd_cpd_duplicate_lines >= 100 THEN 'critical'
            WHEN pmd_cpd_duplicate_lines >= 50 THEN 'high'
            WHEN pmd_cpd_duplicate_lines >= 20 THEN 'medium'
            ELSE 'low'
        END AS duplication_risk,
        -- Code smells debt (aggregate high+ issues)
        COALESCE(semgrep_severity_high_plus, 0) +
        COALESCE(roslyn_severity_high_plus, 0) +
        COALESCE(devskim_severity_high_plus, 0) AS high_plus_issues,
        COALESCE(sonarqube_type_code_smell, 0) AS sonarqube_smells,
        -- Coverage gaps
        coverage_statement_pct,
        CASE
            WHEN coverage_statement_pct IS NULL THEN 'unknown'
            WHEN coverage_statement_pct < 40 AND complexity_max >= 10 THEN 'critical'
            WHEN coverage_statement_pct < 60 AND complexity_max >= 10 THEN 'high'
            WHEN coverage_statement_pct < 80 THEN 'medium'
            ELSE 'low'
        END AS coverage_risk,
        -- Size debt
        CASE
            WHEN loc_code >= 1000 THEN 'critical'
            WHEN loc_code >= 500 THEN 'high'
            WHEN loc_code >= 200 THEN 'medium'
            ELSE 'low'
        END AS size_risk
    FROM unified_file_metrics
    WHERE collection_run_id = (SELECT collection_run_id FROM run_info)
)
SELECT
    -- Category summaries
    COUNT(*) AS total_files,
    SUM(loc_code) AS total_loc,

    -- Complexity debt
    COUNT(CASE WHEN complexity_risk = 'critical' THEN 1 END) AS complexity_critical,
    COUNT(CASE WHEN complexity_risk = 'high' THEN 1 END) AS complexity_high,
    COUNT(CASE WHEN complexity_risk = 'medium' THEN 1 END) AS complexity_medium,
    COUNT(CASE WHEN complexity_max IS NOT NULL THEN 1 END) AS complexity_analyzed,

    -- Duplication debt
    SUM(duplicate_lines) AS total_duplicate_lines,
    COUNT(CASE WHEN duplication_risk = 'critical' THEN 1 END) AS duplication_critical,
    COUNT(CASE WHEN duplication_risk = 'high' THEN 1 END) AS duplication_high,
    COUNT(CASE WHEN duplication_risk = 'medium' THEN 1 END) AS duplication_medium,
    COUNT(CASE WHEN duplicate_lines > 0 THEN 1 END) AS files_with_duplication,

    -- Code smells debt
    SUM(high_plus_issues) AS total_high_plus_issues,
    SUM(sonarqube_smells) AS total_sonarqube_smells,
    COUNT(CASE WHEN high_plus_issues > 0 THEN 1 END) AS files_with_issues,

    -- Coverage gaps
    COUNT(CASE WHEN coverage_risk = 'critical' THEN 1 END) AS coverage_critical,
    COUNT(CASE WHEN coverage_risk = 'high' THEN 1 END) AS coverage_high,
    COUNT(CASE WHEN coverage_risk = 'medium' THEN 1 END) AS coverage_medium,
    COUNT(CASE WHEN coverage_statement_pct IS NOT NULL THEN 1 END) AS coverage_analyzed,
    ROUND(AVG(coverage_statement_pct), 1) AS avg_coverage,

    -- Size debt
    COUNT(CASE WHEN size_risk = 'critical' THEN 1 END) AS size_critical,
    COUNT(CASE WHEN size_risk = 'high' THEN 1 END) AS size_high,
    COUNT(CASE WHEN size_risk = 'medium' THEN 1 END) AS size_medium
FROM file_debt
