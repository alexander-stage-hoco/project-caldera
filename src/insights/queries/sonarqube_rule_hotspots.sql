-- SonarQube rules with most violations
-- Uses mart_sonarqube_rule_hotspots to show rule-level aggregates
-- Resolves sonarqube run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_sq.run_pk AS sonarqube_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_sq
        ON tr_sq.collection_run_id = tr_scc.collection_run_id
        AND tr_sq.tool_name = 'sonarqube'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    rule_id,
    issue_type,
    issue_count,
    files_affected,
    severity_blocker,
    severity_critical,
    severity_major,
    severity_minor,
    severity_info,
    severity_high_plus,
    total_effort_minutes,
    avg_effort_minutes,
    open_count,
    impact_score,
    occurrence_rank,
    effort_rank,
    impact_rank,
    risk_level
FROM mart_sonarqube_rule_hotspots
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)
ORDER BY impact_score DESC, issue_count DESC
LIMIT {{ limit | default(30) }}
