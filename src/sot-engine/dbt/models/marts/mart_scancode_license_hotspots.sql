-- Scancode license hotspots: identify license distribution for compliance review
-- Risk levels by restrictiveness: copyleft > weak-copyleft > permissive > unknown

with license_metrics as (
    select
        run_pk,
        spdx_id,
        -- Representative category (most restrictive if mixed)
        case
            when count(*) filter (where category = 'copyleft') > 0 then 'copyleft'
            when count(*) filter (where category = 'weak-copyleft') > 0 then 'weak-copyleft'
            when count(*) filter (where category = 'permissive') > 0 then 'permissive'
            else 'unknown'
        end as category,
        count(*) as detection_count,
        count(distinct file_id) as files_affected,
        count(distinct directory_id) as directories_affected,
        -- Confidence metrics
        avg(confidence) as avg_confidence,
        min(confidence) as min_confidence,
        max(confidence) as max_confidence,
        -- Category breakdown
        count(*) filter (where category = 'permissive') as category_permissive,
        count(*) filter (where category = 'weak-copyleft') as category_weak_copyleft,
        count(*) filter (where category = 'copyleft') as category_copyleft,
        count(*) filter (where category = 'unknown') as category_unknown
    from {{ ref('stg_lz_scancode_file_licenses') }}
    group by run_pk, spdx_id
),
ranked_licenses as (
    select
        *,
        row_number() over (partition by run_pk order by detection_count desc) as detection_rank,
        row_number() over (partition by run_pk order by files_affected desc, detection_count desc) as spread_rank,
        -- Risk level based on license restrictiveness
        case
            when category_copyleft > 0 then 'high'
            when category_weak_copyleft > 0 then 'medium'
            when category_permissive > 0 then 'low'
            else 'unknown'
        end as risk_level
    from license_metrics
)
select
    run_pk,
    spdx_id,
    category,
    detection_count,
    files_affected,
    directories_affected,
    avg_confidence,
    min_confidence,
    max_confidence,
    category_permissive,
    category_weak_copyleft,
    category_copyleft,
    category_unknown,
    detection_rank,
    spread_rank,
    risk_level
from ranked_licenses
order by run_pk, detection_count desc
