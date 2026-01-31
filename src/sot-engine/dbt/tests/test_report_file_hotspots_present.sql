-- Fail if a collection run has scc tool output but file hotspots would be empty.
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
scc_files as (
    select run_pk
    from {{ source('lz', 'lz_scc_file_metrics') }}
)
select
    rs.collection_run_id,
    sr.scc_run_pk
from run_summary rs
join scc_run sr
    on sr.collection_run_id = rs.collection_run_id
left join scc_files sf
    on sf.run_pk = sr.scc_run_pk
where sf.run_pk is null
