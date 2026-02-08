-- Composite risk hotspots query
-- Uses mart_composite_file_hotspots to identify multi-dimensional risk files
-- Resolves collection_run_id from the SCC run_pk

WITH run_info AS (
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
)
SELECT
    file_id,
    relative_path,
    composite_score,
    composite_risk_level,
    risk_pattern,
    medium_plus_risk_count,
    high_plus_risk_count,
    critical_risk_count,
    available_dimensions,
    max_ccn,
    complexity_risk,
    complexity_score,
    loc_code,
    size_risk,
    size_score,
    total_high_plus_issues,
    semgrep_high_plus,
    sonarqube_high_plus,
    roslyn_high_plus,
    devskim_high_plus,
    issues_risk,
    issues_score,
    coverage_statement_pct,
    coverage_risk,
    coverage_score,
    total_coupling,
    coupling_risk,
    coupling_score,
    has_complexity_data,
    has_size_data,
    has_issues_data,
    has_coverage_data,
    has_coupling_data
FROM mart_composite_file_hotspots
WHERE collection_run_id = (SELECT collection_run_id FROM run_info)
ORDER BY composite_score DESC
LIMIT {{ limit | default(25) }}
