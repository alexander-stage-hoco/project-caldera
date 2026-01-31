-- SCC file counts per directory (direct - only files in that directory)

with scc_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'scc'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        sr.run_pk as scc_run_pk,
        lr.run_pk as layout_run_pk,
        sr.collection_run_id
    from scc_runs sr
    join layout_runs lr
        on lr.collection_run_id = sr.collection_run_id
),
dir_files as (
    select
        rm.scc_run_pk as run_pk,
        rm.layout_run_pk,
        sm.directory_id,
        sm.file_id,
        sm.lines_total,
        sm.code_lines,
        sm.comment_lines,
        sm.blank_lines,
        sm.complexity,
        sm.language,
        sm.is_minified,
        sm.is_generated
    from {{ ref('stg_lz_scc_file_metrics') }} sm
    join run_map rm
        on rm.scc_run_pk = sm.run_pk
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
        sum(lines_total) as total_lines,
        sum(code_lines) as total_code_lines,
        sum(comment_lines) as total_comment_lines,
        sum(blank_lines) as total_blank_lines,
        sum(complexity) as total_complexity,
        count(case when is_minified then 1 end) as minified_count,
        count(case when is_generated then 1 end) as generated_count,
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
    a.total_code_lines,
    a.total_comment_lines,
    a.total_blank_lines,
    a.total_complexity,
    a.minified_count,
    a.generated_count,
    a.language_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
