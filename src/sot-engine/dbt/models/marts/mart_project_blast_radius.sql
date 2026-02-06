-- Blast radius analysis: transitive dependents of each .NET project
-- Answers: "What projects are affected if I change project X?"
-- Uses recursive CTE to find all projects that depend on the target (reverse dependency direction)

with recursive project_refs as (
    select
        run_pk,
        source_project_path,
        target_project_path
    from {{ ref('stg_dependensee_project_refs') }}
    where target_project_path is not null
),
projects as (
    select
        run_pk,
        project_path,
        project_name
    from {{ ref('stg_dependensee_projects') }}
),
-- Build transitive dependent chain for each project
-- Direction: find all projects that depend on target (reverse of ref direction)
ref_chain as (
    -- Base case: direct dependents of each project
    select
        r.run_pk,
        r.target_project_path as target_project,
        r.source_project_path as affected_project,
        1 as depth,
        r.source_project_path as path  -- Track path for cycle detection
    from project_refs r

    union all

    -- Recursive case: dependents of dependents
    select
        r.run_pk,
        rc.target_project,
        r.source_project_path as affected_project,
        rc.depth + 1 as depth,
        rc.path || ' -> ' || r.source_project_path as path
    from project_refs r
    join ref_chain rc
        on r.run_pk = rc.run_pk
        and r.target_project_path = rc.affected_project
    where rc.depth < 10  -- Limit recursion depth
        and position(r.source_project_path in rc.path) = 0  -- Cycle detection
),
-- Aggregate blast radius per target project
blast_radius as (
    select
        run_pk,
        target_project,
        count(distinct affected_project) as blast_radius_projects,
        max(depth) as blast_radius_depth,
        count(*) as total_paths
    from ref_chain
    group by run_pk, target_project
)
select
    br.run_pk,
    p.project_name as target_project,
    br.target_project as target_project_path,
    br.blast_radius_projects,
    br.blast_radius_depth,
    br.total_paths,
    -- Risk classification based on blast radius
    case
        when br.blast_radius_projects >= 10 then 'critical'
        when br.blast_radius_projects >= 5 then 'high'
        when br.blast_radius_projects >= 3 then 'medium'
        else 'low'
    end as blast_radius_risk
from blast_radius br
left join projects p
    on br.run_pk = p.run_pk
    and br.target_project = p.project_path
