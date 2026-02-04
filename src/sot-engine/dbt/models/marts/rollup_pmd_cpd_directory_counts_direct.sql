-- PMD-CPD file counts per directory (direct - only files in that directory)

with cpd_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'pmd-cpd'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        cr.run_pk as cpd_run_pk,
        lr.run_pk as layout_run_pk,
        cr.collection_run_id
    from cpd_runs cr
    join layout_runs lr
        on lr.collection_run_id = cr.collection_run_id
),
dir_files as (
    select
        rm.cpd_run_pk as run_pk,
        rm.layout_run_pk,
        cm.directory_id,
        cm.file_id,
        cm.total_lines,
        cm.duplicate_lines,
        cm.duplicate_blocks,
        cm.duplication_percentage,
        cm.language
    from {{ ref('stg_lz_pmd_cpd_file_metrics') }} cm
    join run_map rm
        on rm.cpd_run_pk = cm.run_pk
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
        sum(total_lines) as total_lines,
        sum(duplicate_lines) as total_duplicate_lines,
        sum(duplicate_blocks) as total_duplicate_blocks,
        avg(duplication_percentage) as avg_duplication_percentage,
        count(distinct language) as language_count
    from dir_files
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.total_lines,
    a.total_duplicate_lines,
    a.total_duplicate_blocks,
    a.avg_duplication_percentage,
    a.language_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
