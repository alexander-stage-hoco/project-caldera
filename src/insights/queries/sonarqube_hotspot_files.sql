-- SonarQube files with most issues
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
    relative_path,
    issue_count,
    type_bug,
    type_vulnerability,
    type_code_smell,
    type_security_hotspot,
    severity_blocker,
    severity_critical,
    severity_major,
    cognitive_complexity,
    complexity AS cyclomatic_complexity,
    ncloc,
    duplicated_lines,
    -- Composite score for ranking
    (severity_blocker * 10 + severity_critical * 5 + severity_major * 2 + type_bug * 5 + type_vulnerability * 4) AS risk_score
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)
  AND issue_count > 0
ORDER BY risk_score DESC, issue_count DESC
LIMIT {{ limit | default(25) }}
