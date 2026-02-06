-- Circular dependency detection in .NET project reference graph
-- Identifies cycles where Project A references B references C references A
-- Uses recursive CTE to follow reference chains and detect when chain returns to starting project

with recursive project_refs as (
    select
        run_pk,
        source_project_path,
        target_project_path
    from {{ ref('stg_dependensee_project_refs') }}
    where target_project_path is not null
),
-- Build reference chain and detect cycles
ref_chain as (
    -- Base case: start from each project's references
    select
        run_pk,
        source_project_path as start_project,
        source_project_path,
        target_project_path,
        1 as depth,
        source_project_path || ' -> ' || target_project_path as path,
        false as is_cycle
    from project_refs

    union all

    -- Recursive case: follow the reference chain
    select
        r.run_pk,
        rc.start_project,
        r.source_project_path,
        r.target_project_path,
        rc.depth + 1 as depth,
        rc.path || ' -> ' || r.target_project_path as path,
        r.target_project_path = rc.start_project as is_cycle
    from project_refs r
    join ref_chain rc
        on r.run_pk = rc.run_pk
        and r.source_project_path = rc.target_project_path
    where rc.depth < 10  -- Limit recursion depth
        and not rc.is_cycle  -- Stop if already found cycle
        and (position(r.target_project_path in rc.path) = 0  -- Avoid revisiting nodes
            or r.target_project_path = rc.start_project)  -- Allow detecting cycle back to start
),
-- Filter to only cycles (where chain returns to starting project)
cycles as (
    select
        run_pk,
        start_project,
        path || ' -> ' || start_project as cycle_path,
        depth + 1 as cycle_length
    from ref_chain
    where is_cycle
)
select
    run_pk,
    start_project,
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
