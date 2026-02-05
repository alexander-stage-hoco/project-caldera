-- Per-symbol coupling metrics: fan-in, fan-out, instability
-- Fan-out: count of distinct symbols this symbol calls
-- Fan-in: count of distinct symbols that call this symbol
-- Instability: fan_out / (fan_in + fan_out), 0 = stable, 1 = unstable

with symbols as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        symbol_name,
        symbol_type
    from {{ ref('stg_lz_code_symbols') }}
),
calls as (
    select
        run_pk,
        caller_file_id,
        caller_directory_id,
        caller_file_path,
        caller_symbol,
        callee_symbol,
        callee_file_id,
        callee_file_path
    from {{ ref('stg_lz_symbol_calls') }}
),
-- Fan-out: how many distinct symbols does each caller symbol call?
fan_out as (
    select
        run_pk,
        caller_symbol as symbol_name,
        caller_file_id as file_id,
        caller_directory_id as directory_id,
        caller_file_path as relative_path,
        count(distinct callee_symbol) as fan_out
    from calls
    group by run_pk, caller_symbol, caller_file_id, caller_directory_id, caller_file_path
),
-- Fan-in: how many distinct symbols call each callee symbol?
fan_in as (
    select
        run_pk,
        callee_symbol as symbol_name,
        callee_file_id as file_id,
        callee_file_path as relative_path,
        count(distinct caller_symbol) as fan_in
    from calls
    where callee_symbol is not null
    group by run_pk, callee_symbol, callee_file_id, callee_file_path
),
-- Combine fan-in and fan-out for all symbols
combined as (
    select
        coalesce(s.run_pk, fo.run_pk, fi.run_pk) as run_pk,
        coalesce(s.file_id, fo.file_id, fi.file_id) as file_id,
        coalesce(s.directory_id, fo.directory_id) as directory_id,
        coalesce(s.relative_path, fo.relative_path, fi.relative_path) as relative_path,
        coalesce(s.symbol_name, fo.symbol_name, fi.symbol_name) as symbol_name,
        s.symbol_type,
        coalesce(fo.fan_out, 0) as fan_out,
        coalesce(fi.fan_in, 0) as fan_in
    from symbols s
    full outer join fan_out fo
        on s.run_pk = fo.run_pk
        and s.symbol_name = fo.symbol_name
        and s.file_id = fo.file_id
    full outer join fan_in fi
        on coalesce(s.run_pk, fo.run_pk) = fi.run_pk
        and coalesce(s.symbol_name, fo.symbol_name) = fi.symbol_name
        and coalesce(s.file_id, fo.file_id) = fi.file_id
)
select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    symbol_name,
    symbol_type,
    fan_out,
    fan_in,
    fan_out + fan_in as total_coupling,
    case
        when fan_in + fan_out = 0 then 0.0
        else cast(fan_out as double) / (fan_in + fan_out)
    end as instability
from combined
where symbol_name is not null
