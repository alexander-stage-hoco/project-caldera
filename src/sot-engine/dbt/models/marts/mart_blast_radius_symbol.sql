-- Blast radius analysis: transitive callers of each symbol
-- Answers: "What is the impact if I change function X?"
-- Uses recursive CTE to find all symbols that would be affected by changes

with recursive calls as (
    select
        run_pk,
        caller_file_id,
        caller_file_path,
        caller_symbol,
        callee_symbol,
        callee_file_id,
        callee_file_path
    from {{ ref('stg_lz_symbol_calls') }}
    where callee_symbol is not null
),
-- Build transitive caller chain for each symbol
call_chain as (
    -- Base case: direct callers of each symbol
    select
        run_pk,
        callee_symbol as target_symbol,
        callee_file_id as target_file_id,
        callee_file_path as target_file_path,
        caller_symbol as affected_symbol,
        caller_file_id as affected_file_id,
        caller_file_path as affected_file_path,
        1 as depth,
        caller_symbol as path  -- Track path for cycle detection
    from calls

    union all

    -- Recursive case: callers of callers
    select
        c.run_pk,
        cc.target_symbol,
        cc.target_file_id,
        cc.target_file_path,
        c.caller_symbol as affected_symbol,
        c.caller_file_id as affected_file_id,
        c.caller_file_path as affected_file_path,
        cc.depth + 1 as depth,
        cc.path || ' -> ' || c.caller_symbol as path
    from calls c
    join call_chain cc
        on c.run_pk = cc.run_pk
        and c.callee_symbol = cc.affected_symbol
    where cc.depth < 5  -- Limit recursion depth
        and position(c.caller_symbol in cc.path) = 0  -- Cycle detection
),
-- Aggregate blast radius per target symbol
blast_radius as (
    select
        run_pk,
        target_symbol,
        target_file_id,
        target_file_path,
        count(distinct affected_symbol) as blast_radius_symbols,
        count(distinct affected_file_id) as blast_radius_files,
        max(depth) as max_depth,
        min(depth) as min_depth,
        count(*) as total_paths
    from call_chain
    group by run_pk, target_symbol, target_file_id, target_file_path
)
select
    run_pk,
    target_symbol,
    target_file_id,
    target_file_path,
    blast_radius_symbols,
    blast_radius_files,
    max_depth,
    min_depth,
    total_paths,
    -- Risk classification based on blast radius
    case
        when blast_radius_symbols >= 20 then 'critical'
        when blast_radius_symbols >= 10 then 'high'
        when blast_radius_symbols >= 5 then 'medium'
        else 'low'
    end as blast_radius_risk
from blast_radius
