-- Fail if roslyn tool runs exist with violations in LZ but category totals would be empty.
-- Note: If roslyn finds zero violations, having no rows in stg_roslyn_file_metrics is valid.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
tool_map as (
    select
        rs.collection_run_id,
        max(case when tr.tool_name in ('roslyn', 'roslyn-analyzers') then tr.run_pk end) as roslyn_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
roslyn_violations as (
    -- Check if violations exist in LZ
    select run_pk, count(*) as violation_count
    from {{ source('lz', 'lz_roslyn_violations') }}
    group by run_pk
),
roslyn_rows as (
    select run_pk
    from {{ ref('stg_roslyn_file_metrics') }}
)
select tm.collection_run_id
from tool_map tm
left join roslyn_violations rv
    on rv.run_pk = tm.roslyn_run_pk
left join roslyn_rows rr
    on rr.run_pk = tm.roslyn_run_pk
-- Only fail if there ARE violations in LZ but no rows in staging
where tm.roslyn_run_pk is not null
  and rv.violation_count > 0
  and rr.run_pk is null
