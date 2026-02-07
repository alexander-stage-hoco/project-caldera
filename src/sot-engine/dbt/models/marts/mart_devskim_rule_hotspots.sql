-- DevSkim rule hotspots: identify most impactful security rules for remediation prioritization
-- Severity levels: CRITICAL > HIGH > MEDIUM > LOW

with rule_metrics as (
    select
        run_pk,
        rule_id,
        -- Representative info
        max(dd_category) as dd_category,
        max(message) as sample_message,
        count(*) as issue_count,
        count(distinct file_id) as files_affected,
        count(distinct directory_id) as directories_affected,
        -- Severity breakdown
        count(*) filter (where upper(severity) = 'CRITICAL') as severity_critical,
        count(*) filter (where upper(severity) = 'HIGH') as severity_high,
        count(*) filter (where upper(severity) = 'MEDIUM') as severity_medium,
        count(*) filter (where upper(severity) = 'LOW') as severity_low,
        count(*) filter (where upper(severity) in ('CRITICAL', 'HIGH')) as severity_high_plus,
        -- Weighted severity score for ranking
        (count(*) filter (where upper(severity) = 'CRITICAL') * 4 +
         count(*) filter (where upper(severity) = 'HIGH') * 3 +
         count(*) filter (where upper(severity) = 'MEDIUM') * 2 +
         count(*) filter (where upper(severity) = 'LOW') * 1) as severity_score
    from {{ ref('stg_lz_devskim_findings') }}
    group by run_pk, rule_id
),
ranked_rules as (
    select
        *,
        row_number() over (partition by run_pk order by issue_count desc) as issue_rank,
        row_number() over (partition by run_pk order by severity_critical desc, severity_high desc, issue_count desc) as severity_rank,
        row_number() over (partition by run_pk order by files_affected desc, issue_count desc) as spread_rank,
        -- Risk level based on max severity
        case
            when severity_critical > 0 then 'critical'
            when severity_high > 0 then 'high'
            when severity_medium > 0 then 'medium'
            else 'low'
        end as risk_level
    from rule_metrics
)
select
    run_pk,
    rule_id,
    dd_category,
    sample_message,
    issue_count,
    files_affected,
    directories_affected,
    severity_critical,
    severity_high,
    severity_medium,
    severity_low,
    severity_high_plus,
    severity_score,
    issue_rank,
    severity_rank,
    spread_rank,
    risk_level
from ranked_rules
order by run_pk, severity_score desc
