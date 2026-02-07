-- Git-sizer LFS candidates per directory (recursive - all files in subtree)
-- Note: git-sizer LFS candidates only have file_path, so we join through layout files on relative_path

with recursive git_sizer_runs as (
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
dir_tree as (
    -- Base case: each directory is its own ancestor
    select
        rm.git_sizer_run_pk,
        rm.layout_run_pk,
        ld.directory_id as ancestor_id,
        ld.directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }} ld
    join run_map rm
        on rm.layout_run_pk = ld.run_pk

    union all

    -- Recursive case: parent inherits children
    select
        parent.git_sizer_run_pk,
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
        dt.git_sizer_run_pk,
        dt.layout_run_pk,
        dt.ancestor_id as directory_id,
        lfc.file_path
    from {{ ref('stg_lz_git_sizer_lfs_candidates') }} lfc
    join run_map rm
        on rm.git_sizer_run_pk = lfc.run_pk
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = rm.layout_run_pk
        and lf.relative_path = lfc.file_path
    join dir_tree dt
        on dt.git_sizer_run_pk = lfc.run_pk
        and dt.descendant_id = lf.directory_id
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
        git_sizer_run_pk as run_pk,
        layout_run_pk,
        directory_id,
        count(*) as lfs_candidate_count
    from files_with_ancestor
    group by git_sizer_run_pk, layout_run_pk, directory_id
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
