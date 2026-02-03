-- Symbol counts per directory (direct - only symbols in that directory)

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
symbols_with_directory as (
    select
        rm.symbol_run_pk as run_pk,
        rm.layout_run_pk,
        cs.directory_id,
        cs.file_id,
        cs.symbol_name,
        cs.symbol_type,
        cs.is_exported,
        cs.parameters
    from {{ ref('stg_lz_code_symbols') }} cs
    join run_map rm
        on rm.symbol_run_pk = cs.run_pk
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
        count(*) as symbol_count,
        count(distinct file_id) as file_count,
        sum(case when symbol_type = 'function' then 1 else 0 end) as function_count,
        sum(case when symbol_type = 'class' then 1 else 0 end) as class_count,
        sum(case when symbol_type = 'method' then 1 else 0 end) as method_count,
        sum(case when is_exported then 1 else 0 end) as exported_count,
        avg(parameters) as avg_parameters
    from symbols_with_directory
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.symbol_count,
    a.file_count,
    a.function_count,
    a.class_count,
    a.method_count,
    a.exported_count,
    a.avg_parameters
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
