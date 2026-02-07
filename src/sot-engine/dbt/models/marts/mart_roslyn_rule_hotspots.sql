-- Roslyn rule hotspots: identify most impactful analyzer rules for code quality prioritization
-- Severity levels: Error > Warning > Info > Hidden

with rule_metrics as (
    select
        run_pk,
        rule_id,
        -- Representative info
        max(dd_category) as dd_category,
        max(message) as sample_message,
        count(*) as violation_count,
        count(distinct file_id) as files_affected,
        count(distinct directory_id) as directories_affected,
        -- Severity breakdown
        count(*) filter (where severity = 'Error') as severity_error,
        count(*) filter (where severity = 'Warning') as severity_warning,
        count(*) filter (where severity = 'Info') as severity_info,
        count(*) filter (where severity = 'Hidden') as severity_hidden,
        count(*) filter (where severity in ('Error', 'Warning')) as severity_high_plus,
        -- Weighted severity score for ranking
        (count(*) filter (where severity = 'Error') * 4 +
         count(*) filter (where severity = 'Warning') * 3 +
         count(*) filter (where severity = 'Info') * 2 +
         count(*) filter (where severity = 'Hidden') * 1) as severity_score
    from {{ ref('stg_lz_roslyn_violations') }}
    group by run_pk, rule_id
),
ranked_rules as (
    select
        *,
        row_number() over (partition by run_pk order by violation_count desc) as violation_rank,
        row_number() over (partition by run_pk order by severity_error desc, severity_warning desc, violation_count desc) as severity_rank,
        row_number() over (partition by run_pk order by files_affected desc, violation_count desc) as spread_rank,
        -- Risk level based on max severity
        case
            when severity_error > 0 then 'critical'
            when severity_warning > 0 then 'high'
            when severity_info > 0 then 'medium'
            else 'low'
        end as risk_level
    from rule_metrics
)
select
    run_pk,
    rule_id,
    dd_category,
    sample_message,
    violation_count,
    files_affected,
    directories_affected,
    severity_error,
    severity_warning,
    severity_info,
    severity_hidden,
    severity_high_plus,
    severity_score,
    violation_rank,
    severity_rank,
    spread_rank,
    risk_level
from ranked_rules
order by run_pk, severity_score desc
