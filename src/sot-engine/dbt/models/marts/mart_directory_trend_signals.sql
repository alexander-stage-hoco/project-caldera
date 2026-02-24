-- Directory trend signals: cross-run directory metric deltas
-- Answers: "Which directories are growing, shrinking, or newly created?"
-- Compares directory-level metrics between consecutive runs

with collection_runs as (
    select
        collection_run_id,
        repo_id,
        started_at
    from {{ source('lz', 'lz_collection_runs') }}
    where status = 'completed'
),

-- Pair consecutive runs per repo
run_pairs as (
    select
        collection_run_id as curr_collection_run_id,
        repo_id,
        lag(collection_run_id) over (
            partition by repo_id order by started_at
        ) as prev_collection_run_id
    from collection_runs
),

valid_pairs as (
    select *
    from run_pairs
    where prev_collection_run_id is not null
),

-- Get tool run PKs for layout-scanner
tool_runs as (
    select
        run_pk,
        collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout-scanner', 'layout')
),

-- Current run directories
curr_dirs as (
    select
        vp.curr_collection_run_id as collection_run_id,
        vp.repo_id,
        vp.prev_collection_run_id,
        tr.run_pk,
        d.directory_id,
        d.relative_path,
        d.file_count as current_file_count,
        d.total_size_bytes as current_size
    from valid_pairs vp
    inner join tool_runs tr
        on tr.collection_run_id = vp.curr_collection_run_id
    inner join {{ ref('stg_lz_layout_directories') }} d
        on d.run_pk = tr.run_pk
),

-- Previous run directories
prev_dirs as (
    select
        vp.curr_collection_run_id,
        tr.run_pk as prev_run_pk,
        d.directory_id as prev_directory_id,
        d.relative_path as prev_path,
        d.file_count as prev_file_count,
        d.total_size_bytes as prev_size
    from valid_pairs vp
    inner join tool_runs tr
        on tr.collection_run_id = vp.prev_collection_run_id
    inner join {{ ref('stg_lz_layout_directories') }} d
        on d.run_pk = tr.run_pk
),

-- Directories present in both runs (by path)
both_runs as (
    select
        cd.run_pk,
        cd.collection_run_id,
        cd.repo_id,
        cd.directory_id,
        cd.relative_path,
        cd.current_file_count,
        coalesce(pd.prev_file_count, 0) as prev_file_count,
        coalesce(cd.current_file_count, 0) - coalesce(pd.prev_file_count, 0) as file_count_delta,
        cd.current_size,
        pd.prev_size,
        coalesce(cd.current_size, 0) - coalesce(pd.prev_size, 0) as size_delta,
        case
            when coalesce(cd.current_file_count, 0) - coalesce(pd.prev_file_count, 0) > 0 then 'growing'
            when coalesce(cd.current_file_count, 0) - coalesce(pd.prev_file_count, 0) < 0 then 'shrinking'
            else 'stable'
        end as structure_trend
    from curr_dirs cd
    inner join prev_dirs pd
        on pd.curr_collection_run_id = cd.collection_run_id
        and pd.prev_path = cd.relative_path
),

-- New directories (in current but not previous)
new_dirs as (
    select
        cd.run_pk,
        cd.collection_run_id,
        cd.repo_id,
        cd.directory_id,
        cd.relative_path,
        cd.current_file_count,
        cast(null as integer) as prev_file_count,
        cd.current_file_count as file_count_delta,
        cd.current_size,
        cast(null as bigint) as prev_size,
        cd.current_size as size_delta,
        'new_directory' as structure_trend
    from curr_dirs cd
    left join prev_dirs pd
        on pd.curr_collection_run_id = cd.collection_run_id
        and pd.prev_path = cd.relative_path
    where pd.prev_path is null
),

-- Deleted directories (in previous but not current)
deleted_dirs as (
    select
        cd_any.run_pk,
        pd.curr_collection_run_id as collection_run_id,
        cd_any.repo_id,
        cast(null as varchar) as directory_id,
        pd.prev_path as relative_path,
        cast(null as integer) as current_file_count,
        pd.prev_file_count,
        -coalesce(pd.prev_file_count, 0) as file_count_delta,
        cast(null as bigint) as current_size,
        pd.prev_size,
        -coalesce(pd.prev_size, 0) as size_delta,
        'deleted' as structure_trend
    from prev_dirs pd
    left join curr_dirs cd
        on cd.collection_run_id = pd.curr_collection_run_id
        and cd.relative_path = pd.prev_path
    inner join (
        select distinct collection_run_id, repo_id, run_pk
        from curr_dirs
    ) cd_any
        on cd_any.collection_run_id = pd.curr_collection_run_id
    where cd.relative_path is null
),

combined as (
    select run_pk, collection_run_id, repo_id, directory_id, relative_path,
           current_file_count, prev_file_count, file_count_delta,
           current_size, prev_size, size_delta, structure_trend
    from both_runs

    union all

    select run_pk, collection_run_id, repo_id, directory_id, relative_path,
           current_file_count, prev_file_count, file_count_delta,
           current_size, prev_size, size_delta, structure_trend
    from new_dirs

    union all

    select run_pk, collection_run_id, repo_id, directory_id, relative_path,
           current_file_count, prev_file_count, file_count_delta,
           current_size, prev_size, size_delta, structure_trend
    from deleted_dirs
)

select
    run_pk,
    collection_run_id,
    repo_id,
    directory_id,
    relative_path,
    current_file_count,
    prev_file_count,
    file_count_delta,
    current_size,
    prev_size,
    size_delta,
    structure_trend
from combined
