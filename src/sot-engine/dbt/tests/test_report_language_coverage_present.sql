-- Fail if a collection run has a layout tool run but language coverage would be empty.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
layout_run as (
    select tr.collection_run_id, tr.run_pk as layout_run_pk
    from tool_runs tr
    where tr.tool_name in ('layout', 'layout-scanner')
),
layout_files as (
    select run_pk
    from {{ source('lz', 'lz_layout_files') }}
)
select
    rs.collection_run_id,
    lr.layout_run_pk
from run_summary rs
join layout_run lr
    on lr.collection_run_id = rs.collection_run_id
left join layout_files lf
    on lf.run_pk = lr.layout_run_pk
where lf.run_pk is null
