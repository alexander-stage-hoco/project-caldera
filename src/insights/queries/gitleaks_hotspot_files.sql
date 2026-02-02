-- Files with most secret findings
SELECT
    relative_path,
    secret_count,
    severity_critical,
    severity_high,
    secrets_in_head,
    unique_rule_count
FROM stg_gitleaks_secrets
WHERE run_pk = {{ run_pk }}
ORDER BY severity_critical DESC, severity_high DESC, secret_count DESC
LIMIT {{ limit | default(10) }}
