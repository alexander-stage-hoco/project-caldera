-- Fail if a collection run has an scc tool run but the report would yield NULL LOC distribution.
with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
scc_run as (
    select tr.collection_run_id, tr.run_pk as scc_run_pk
    from tool_runs tr
    where tr.tool_name = 'scc'
),
root_scc as (
    select run_pk, metric
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where metric = 'lines_total'
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
)
select
    rs.collection_run_id,
    sr.scc_run_pk
from run_summary rs
join scc_run sr
    on sr.collection_run_id = rs.collection_run_id
left join root_scc sc
    on sc.run_pk = sr.scc_run_pk
where sc.metric is null
