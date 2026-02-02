-- Summary of gitleaks secrets by severity
SELECT
    severity,
    COUNT(*) AS count,
    COUNT(DISTINCT fingerprint) AS unique_count,
    SUM(CASE WHEN in_current_head THEN 1 ELSE 0 END) AS in_head_count
FROM stg_lz_gitleaks_secrets
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
