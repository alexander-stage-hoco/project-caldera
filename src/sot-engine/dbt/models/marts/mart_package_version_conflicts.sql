-- NuGet package version conflict detection
-- Identifies packages used with multiple versions across projects in the same repository
-- Version conflicts can cause runtime issues and build failures

with package_versions as (
    select
        run_pk,
        package_name,
        package_version,
        project_path
    from {{ ref('stg_dependensee_package_refs') }}
    where package_name is not null
        and package_version is not null
),
-- Aggregate versions per package
package_aggregates as (
    select
        run_pk,
        package_name,
        count(distinct package_version) as version_count,
        string_agg(distinct package_version, ', ' order by package_version) as versions_list,
        count(distinct project_path) as projects_affected,
        string_agg(distinct project_path, ', ' order by project_path) as affected_projects
    from package_versions
    group by run_pk, package_name
    having count(distinct package_version) > 1
)
select
    run_pk,
    package_name,
    version_count,
    versions_list,
    projects_affected,
    affected_projects,
    -- Severity based on number of conflicting versions and affected projects
    case
        when version_count >= 4 then 'critical'
        when version_count >= 3 or projects_affected >= 5 then 'high'
        when version_count = 2 and projects_affected >= 3 then 'medium'
        else 'low'
    end as conflict_severity
from package_aggregates
order by version_count desc, projects_affected desc
