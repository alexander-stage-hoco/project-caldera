-- Lizard file counts per directory (direct - only files in that directory)
-- Note: Lizard lacks directory_id, so we join through layout files on relative_path

with lizard_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'lizard'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        lr_tool.run_pk as lizard_run_pk,
        lay.run_pk as layout_run_pk,
        lr_tool.collection_run_id
    from lizard_runs lr_tool
    join layout_runs lay
        on lay.collection_run_id = lr_tool.collection_run_id
),
files_with_directory as (
    select
        rm.lizard_run_pk as run_pk,
        rm.layout_run_pk,
        lf.directory_id,
        lm.file_id,
        lm.nloc,
        lm.function_count,
        lm.total_ccn,
        lm.avg_ccn,
        lm.max_ccn,
        lm.language
    from {{ ref('stg_lz_lizard_file_metrics') }} lm
    join run_map rm
        on rm.lizard_run_pk = lm.run_pk
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = rm.layout_run_pk
        and lf.relative_path = lm.relative_path
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
        count(distinct file_id) as file_count,
        sum(nloc) as total_nloc,
        sum(function_count) as total_function_count,
        sum(total_ccn) as total_ccn,
        avg(avg_ccn) as avg_ccn,
        max(max_ccn) as max_ccn,
        count(distinct language) as language_count
    from files_with_directory
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.total_nloc,
    a.total_function_count,
    a.total_ccn,
    a.avg_ccn,
    a.max_ccn,
    a.language_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
