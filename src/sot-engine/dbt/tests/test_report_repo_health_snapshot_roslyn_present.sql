-- Fail if a collection run has a roslyn tool run but the report would yield NULL roslyn distributions.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
roslyn_run as (
    select tr.collection_run_id, tr.run_pk as roslyn_run_pk
    from tool_runs tr
    where tr.tool_name = 'roslyn'
),
root_roslyn as (
    select run_pk, metric
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where metric = 'violation_count'
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
)
select
    rs.collection_run_id,
    rr.roslyn_run_pk
from run_summary rs
join roslyn_run rr
    on rr.collection_run_id = rs.collection_run_id
left join root_roslyn rl
    on rl.run_pk = rr.roslyn_run_pk
where rl.metric is null
