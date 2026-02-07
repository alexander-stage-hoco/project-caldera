-- SonarQube rule hotspots: identify most impactful rules across codebase
-- Aggregates issues by rule_id for prioritization of code quality improvements
-- Risk levels: critical (blocker issues), high (critical issues), medium (major), low (minor/info)

with issues as (
    select
        run_pk,
        collection_run_id,
        rule_id,
        file_id,
        issue_type,
        severity,
        status,
        -- Normalize effort string to minutes
        case
            when effort like '%min' then cast(replace(effort, 'min', '') as integer)
            when effort like '%h' then cast(replace(effort, 'h', '') as integer) * 60
            when effort like '%d' then cast(replace(effort, 'd', '') as integer) * 480
            else 0
        end as effort_minutes
    from {{ ref('stg_sonarqube_issues') }}
),
rule_metrics as (
    select
        run_pk,
        collection_run_id,
        rule_id,
        -- Take the first issue_type for this rule (should be consistent per rule)
        max(issue_type) as issue_type,
        count(*) as issue_count,
        count(distinct file_id) as files_affected,
        -- Severity breakdown
        count(*) filter (where severity = 'BLOCKER') as severity_blocker,
        count(*) filter (where severity = 'CRITICAL') as severity_critical,
        count(*) filter (where severity = 'MAJOR') as severity_major,
        count(*) filter (where severity = 'MINOR') as severity_minor,
        count(*) filter (where severity = 'INFO') as severity_info,
        count(*) filter (where severity in ('BLOCKER', 'CRITICAL')) as severity_high_plus,
        -- Effort metrics
        sum(effort_minutes) as total_effort_minutes,
        round(avg(effort_minutes), 1) as avg_effort_minutes,
        -- Status
        count(*) filter (where status = 'OPEN') as open_count,
        -- Impact score: weighted by severity
        (count(*) filter (where severity = 'BLOCKER') * 4 +
         count(*) filter (where severity = 'CRITICAL') * 3 +
         count(*) filter (where severity = 'MAJOR') * 2 +
         count(*) filter (where severity = 'MINOR') * 1) as impact_score
    from issues
    group by run_pk, collection_run_id, rule_id
),
ranked_rules as (
    select
        *,
        row_number() over (partition by collection_run_id order by issue_count desc) as occurrence_rank,
        row_number() over (partition by collection_run_id order by total_effort_minutes desc) as effort_rank,
        row_number() over (partition by collection_run_id order by impact_score desc) as impact_rank,
        -- Risk level based on severity composition
        case
            when severity_blocker > 0 then 'critical'
            when severity_critical > 0 then 'high'
            when severity_major > 0 then 'medium'
            else 'low'
        end as risk_level
    from rule_metrics
)
select
    run_pk,
    collection_run_id,
    rule_id,
    issue_type,
    issue_count,
    files_affected,
    severity_blocker,
    severity_critical,
    severity_major,
    severity_minor,
    severity_info,
    severity_high_plus,
    total_effort_minutes,
    avg_effort_minutes,
    open_count,
    impact_score,
    occurrence_rank,
    effort_rank,
    impact_rank,
    risk_level
from ranked_rules
order by collection_run_id, impact_score desc
