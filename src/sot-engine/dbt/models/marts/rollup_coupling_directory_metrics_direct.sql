-- Coupling metrics per directory (direct - fan-in/fan-out for files in directory)
-- Fan-out: Number of distinct callee files/symbols a directory calls
-- Fan-in: Number of distinct caller files from OTHER directories that call into this directory

with symbol_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'symbol-scanner'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        sr.run_pk as symbol_run_pk,
        lay.run_pk as layout_run_pk,
        sr.collection_run_id
    from symbol_runs sr
    join layout_runs lay
        on lay.collection_run_id = sr.collection_run_id
),
calls_with_directory as (
    select
        rm.symbol_run_pk as run_pk,
        rm.layout_run_pk,
        sc.caller_directory_id,
        sc.caller_file_id,
        sc.caller_symbol,
        sc.callee_symbol,
        sc.callee_file_id,
        sc.call_type
    from {{ ref('stg_lz_symbol_calls') }} sc
    join run_map rm
        on rm.symbol_run_pk = sc.run_pk
),
-- Resolve callee_directory_id by joining with layout files
calls_with_callee_directory as (
    select
        cwd.run_pk,
        cwd.layout_run_pk,
        cwd.caller_directory_id,
        cwd.caller_file_id,
        cwd.caller_symbol,
        cwd.callee_symbol,
        cwd.callee_file_id,
        lf.directory_id as callee_directory_id,
        cwd.call_type
    from calls_with_directory cwd
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = cwd.layout_run_pk
        and lf.file_id = cwd.callee_file_id
    where cwd.callee_file_id is not null
),
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
-- Fan-out: calls FROM this directory TO other symbols
fan_out as (
    select
        run_pk,
        layout_run_pk,
        caller_directory_id as directory_id,
        count(*) as outgoing_calls,
        count(distinct callee_symbol) as distinct_callees,
        count(distinct callee_file_id) as distinct_callee_files,
        sum(case when call_type = 'direct' then 1 else 0 end) as direct_calls,
        sum(case when call_type = 'dynamic' then 1 else 0 end) as dynamic_calls,
        sum(case when call_type = 'async' then 1 else 0 end) as async_calls
    from calls_with_directory
    group by run_pk, layout_run_pk, caller_directory_id
),
-- Fan-in: calls INTO this directory FROM other directories (external calls only)
-- Groups by callee directory and counts distinct caller files from OTHER directories
fan_in_prep as (
    select
        run_pk,
        layout_run_pk,
        callee_directory_id as directory_id,
        count(distinct caller_file_id) as distinct_caller_files
    from calls_with_callee_directory
    where caller_directory_id != callee_directory_id  -- external calls only
    group by run_pk, layout_run_pk, callee_directory_id
),
combined as (
    select
        coalesce(fo.run_pk, fi.run_pk) as run_pk,
        coalesce(fo.layout_run_pk, fi.layout_run_pk) as layout_run_pk,
        coalesce(fo.directory_id, fi.directory_id) as directory_id,
        coalesce(fo.outgoing_calls, 0) as outgoing_calls,
        coalesce(fo.distinct_callees, 0) as distinct_callees,
        coalesce(fo.distinct_callee_files, 0) as fan_out,
        coalesce(fi.distinct_caller_files, 0) as fan_in,
        coalesce(fo.direct_calls, 0) as direct_calls,
        coalesce(fo.dynamic_calls, 0) as dynamic_calls,
        coalesce(fo.async_calls, 0) as async_calls
    from fan_out fo
    full outer join fan_in_prep fi
        on fo.run_pk = fi.run_pk
        and fo.directory_id = fi.directory_id
)
select
    c.run_pk,
    c.directory_id,
    dp.relative_path as directory_path,
    c.outgoing_calls,
    c.distinct_callees,
    c.fan_out,
    c.fan_in,
    c.direct_calls,
    c.dynamic_calls,
    c.async_calls,
    -- Instability metric: fan_out / (fan_in + fan_out), 0 = stable, 1 = unstable
    case
        when c.fan_in + c.fan_out = 0 then 0.0
        else cast(c.fan_out as double) / (c.fan_in + c.fan_out)
    end as instability
from combined c
join directory_paths dp
    on dp.run_pk = c.layout_run_pk
    and dp.directory_id = c.directory_id
