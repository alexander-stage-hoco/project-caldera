-- Staging model for gitleaks secrets
-- Provides file-level aggregation of secret findings

with secrets as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        rule_id,
        secret_type,
        severity,
        line_number,
        commit_hash,
        in_current_head,
        entropy,
        fingerprint
    from {{ ref('stg_lz_gitleaks_secrets') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as secret_count,
        -- Severity counts
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'HIGH' then 1 end) as severity_high,
        count(case when severity = 'MEDIUM' then 1 end) as severity_medium,
        count(case when severity = 'LOW' then 1 end) as severity_low,
        -- Combined high+ for distribution analysis
        count(case when severity in ('CRITICAL', 'HIGH') then 1 end) as severity_high_plus,
        -- Location breakdown
        count(case when in_current_head = true then 1 end) as secrets_in_head,
        count(case when in_current_head = false then 1 end) as secrets_in_history,
        -- Unique metrics
        count(distinct rule_id) as unique_rule_count,
        count(distinct fingerprint) as unique_secret_count,
        count(distinct commit_hash) as commit_count,
        -- Entropy stats
        avg(entropy) as avg_entropy,
        max(entropy) as max_entropy
    from secrets
    group by run_pk, file_id, directory_id
)
select * from file_metrics
