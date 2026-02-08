-- Staging model for git-sizer LFS candidates with file size metrics
-- Joins LFS candidates with layout files and SCC file metrics to get file_size_bytes
-- This enables distribution statistics on LFS candidate sizes

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
scc_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'scc'
),
run_map as (
    select
        gs.run_pk as git_sizer_run_pk,
        lay.run_pk as layout_run_pk,
        scc.run_pk as scc_run_pk,
        gs.collection_run_id
    from git_sizer_runs gs
    join layout_runs lay
        on lay.collection_run_id = gs.collection_run_id
    join scc_runs scc
        on scc.collection_run_id = gs.collection_run_id
),
lfs_with_file_info as (
    select
        rm.git_sizer_run_pk as run_pk,
        rm.layout_run_pk,
        rm.scc_run_pk,
        lf.file_id,
        lf.directory_id,
        lfc.file_path
    from {{ ref('stg_lz_git_sizer_lfs_candidates') }} lfc
    join run_map rm
        on rm.git_sizer_run_pk = lfc.run_pk
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = rm.layout_run_pk
        and lf.relative_path = lfc.file_path
)
select
    lfwf.run_pk,
    lfwf.file_id,
    lfwf.directory_id,
    lfwf.file_path,
    scc.bytes as file_size_bytes
from lfs_with_file_info lfwf
join {{ source('lz', 'lz_scc_file_metrics') }} scc
    on scc.run_pk = lfwf.scc_run_pk
    and scc.file_id = lfwf.file_id
