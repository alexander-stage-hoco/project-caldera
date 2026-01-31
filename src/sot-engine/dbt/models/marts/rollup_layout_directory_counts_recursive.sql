-- Layout file counts per directory (recursive - all files in subtree)

with recursive layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
dir_tree as (
    select
        lr.run_pk as layout_run_pk,
        ld.directory_id as ancestor_id,
        ld.directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }} ld
    join layout_runs lr
        on lr.run_pk = ld.run_pk

    union all

    select
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
        dt.layout_run_pk as run_pk,
        dt.ancestor_id as directory_id,
        lf.file_id,
        lf.size_bytes,
        lf.line_count,
        lf.language,
        lf.category,
        lf.is_binary
    from {{ source('lz', 'lz_layout_files') }} lf
    join dir_tree dt
        on dt.layout_run_pk = lf.run_pk
        and dt.descendant_id = lf.directory_id
),
dir_files as (
    select
        fa.run_pk,
        fa.directory_id,
        ld.relative_path as directory_path,
        fa.file_id,
        fa.size_bytes,
        fa.line_count,
        fa.language,
        fa.category,
        fa.is_binary
    from files_with_ancestor fa
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = fa.run_pk
        and ld.directory_id = fa.directory_id
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
