-- Layout file counts per directory (direct - only files in that directory)

with layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
dir_files as (
    select
        lr.run_pk,
        lf.directory_id,
        ld.relative_path as directory_path,
        lf.file_id,
        lf.size_bytes,
        lf.line_count,
        lf.language,
        lf.category,
        lf.is_binary
    from {{ source('lz', 'lz_layout_files') }} lf
    join layout_runs lr
        on lr.run_pk = lf.run_pk
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = lf.run_pk
        and ld.directory_id = lf.directory_id
)
select
    run_pk,
    directory_id,
    directory_path,
    count(distinct file_id) as file_count,
    count(case when is_binary then 1 end) as binary_file_count,
    sum(size_bytes) as total_size_bytes,
    sum(line_count) as total_line_count,
    count(distinct language) as language_count,
    count(distinct category) as category_count
from dir_files
group by run_pk, directory_id, directory_path
