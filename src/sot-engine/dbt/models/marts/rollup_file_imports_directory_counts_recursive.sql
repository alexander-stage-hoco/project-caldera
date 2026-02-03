-- File import counts per directory (recursive - includes all files in subtree)

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
        m.import_count,
        m.unique_imports,
        m.static_import_count,
        m.dynamic_import_count,
        m.side_effect_import_count
    from files_with_ancestor fa
    join {{ ref('stg_file_imports_file_metrics') }} m
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
        count(*) as file_count,
        sum(import_count) as total_import_count,
        sum(unique_imports) as total_unique_imports,
        sum(static_import_count) as total_static_import_count,
        sum(dynamic_import_count) as total_dynamic_import_count,
        sum(side_effect_import_count) as total_side_effect_import_count
    from file_metrics
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
