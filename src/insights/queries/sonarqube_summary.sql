-- SonarQube aggregate statistics
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
    COUNT(*) AS total_files,
    COALESCE(SUM(issue_count), 0) AS total_issues,
    COALESCE(SUM(type_bug), 0) AS total_bugs,
    COALESCE(SUM(type_vulnerability), 0) AS total_vulnerabilities,
    COALESCE(SUM(type_code_smell), 0) AS total_code_smells,
    COALESCE(SUM(type_security_hotspot), 0) AS total_security_hotspots,
    COALESCE(SUM(severity_blocker), 0) AS total_blocker,
    COALESCE(SUM(severity_critical), 0) AS total_critical,
    COALESCE(SUM(severity_major), 0) AS total_major,
    COALESCE(SUM(severity_minor), 0) AS total_minor,
    COALESCE(SUM(severity_info), 0) AS total_info,
    COALESCE(SUM(cognitive_complexity), 0) AS total_cognitive_complexity,
    ROUND(AVG(cognitive_complexity), 1) AS avg_cognitive_complexity,
    MAX(cognitive_complexity) AS max_cognitive_complexity,
    ROUND(AVG(complexity), 1) AS avg_cyclomatic_complexity,
    COUNT(CASE WHEN cognitive_complexity >= 25 THEN 1 END) AS files_high_cognitive,
    COUNT(CASE WHEN cognitive_complexity >= 50 THEN 1 END) AS files_critical_cognitive,
    COUNT(CASE WHEN cognitive_complexity >= 15 THEN 1 END) AS files_medium_cognitive,
    COALESCE(SUM(duplicated_lines), 0) AS total_duplicated_lines,
    COALESCE(SUM(ncloc), 0) AS total_ncloc
FROM stg_sonarqube_file_metrics
WHERE run_pk = (SELECT sonarqube_run_pk FROM run_map)
