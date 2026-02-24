-- File identity map: cross-run file lifecycle tracking
-- Answers: "What changed between consecutive analyses of the same repo?"
-- Classifies each file as unchanged, modified, moved, new, or deleted

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

-- Only keep pairs where a previous run exists
valid_pairs as (
    select *
    from run_pairs
    where prev_collection_run_id is not null
),

-- Get tool run PKs for layout-scanner
tool_runs as (
    select
        run_pk,
        collection_run_id,
        tool_name
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout-scanner', 'layout')
),

-- Current run files
curr_files as (
    select
        vp.curr_collection_run_id as collection_run_id,
        vp.repo_id,
        vp.prev_collection_run_id,
        tr.run_pk,
        f.file_id,
        f.relative_path,
        f.stable_fingerprint,
        f.size_bytes,
        f.language
    from valid_pairs vp
    inner join tool_runs tr
        on tr.collection_run_id = vp.curr_collection_run_id
    inner join {{ ref('stg_lz_layout_files') }} f
        on f.run_pk = tr.run_pk
),

-- Previous run files
prev_files as (
    select
        vp.curr_collection_run_id,
        tr.run_pk as prev_run_pk,
        f.file_id as prev_file_id,
        f.relative_path as prev_path,
        f.stable_fingerprint as prev_fingerprint,
        f.size_bytes as prev_size_bytes
    from valid_pairs vp
    inner join tool_runs tr
        on tr.collection_run_id = vp.prev_collection_run_id
    inner join {{ ref('stg_lz_layout_files') }} f
        on f.run_pk = tr.run_pk
),

-- Match by path (same path in both runs)
path_matches as (
    select
        cf.run_pk,
        cf.collection_run_id,
        cf.repo_id,
        cf.file_id,
        cf.relative_path,
        cf.stable_fingerprint,
        cf.size_bytes,
        cf.language,
        pf.prev_path,
        pf.prev_fingerprint,
        pf.prev_size_bytes,
        case
            when cf.stable_fingerprint is null or pf.prev_fingerprint is null then 'unknown'
            when cf.stable_fingerprint = pf.prev_fingerprint then 'unchanged'
            else 'modified'
        end as lifecycle_status
    from curr_files cf
    inner join prev_files pf
        on pf.curr_collection_run_id = cf.collection_run_id
        and pf.prev_path = cf.relative_path
),

-- Files in current but not in previous (candidates for new or moved)
curr_only as (
    select
        cf.run_pk,
        cf.collection_run_id,
        cf.repo_id,
        cf.file_id,
        cf.relative_path,
        cf.stable_fingerprint,
        cf.size_bytes,
        cf.language
    from curr_files cf
    left join prev_files pf
        on pf.curr_collection_run_id = cf.collection_run_id
        and pf.prev_path = cf.relative_path
    where pf.prev_path is null
),

-- Files in previous but not in current (candidates for deleted or moved)
prev_only as (
    select
        pf.curr_collection_run_id as collection_run_id,
        pf.prev_path,
        pf.prev_fingerprint,
        pf.prev_size_bytes
    from prev_files pf
    left join curr_files cf
        on cf.collection_run_id = pf.curr_collection_run_id
        and cf.relative_path = pf.prev_path
    where cf.relative_path is null
),

-- Detect moves: new-path file has same fingerprint as a deleted-path file
moved_files as (
    select
        co.run_pk,
        co.collection_run_id,
        co.repo_id,
        co.file_id,
        co.relative_path,
        co.stable_fingerprint,
        co.size_bytes,
        co.language,
        po.prev_path,
        po.prev_size_bytes,
        'moved' as lifecycle_status
    from curr_only co
    inner join prev_only po
        on po.collection_run_id = co.collection_run_id
        and po.prev_fingerprint = co.stable_fingerprint
    where co.stable_fingerprint is not null
),

-- New files: in current only and not detected as moved
new_files as (
    select
        co.run_pk,
        co.collection_run_id,
        co.repo_id,
        co.file_id,
        co.relative_path,
        co.stable_fingerprint,
        co.size_bytes,
        co.language,
        cast(null as varchar) as prev_path,
        cast(null as bigint) as prev_size_bytes,
        'new' as lifecycle_status
    from curr_only co
    left join moved_files mf
        on mf.collection_run_id = co.collection_run_id
        and mf.file_id = co.file_id
    where mf.file_id is null
),

-- Deleted files: in previous only and not the source of a move
deleted_files as (
    select
        -- Use current run context for the deleted record
        cf_any.run_pk,
        po.collection_run_id,
        cf_any.repo_id,
        cast(null as varchar) as file_id,
        po.prev_path as relative_path,
        po.prev_fingerprint as stable_fingerprint,
        cast(null as bigint) as size_bytes,
        cast(null as varchar) as language,
        po.prev_path as prev_path,
        po.prev_size_bytes,
        'deleted' as lifecycle_status
    from prev_only po
    left join moved_files mf
        on mf.collection_run_id = po.collection_run_id
        and mf.prev_path = po.prev_path
    -- Get a run_pk from the current run for context
    inner join (
        select distinct collection_run_id, repo_id, run_pk
        from curr_files
    ) cf_any
        on cf_any.collection_run_id = po.collection_run_id
    where mf.prev_path is null
),

-- Union all lifecycle statuses
combined as (
    select run_pk, collection_run_id, repo_id, file_id, relative_path,
           stable_fingerprint, lifecycle_status, prev_path, size_bytes,
           prev_size_bytes, language
    from path_matches

    union all

    select run_pk, collection_run_id, repo_id, file_id, relative_path,
           stable_fingerprint, lifecycle_status, prev_path, size_bytes,
           prev_size_bytes, language
    from moved_files

    union all

    select run_pk, collection_run_id, repo_id, file_id, relative_path,
           stable_fingerprint, lifecycle_status, prev_path, size_bytes,
           prev_size_bytes, language
    from new_files

    union all

    select run_pk, collection_run_id, repo_id, file_id, relative_path,
           stable_fingerprint, lifecycle_status, prev_path, size_bytes,
           prev_size_bytes, language
    from deleted_files
)

select
    run_pk,
    collection_run_id,
    repo_id,
    file_id,
    relative_path,
    stable_fingerprint,
    lifecycle_status,
    prev_path,
    size_bytes,
    prev_size_bytes,
    language
from combined
