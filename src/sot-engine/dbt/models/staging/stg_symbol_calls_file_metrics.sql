-- Aggregates stg_lz_symbol_calls to file-level metrics (caller perspective)
with calls as (
    select run_pk, caller_file_id, caller_directory_id, caller_file_path, callee_symbol, callee_file_id, call_type
    from {{ ref('stg_lz_symbol_calls') }}
),
file_metrics as (
    select
        run_pk,
        caller_file_id as file_id,
        caller_directory_id as directory_id,
        min(caller_file_path) as relative_path,
        count(*) as call_count,
        count(distinct callee_symbol) as distinct_callees,
        count(distinct callee_file_id) as distinct_callee_files,
        count(case when call_type = 'direct' then 1 end) as direct_call_count,
        count(case when call_type = 'dynamic' then 1 end) as dynamic_call_count,
        count(case when call_type = 'async' then 1 end) as async_call_count
    from calls
    group by run_pk, caller_file_id, caller_directory_id
)
select * from file_metrics
