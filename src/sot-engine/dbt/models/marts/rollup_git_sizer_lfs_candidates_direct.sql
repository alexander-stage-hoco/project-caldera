-- Git-sizer LFS candidates per directory (direct - only files in that directory)
-- Note: git-sizer LFS candidates only have file_path, so we join through layout files on relative_path

with git_sizer_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'git-sizer'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        gs.run_pk as git_sizer_run_pk,
        lay.run_pk as layout_run_pk,
        gs.collection_run_id
    from git_sizer_runs gs
    join layout_runs lay
        on lay.collection_run_id = gs.collection_run_id
),
files_with_directory as (
    select
        rm.git_sizer_run_pk as run_pk,
        rm.layout_run_pk,
        lf.directory_id,
        lfc.file_path
    from {{ ref('stg_lz_git_sizer_lfs_candidates') }} lfc
    join run_map rm
        on rm.git_sizer_run_pk = lfc.run_pk
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = rm.layout_run_pk
        and lf.relative_path = lfc.file_path
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
        count(*) as lfs_candidate_count
    from files_with_directory
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.lfs_candidate_count
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
