-- Top IaC misconfigurations by severity for Caldera
-- Uses stg_trivy_iac_misconfigs

SELECT
    misconfig_id,
    severity,
    title,
    type AS iac_type,
    target_key AS file_path
FROM stg_trivy_iac_misconfigs
WHERE run_pk = {{ run_pk }}
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END,
    misconfig_id
LIMIT {{ limit | default(20) }}
