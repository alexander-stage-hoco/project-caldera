-- Files with IaC misconfigurations for Caldera
-- Groups by target file

SELECT
    target_key AS file_path,
    type AS iac_type,
    COUNT(*) AS misconfig_count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_count
FROM stg_trivy_iac_misconfigs
WHERE run_pk = {{ run_pk }}
GROUP BY target_key, type
ORDER BY critical_count DESC, high_count DESC, misconfig_count DESC
LIMIT {{ limit | default(15) }}
