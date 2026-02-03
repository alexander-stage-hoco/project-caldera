-- File import counts per directory (direct - only imports from files in that directory)

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
imports_with_directory as (
    select
        rm.symbol_run_pk as run_pk,
        rm.layout_run_pk,
        m.directory_id,
        m.file_id,
        m.import_count,
        m.unique_imports,
        m.static_import_count,
        m.dynamic_import_count,
        m.side_effect_import_count
    from {{ ref('stg_file_imports_file_metrics') }} m
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
        sum(import_count) as total_import_count,
        sum(unique_imports) as total_unique_imports,
        sum(static_import_count) as total_static_import_count,
        sum(dynamic_import_count) as total_dynamic_import_count,
        sum(side_effect_import_count) as total_side_effect_import_count
    from imports_with_directory
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.total_import_count,
    a.total_unique_imports,
    a.total_static_import_count,
    a.total_dynamic_import_count,
    a.total_side_effect_import_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
