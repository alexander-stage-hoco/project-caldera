-- SonarQube issues breakdown by type
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
    'BUG' AS issue_type,
    COALESCE(SUM(type_bug), 0) AS issue_count,
    COUNT(CASE WHEN type_bug > 0 THEN 1 END) AS files_affected,
    COALESCE(SUM(CASE WHEN type_bug > 0 THEN severity_blocker END), 0) AS blocker_count,
    COALESCE(SUM(CASE WHEN type_bug > 0 THEN severity_critical END), 0) AS critical_count
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)

UNION ALL

SELECT
    'VULNERABILITY' AS issue_type,
    COALESCE(SUM(type_vulnerability), 0) AS issue_count,
    COUNT(CASE WHEN type_vulnerability > 0 THEN 1 END) AS files_affected,
    COALESCE(SUM(CASE WHEN type_vulnerability > 0 THEN severity_blocker END), 0) AS blocker_count,
    COALESCE(SUM(CASE WHEN type_vulnerability > 0 THEN severity_critical END), 0) AS critical_count
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)

UNION ALL

SELECT
    'CODE_SMELL' AS issue_type,
    COALESCE(SUM(type_code_smell), 0) AS issue_count,
    COUNT(CASE WHEN type_code_smell > 0 THEN 1 END) AS files_affected,
    COALESCE(SUM(CASE WHEN type_code_smell > 0 THEN severity_blocker END), 0) AS blocker_count,
    COALESCE(SUM(CASE WHEN type_code_smell > 0 THEN severity_critical END), 0) AS critical_count
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)

UNION ALL

SELECT
    'SECURITY_HOTSPOT' AS issue_type,
    COALESCE(SUM(type_security_hotspot), 0) AS issue_count,
    COUNT(CASE WHEN type_security_hotspot > 0 THEN 1 END) AS files_affected,
    COALESCE(SUM(CASE WHEN type_security_hotspot > 0 THEN severity_blocker END), 0) AS blocker_count,
    COALESCE(SUM(CASE WHEN type_security_hotspot > 0 THEN severity_critical END), 0) AS critical_count
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)

ORDER BY issue_count DESC
