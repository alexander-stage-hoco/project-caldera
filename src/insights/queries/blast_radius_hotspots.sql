-- Blast radius hotspots query
-- Uses mart_project_blast_radius to identify projects with high change impact
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
    target_project,
    target_project_path,
    blast_radius_projects,
    blast_radius_depth,
    total_paths,
    blast_radius_risk
FROM mart_project_blast_radius
WHERE run_pk = (SELECT dep_run_pk FROM run_map)
ORDER BY blast_radius_projects DESC, blast_radius_depth DESC
LIMIT {{ limit | default(20) }}
