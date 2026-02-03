-- Symbol counts per directory (recursive - includes all files in subtree)

with recursive symbol_runs as (
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
dir_tree as (
    -- Base case: each directory is its own ancestor
    select
        rm.symbol_run_pk,
        rm.layout_run_pk,
        ld.directory_id as ancestor_id,
        ld.directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }} ld
    join run_map rm
        on rm.layout_run_pk = ld.run_pk

    union all

    -- Recursive case: parent inherits children
    select
        parent.symbol_run_pk,
        parent.layout_run_pk,
        parent.ancestor_id,
        child.directory_id as descendant_id
    from dir_tree parent
    join {{ source('lz', 'lz_layout_directories') }} child
        on child.run_pk = parent.layout_run_pk
        and child.parent_id = parent.descendant_id
),
files_with_ancestor as (
    select
        dt.symbol_run_pk,
        dt.layout_run_pk,
        lf.file_id,
        dt.ancestor_id as directory_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join dir_tree dt
        on dt.layout_run_pk = lf.run_pk
        and dt.descendant_id = lf.directory_id
),
file_metrics as (
    select
        fa.symbol_run_pk as run_pk,
        fa.layout_run_pk,
        fa.directory_id,
        m.symbol_count,
        m.function_count,
        m.class_count,
        m.method_count,
        m.exported_count,
        m.avg_parameters
    from files_with_ancestor fa
    join {{ ref('stg_symbols_file_metrics') }} m
        on m.run_pk = fa.symbol_run_pk
        and m.file_id = fa.file_id
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
        sum(symbol_count) as symbol_count,
        count(*) as file_count,
        sum(function_count) as function_count,
        sum(class_count) as class_count,
        sum(method_count) as method_count,
        sum(exported_count) as exported_count,
        avg(avg_parameters) as avg_parameters
    from file_metrics
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
