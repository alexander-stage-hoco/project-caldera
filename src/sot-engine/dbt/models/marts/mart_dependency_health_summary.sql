-- Repository-level dependency health summary for .NET projects
-- Aggregates metrics from dependensee analysis into a single health assessment

with project_stats as (
    select
        run_pk,
        count(*) as total_projects,
        sum(project_reference_count) as total_project_refs,
        sum(package_reference_count) as total_package_refs,
        avg(package_reference_count) as avg_packages_per_project
    from {{ ref('stg_dependensee_projects') }}
    group by run_pk
),
package_stats as (
    select
        run_pk,
        count(distinct package_name) as unique_packages
    from {{ ref('stg_dependensee_package_refs') }}
    group by run_pk
),
cycle_stats as (
    select
        run_pk,
        count(*) as circular_dependency_count,
        sum(case when severity = 'critical' then 1 else 0 end) as critical_cycles,
        sum(case when severity = 'high' then 1 else 0 end) as high_cycles
    from {{ ref('mart_project_dependency_cycles') }}
    group by run_pk
),
conflict_stats as (
    select
        run_pk,
        count(*) as version_conflict_count,
        sum(case when conflict_severity = 'critical' then 1 else 0 end) as critical_conflicts,
        sum(case when conflict_severity = 'high' then 1 else 0 end) as high_conflicts
    from {{ ref('mart_package_version_conflicts') }}
    group by run_pk
),
blast_stats as (
    select
        run_pk,
        max(blast_radius_projects) as max_blast_radius,
        avg(blast_radius_projects) as avg_blast_radius
    from {{ ref('mart_project_blast_radius') }}
    group by run_pk
),
-- Combine all stats
combined as (
    select
        ps.run_pk,
        ps.total_projects,
        ps.total_project_refs,
        ps.total_package_refs,
        coalesce(pkg.unique_packages, 0) as unique_packages,
        round(ps.avg_packages_per_project, 2) as avg_packages_per_project,
        coalesce(cs.circular_dependency_count, 0) as circular_dependency_count,
        coalesce(cs.critical_cycles, 0) as critical_cycles,
        coalesce(cs.high_cycles, 0) as high_cycles,
        coalesce(cf.version_conflict_count, 0) as version_conflict_count,
        coalesce(cf.critical_conflicts, 0) as critical_conflicts,
        coalesce(cf.high_conflicts, 0) as high_conflicts,
        coalesce(bs.max_blast_radius, 0) as max_blast_radius,
        round(coalesce(bs.avg_blast_radius, 0), 2) as avg_blast_radius
    from project_stats ps
    left join package_stats pkg on ps.run_pk = pkg.run_pk
    left join cycle_stats cs on ps.run_pk = cs.run_pk
    left join conflict_stats cf on ps.run_pk = cf.run_pk
    left join blast_stats bs on ps.run_pk = bs.run_pk
)
select
    run_pk,
    total_projects,
    total_project_refs,
    total_package_refs,
    unique_packages,
    avg_packages_per_project,
    circular_dependency_count,
    critical_cycles,
    high_cycles,
    version_conflict_count,
    critical_conflicts,
    high_conflicts,
    max_blast_radius,
    avg_blast_radius,
    -- Health grade calculation (A-F)
    case
        when critical_cycles > 0 or critical_conflicts > 2 then 'F'
        when high_cycles > 0 or critical_conflicts > 0 or high_conflicts > 3 then 'D'
        when circular_dependency_count > 0 or high_conflicts > 0 or max_blast_radius >= 10 then 'C'
        when version_conflict_count > 2 or max_blast_radius >= 5 then 'B'
        else 'A'
    end as health_grade,
    -- Actionable recommendations
    case
        when critical_cycles > 0 then 'URGENT: Resolve ' || critical_cycles || ' critical circular dependency cycle(s) immediately'
        when high_cycles > 0 then 'HIGH: Address ' || high_cycles || ' high-severity circular dependencies'
        when circular_dependency_count > 0 then 'MODERATE: Review ' || circular_dependency_count || ' circular dependency cycle(s)'
        when critical_conflicts > 0 then 'HIGH: Consolidate package versions to resolve ' || critical_conflicts || ' critical version conflict(s)'
        when version_conflict_count > 0 then 'MODERATE: Consider consolidating ' || version_conflict_count || ' package version conflict(s)'
        when max_blast_radius >= 10 then 'INFO: Review high-impact projects with blast radius >= 10'
        else 'Repository dependency health is good'
    end as recommendations
from combined
