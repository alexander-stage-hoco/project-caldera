-- Gitleaks secret hotspots: identify most impactful secret types for remediation prioritization
-- Focus on secrets still in HEAD (urgent) vs historical-only (less urgent)

with secret_metrics as (
    select
        run_pk,
        rule_id,
        -- Representative info
        max(secret_type) as secret_type,
        max(description) as description,
        count(*) as detection_count,
        count(distinct file_id) as files_affected,
        count(distinct commit_author) as authors_affected,
        -- Current HEAD vs historical
        count(*) filter (where in_current_head = true) as in_head_count,
        count(*) filter (where in_current_head = false or in_current_head is null) as historical_count,
        round(100.0 * count(*) filter (where in_current_head = true) / nullif(count(*), 0), 1) as in_head_pct,
        -- Severity breakdown
        count(*) filter (where severity = 'CRITICAL') as severity_critical,
        count(*) filter (where severity = 'HIGH') as severity_high,
        count(*) filter (where severity = 'MEDIUM') as severity_medium,
        count(*) filter (where severity = 'LOW') as severity_low,
        count(*) filter (where severity in ('CRITICAL', 'HIGH')) as severity_high_plus,
        -- Entropy metrics (higher = more likely real secret)
        min(entropy) as min_entropy,
        max(entropy) as max_entropy,
        round(avg(entropy), 2) as avg_entropy,
        count(*) filter (where entropy > 4.0) as high_entropy_count,
        -- Risk score: in_head secrets weighted by severity
        (count(*) filter (where in_current_head = true) *
         case max(severity)
            when 'CRITICAL' then 4
            when 'HIGH' then 3
            when 'MEDIUM' then 2
            else 1
         end) as risk_score
    from {{ ref('stg_lz_gitleaks_secrets') }}
    group by run_pk, rule_id
),
ranked_secrets as (
    select
        *,
        row_number() over (partition by run_pk order by detection_count desc) as detection_rank,
        row_number() over (partition by run_pk order by in_head_count desc, detection_count desc) as urgency_rank,
        row_number() over (partition by run_pk order by risk_score desc) as risk_rank,
        -- Risk level based on in_head presence and severity
        case
            when in_head_count > 0 and severity_critical > 0 then 'critical'
            when in_head_count > 0 and severity_high > 0 then 'high'
            when in_head_count > 0 then 'medium'
            else 'low'
        end as risk_level
    from secret_metrics
)
select
    run_pk,
    rule_id,
    secret_type,
    description,
    detection_count,
    files_affected,
    authors_affected,
    in_head_count,
    historical_count,
    in_head_pct,
    severity_critical,
    severity_high,
    severity_medium,
    severity_low,
    severity_high_plus,
    min_entropy,
    max_entropy,
    avg_entropy,
    high_entropy_count,
    risk_score,
    detection_rank,
    urgency_rank,
    risk_rank,
    risk_level
from ranked_secrets
order by run_pk, risk_score desc
