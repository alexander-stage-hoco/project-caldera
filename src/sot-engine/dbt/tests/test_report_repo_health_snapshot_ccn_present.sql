-- Fail if a collection run has a lizard tool run but the report would yield NULL CCN distribution.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
lizard_run as (
    select tr.collection_run_id, tr.run_pk as lizard_run_pk
    from tool_runs tr
    where tr.tool_name = 'lizard'
),
root_lizard as (
    select run_pk, metric
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where metric = 'total_ccn'
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
)
select
    rs.collection_run_id,
    lr.lizard_run_pk
from run_summary rs
join lizard_run lr
    on lr.collection_run_id = rs.collection_run_id
left join root_lizard rl
    on rl.run_pk = lr.lizard_run_pk
where rl.metric is null
