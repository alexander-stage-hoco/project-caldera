-- Secrets grouped by rule/type
SELECT
    rule_id,
    secret_type,
    COUNT(*) AS count,
    COUNT(DISTINCT relative_path) AS file_count,
    MAX(severity) AS max_severity
FROM stg_lz_gitleaks_secrets
WHERE run_pk = {{ run_pk }}
GROUP BY rule_id, secret_type
ORDER BY count DESC
LIMIT {{ limit | default(15) }}
