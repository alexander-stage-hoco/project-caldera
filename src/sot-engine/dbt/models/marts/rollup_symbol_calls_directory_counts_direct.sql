-- Symbol call counts per directory (direct - only calls from files in that directory)

with symbol_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'symbol-scanner'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        sr.run_pk as symbol_run_pk,
        lay.run_pk as layout_run_pk,
        sr.collection_run_id
    from symbol_runs sr
    join layout_runs lay
        on lay.collection_run_id = sr.collection_run_id
),
calls_with_directory as (
    select
        rm.symbol_run_pk as run_pk,
        rm.layout_run_pk,
        m.directory_id,
        m.file_id,
        m.call_count,
        m.distinct_callees,
        m.distinct_callee_files,
        m.direct_call_count,
        m.dynamic_call_count,
        m.async_call_count
    from {{ ref('stg_symbol_calls_file_metrics') }} m
    join run_map rm
        on rm.symbol_run_pk = m.run_pk
),
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
aggregated as (
    select
        run_pk,
        layout_run_pk,
        directory_id,
        count(*) as file_count,
        sum(call_count) as total_call_count,
        sum(distinct_callees) as total_distinct_callees,
        sum(distinct_callee_files) as total_distinct_callee_files,
        sum(direct_call_count) as total_direct_call_count,
        sum(dynamic_call_count) as total_dynamic_call_count,
        sum(async_call_count) as total_async_call_count
    from calls_with_directory
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.total_call_count,
    a.total_distinct_callees,
    a.total_distinct_callee_files,
    a.total_direct_call_count,
    a.total_dynamic_call_count,
    a.total_async_call_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
