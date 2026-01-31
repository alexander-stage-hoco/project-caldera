{% set run_pk = var('run_pk') %}

with run_summary as (
    select *
    from {{ ref('unified_run_summary') }}
    where run_pk = {{ run_pk }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
lizard_run as (
    select tr.run_pk as lizard_run_pk
    from tool_runs tr
    join run_summary rs
        on rs.collection_run_id = tr.collection_run_id
    where tr.tool_name = 'lizard'
    limit 1
),
roslyn_run as (
    select tr.run_pk as roslyn_run_pk
    from tool_runs tr
    join run_summary rs
        on rs.collection_run_id = tr.collection_run_id
    where tr.tool_name in ('roslyn', 'roslyn-analyzers')
    limit 1
),
root_scc as (
    select *
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = {{ run_pk }}
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
),
root_lizard as (
    select *
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (
        select lizard_run_pk
        from lizard_run
    )
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
),
root_roslyn as (
    select *
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (
        select roslyn_run_pk
        from roslyn_run
    )
    qualify row_number() over (
        partition by run_pk, metric
        order by length(directory_path), directory_path
    ) = 1
)
select
    rs.repo_id,
    rs.run_id,
    rs.total_files,
    rs.total_loc,
    rs.total_code,
    rs.total_comment,
    rs.total_blank,
    rs.total_ccn,
    rs.avg_ccn,
    rs.max_ccn,
    rs.avg_nloc,
    scc_loc.p95_value as scc_loc_p95,
    scc_loc.p99_value as scc_loc_p99,
    scc_loc.gini_value as scc_loc_gini,
    scc_loc.hoover_value as scc_loc_hoover,
    scc_loc.top_20_pct_share as scc_loc_top_20_share,
    lizard_ccn.p95_value as ccn_p95,
    lizard_ccn.p99_value as ccn_p99,
    lizard_ccn.gini_value as ccn_gini,
    lizard_ccn.hoover_value as ccn_hoover,
    lizard_ccn.top_20_pct_share as ccn_top_20_share,
    roslyn_v.p95_value as roslyn_violation_p95,
    roslyn_v.p99_value as roslyn_violation_p99,
    roslyn_v.gini_value as roslyn_violation_gini,
    roslyn_v.hoover_value as roslyn_violation_hoover,
    roslyn_v.top_20_pct_share as roslyn_violation_top_20_share
from run_summary rs
left join root_scc scc_loc
    on scc_loc.run_pk = rs.run_pk
    and scc_loc.metric = 'lines_total'
left join root_lizard lizard_ccn
    on lizard_ccn.metric = 'total_ccn'
left join root_roslyn roslyn_v
    on roslyn_v.metric = 'violation_count'
