-- Git-sizer violation hotspots: identify repository health issues by metric
-- Levels: 1=notice, 2=warning, 3=attention, 4=critical

with violation_metrics as (
    select
        run_pk,
        metric,
        count(*) as violation_count,
        max(level) as max_level,
        min(level) as min_level,
        -- Representative info
        max(value_display) as sample_value_display,
        max(object_ref) as sample_object_ref,
        -- Level breakdown
        count(*) filter (where level = 1) as level_1_count,
        count(*) filter (where level = 2) as level_2_count,
        count(*) filter (where level = 3) as level_3_count,
        count(*) filter (where level = 4) as level_4_count,
        count(*) filter (where level >= 3) as level_3_plus,
        -- Weighted severity score
        (count(*) filter (where level = 4) * 4 +
         count(*) filter (where level = 3) * 3 +
         count(*) filter (where level = 2) * 2 +
         count(*) filter (where level = 1) * 1) as severity_score,
        -- Value metrics
        min(raw_value) as min_raw_value,
        max(raw_value) as max_raw_value,
        count(distinct object_ref) as distinct_objects
    from {{ ref('stg_lz_git_sizer_violations') }}
    group by run_pk, metric
),
ranked_violations as (
    select
        *,
        row_number() over (partition by run_pk order by violation_count desc) as violation_rank,
        row_number() over (partition by run_pk order by max_level desc, level_4_count desc, level_3_count desc, violation_count desc) as severity_rank,
        -- Risk level based on max level
        case
            when max_level = 4 then 'critical'
            when max_level = 3 then 'high'
            when max_level = 2 then 'medium'
            else 'low'
        end as risk_level
    from violation_metrics
)
select
    run_pk,
    metric,
    violation_count,
    max_level,
    min_level,
    sample_value_display,
    sample_object_ref,
    level_1_count,
    level_2_count,
    level_3_count,
    level_4_count,
    level_3_plus,
    severity_score,
    min_raw_value,
    max_raw_value,
    distinct_objects,
    violation_rank,
    severity_rank,
    risk_level
from ranked_violations
order by run_pk, severity_score desc
