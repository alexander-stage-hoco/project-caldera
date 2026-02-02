-- IaC misconfigurations by type for Caldera
-- Groups by IaC type (terraform, kubernetes, dockerfile, etc.)

SELECT
    type AS iac_type,
    COUNT(*) AS count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) AS high_count
FROM stg_trivy_iac_misconfigs
WHERE run_pk = {{ run_pk }}
GROUP BY type
ORDER BY count DESC
