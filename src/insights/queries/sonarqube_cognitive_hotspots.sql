-- SonarQube files with highest cognitive complexity
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
    cognitive_complexity,
    complexity AS cyclomatic_complexity,
    ncloc,
    issue_count,
    type_code_smell,
    CASE
        WHEN cognitive_complexity >= 50 THEN 'critical'
        WHEN cognitive_complexity >= 25 THEN 'high'
        WHEN cognitive_complexity >= 15 THEN 'medium'
        ELSE 'low'
    END AS complexity_level
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)
  AND cognitive_complexity > 0
ORDER BY cognitive_complexity DESC
LIMIT {{ limit | default(25) }}
