-- Coupling-weighted technical debt hotspots
-- Combines debt score with coupling impact to identify high-blast-radius debt

WITH run_info AS (
    SELECT collection_run_id
    FROM lz_tool_runs
    WHERE run_pk = {{ run_pk }}
),
run_stats AS (
    SELECT
        AVG(coupling_fan_in) AS avg_fan_in,
        STDDEV(coupling_fan_in) AS stddev_fan_in,
        PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY coupling_fan_in) AS p90_fan_in
    FROM unified_file_metrics
    WHERE collection_run_id = (SELECT collection_run_id FROM run_info)
      AND coupling_fan_in IS NOT NULL
),
debt_with_coupling AS (
    SELECT
        f.relative_path,
        f.loc_code,
        f.complexity_max,
        f.semgrep_severity_high_plus,
        f.roslyn_severity_high_plus,
        f.pmd_cpd_duplicate_lines,
        f.coupling_fan_in,
        f.coupling_fan_out,
        f.coupling_avg_instability,
        -- Base debt score (same formula as technical_debt_hotspots)
        ROUND(
            COALESCE(f.complexity_max, 0) * 0.30 +
            COALESCE(f.pmd_cpd_duplicate_lines, 0) * 0.20 +
            (COALESCE(f.semgrep_severity_high_plus, 0) + COALESCE(f.roslyn_severity_high_plus, 0)) * 10 * 0.25 +
            COALESCE(f.loc_code, 0) / 100.0 * 0.10
        , 2) AS debt_score,
        -- Coupling impact factor (normalized by run average)
        CASE
            WHEN rs.avg_fan_in > 0 THEN COALESCE(f.coupling_fan_in, 0) / rs.avg_fan_in
            ELSE 1.0
        END AS coupling_factor,
        rs.avg_fan_in AS run_avg_fan_in,
        rs.p90_fan_in AS run_p90_fan_in
    FROM unified_file_metrics f
    CROSS JOIN run_stats rs
    WHERE f.collection_run_id = (SELECT collection_run_id FROM run_info)
)
SELECT
    relative_path,
    loc_code,
    complexity_max,
    COALESCE(semgrep_severity_high_plus, 0) + COALESCE(roslyn_severity_high_plus, 0) AS high_plus_issues,
    COALESCE(pmd_cpd_duplicate_lines, 0) AS duplicate_lines,
    COALESCE(coupling_fan_in, 0) AS coupling_fan_in,
    COALESCE(coupling_fan_out, 0) AS coupling_fan_out,
    coupling_avg_instability,
    debt_score,
    ROUND(coupling_factor, 2) AS coupling_factor,
    -- Debt impact score: debt weighted by coupling factor
    ROUND(debt_score * (1 + coupling_factor * 0.5), 2) AS debt_impact_score,
    -- Quadrant classification based on debt and coupling thresholds
    CASE
        WHEN debt_score >= 20 AND COALESCE(coupling_fan_in, 0) >= 10 THEN 'critical-coupled'
        WHEN debt_score >= 20 AND COALESCE(coupling_fan_in, 0) < 10 THEN 'high-isolated'
        WHEN debt_score >= 10 AND COALESCE(coupling_fan_in, 0) >= 5 THEN 'medium-coupled'
        WHEN debt_score >= 10 THEN 'medium-isolated'
        ELSE 'low'
    END AS debt_quadrant,
    run_avg_fan_in,
    run_p90_fan_in
FROM debt_with_coupling
WHERE debt_score > 0
ORDER BY debt_impact_score DESC
LIMIT {{ limit | default(30) }}
