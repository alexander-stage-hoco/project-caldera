-- Dependency health summary query
-- Uses mart_dependency_health_summary to get overall health grade and metrics
-- Resolves dependensee run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_dep.run_pk AS dep_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_dep
        ON tr_dep.collection_run_id = tr_scc.collection_run_id
        AND tr_dep.tool_name = 'dependensee'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
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
    health_grade,
    recommendations
FROM mart_dependency_health_summary
WHERE run_pk = (SELECT dep_run_pk FROM run_map)
