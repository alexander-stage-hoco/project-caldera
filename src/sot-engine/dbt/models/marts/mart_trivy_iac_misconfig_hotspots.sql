-- Trivy IaC misconfig hotspots: identify misconfiguration patterns for security remediation
-- Severity levels: CRITICAL > HIGH > MEDIUM > LOW > UNKNOWN

with misconfig_metrics as (
    select
        run_pk,
        misconfig_id,
        -- Representative info
        max(title) as sample_title,
        max(resolution) as sample_resolution,
        count(*) as issue_count,
        count(distinct file_id) as files_affected,
        count(distinct directory_id) as directories_affected,
        -- Severity breakdown
        count(*) filter (where upper(severity) = 'CRITICAL') as severity_critical,
        count(*) filter (where upper(severity) = 'HIGH') as severity_high,
        count(*) filter (where upper(severity) = 'MEDIUM') as severity_medium,
        count(*) filter (where upper(severity) = 'LOW') as severity_low,
        count(*) filter (where upper(severity) = 'UNKNOWN') as severity_unknown,
        count(*) filter (where upper(severity) in ('CRITICAL', 'HIGH')) as severity_high_plus,
        -- Weighted severity score for ranking
        (count(*) filter (where upper(severity) = 'CRITICAL') * 4 +
         count(*) filter (where upper(severity) = 'HIGH') * 3 +
         count(*) filter (where upper(severity) = 'MEDIUM') * 2 +
         count(*) filter (where upper(severity) = 'LOW') * 1) as severity_score,
        -- Target type breakdown
        count(*) filter (where lower(target_type) like '%terraform%') as target_terraform,
        count(*) filter (where lower(target_type) like '%dockerfile%') as target_dockerfile,
        count(*) filter (where lower(target_type) like '%kubernetes%') as target_kubernetes,
        count(*) filter (where lower(target_type) not like '%terraform%'
                           and lower(target_type) not like '%dockerfile%'
                           and lower(target_type) not like '%kubernetes%') as target_other
    from {{ ref('stg_trivy_iac_misconfigs') }}
    group by run_pk, misconfig_id
),
ranked_misconfigs as (
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
    from misconfig_metrics
)
select
    run_pk,
    misconfig_id,
    sample_title,
    sample_resolution,
    issue_count,
    files_affected,
    directories_affected,
    severity_critical,
    severity_high,
    severity_medium,
    severity_low,
    severity_unknown,
    severity_high_plus,
    severity_score,
    target_terraform,
    target_dockerfile,
    target_kubernetes,
    target_other,
    issue_rank,
    severity_rank,
    spread_rank,
    risk_level
from ranked_misconfigs
order by run_pk, severity_score desc
