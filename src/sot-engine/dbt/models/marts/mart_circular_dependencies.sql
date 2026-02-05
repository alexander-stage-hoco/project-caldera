-- Circular dependency detection in import graph
-- Identifies cycles where file A imports B imports C imports A
-- Uses recursive CTE to follow import chains and detect when chain returns to starting file

with recursive imports as (
    select
        run_pk,
        file_id,
        relative_path as source_file,
        imported_path as target_file,
        import_type
    from {{ ref('stg_lz_file_imports') }}
    where imported_path is not null
),
-- Build import chain and detect cycles
import_chain as (
    -- Base case: start from each file's imports
    select
        run_pk,
        source_file as start_file,
        file_id as start_file_id,
        source_file,
        target_file,
        1 as depth,
        source_file || ' -> ' || target_file as path,
        false as is_cycle
    from imports

    union all

    -- Recursive case: follow the import chain
    select
        i.run_pk,
        ic.start_file,
        ic.start_file_id,
        i.source_file,
        i.target_file,
        ic.depth + 1 as depth,
        ic.path || ' -> ' || i.target_file as path,
        i.target_file = ic.start_file as is_cycle
    from imports i
    join import_chain ic
        on i.run_pk = ic.run_pk
        and i.source_file = ic.target_file
    where ic.depth < 10  -- Limit recursion depth
        and not ic.is_cycle  -- Stop if already found cycle
        and position(i.target_file in ic.path) = 0  -- Avoid revisiting nodes (except to detect cycle back to start)
            or i.target_file = ic.start_file  -- Allow detecting cycle back to start
),
-- Filter to only cycles (where chain returns to starting file)
cycles as (
    select
        run_pk,
        start_file,
        start_file_id,
        path || ' -> ' || start_file as cycle_path,
        depth + 1 as cycle_length
    from import_chain
    where is_cycle
)
select
    run_pk,
    start_file,
    start_file_id,
    cycle_path,
    cycle_length,
    -- Severity based on cycle length (shorter = more tightly coupled = worse)
    case
        when cycle_length = 2 then 'critical'  -- Direct bidirectional dependency
        when cycle_length <= 4 then 'high'
        when cycle_length <= 6 then 'medium'
        else 'low'
    end as severity
from cycles
