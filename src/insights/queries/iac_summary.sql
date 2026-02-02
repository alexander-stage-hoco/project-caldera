-- IaC misconfiguration summary by severity for Caldera
-- Uses stg_trivy_iac_misconfigs

SELECT
    severity,
    COUNT(*) AS count,
    COUNT(DISTINCT target_key) AS affected_files
FROM stg_trivy_iac_misconfigs
WHERE run_pk = {{ run_pk }}
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END
