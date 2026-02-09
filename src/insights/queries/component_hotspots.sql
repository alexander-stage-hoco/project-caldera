-- Component hotspots query
-- Identifies high-CCN files within each component directory
-- Used to surface complexity hotspots per component

WITH run_map AS (
    -- Resolve tool-specific run_pks from collection
    SELECT
        tr_layout.run_pk AS layout_run_pk,
        tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_layout
        ON tr_layout.collection_run_id = tr_scc.collection_run_id
        AND tr_layout.tool_name IN ('layout', 'layout-scanner')
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.tool_name = 'scc'
      AND tr_scc.run_pk = {{ run_pk }}
),
-- Get component directories (depth 1-2)
component_dirs AS (
    SELECT
        directory_id,
        relative_path AS component_path,
        depth
    FROM lz_layout_directories ld
    JOIN run_map rm ON rm.layout_run_pk = ld.run_pk
    WHERE ld.depth BETWEEN 1 AND 2
      AND ld.file_count > 0
      -- Filter out non-code directories
      AND ld.relative_path NOT LIKE 'test%'
      AND ld.relative_path NOT LIKE 'tests%'
      AND ld.relative_path NOT LIKE '%/test%'
      AND ld.relative_path NOT LIKE '%/tests%'
      AND ld.relative_path NOT LIKE 'docs%'
      AND ld.relative_path NOT LIKE '.%'
      AND ld.relative_path NOT LIKE 'node_modules%'
      AND ld.relative_path NOT LIKE 'vendor%'
),
-- Map files to components based on directory containment
file_to_component AS (
    SELECT
        lf.file_id,
        lf.relative_path AS file_path,
        cd.directory_id AS component_id,
        cd.component_path
    FROM lz_layout_files lf
    JOIN run_map rm ON rm.layout_run_pk = lf.run_pk
    JOIN component_dirs cd ON lf.directory_id = cd.directory_id
       OR lf.relative_path LIKE cd.component_path || '/%'
),
-- Get file-level complexity from lizard
file_complexity AS (
    SELECT
        lm.file_id,
        lm.relative_path,
        lm.total_ccn,
        lm.avg_ccn,
        lm.max_ccn,
        lm.function_count,
        lm.nloc
    FROM lz_lizard_file_metrics lm
    WHERE lm.run_pk = (SELECT lizard_run_pk FROM run_map)
      AND lm.total_ccn > 0
),
-- Join to get component-level hotspots
component_hotspots AS (
    SELECT
        fc.component_id,
        fc.component_path,
        fcomp.file_id,
        fcomp.relative_path AS file_path,
        fcomp.total_ccn,
        fcomp.avg_ccn,
        fcomp.max_ccn,
        fcomp.function_count,
        fcomp.nloc,
        -- Classify hotspot type
        CASE
            WHEN fcomp.max_ccn > 30 THEN 'critical_complexity'
            WHEN fcomp.max_ccn > 20 THEN 'high_complexity'
            WHEN fcomp.max_ccn > 10 THEN 'moderate_complexity'
            ELSE 'normal'
        END AS hotspot_type,
        -- Rank within component
        ROW_NUMBER() OVER (
            PARTITION BY fc.component_id
            ORDER BY fcomp.total_ccn DESC
        ) AS rank_in_component
    FROM file_to_component fc
    JOIN file_complexity fcomp ON fcomp.file_id = fc.file_id
)
SELECT
    component_id,
    component_path,
    file_id,
    file_path,
    total_ccn,
    ROUND(avg_ccn, 1) AS avg_ccn,
    max_ccn,
    function_count,
    nloc,
    hotspot_type,
    rank_in_component
FROM component_hotspots
WHERE rank_in_component <= 3  -- Top 3 hotspots per component
  AND hotspot_type != 'normal'  -- Only actual hotspots
ORDER BY component_path, rank_in_component
