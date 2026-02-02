-- Complex files in directories with vulnerabilities for Caldera
-- Links complexity hotspots to vulnerability-affected directories
-- Uses rollup_trivy_directory_counts_recursive for directory-level vuln counts
-- Joins via collection_run_id to find related trivy run

WITH trivy_run AS (
    -- Find the trivy run_pk for the same collection
    SELECT tr_trivy.run_pk
    FROM lz_tool_runs tr_source
    JOIN lz_tool_runs tr_trivy
        ON tr_trivy.collection_run_id = tr_source.collection_run_id
        AND tr_trivy.tool_name = 'trivy'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT DISTINCT
    ufm.relative_path,
    ufm.complexity_total_ccn AS complexity,
    ufm.loc_total AS loc,
    rv.total_vulnerability_count AS vulnerability_count,
    lf.language
FROM unified_file_metrics ufm
INNER JOIN stg_lz_layout_files lf
    ON ufm.layout_run_pk = lf.run_pk AND ufm.file_id = lf.file_id
INNER JOIN rollup_trivy_directory_counts_recursive rv
    ON rv.run_pk = (SELECT run_pk FROM trivy_run)
    AND ufm.directory_id = rv.directory_id
    AND rv.total_vulnerability_count > 0
WHERE ufm.run_pk = {{ run_pk }}
  AND ufm.complexity_total_ccn >= 15
ORDER BY ufm.complexity_total_ccn DESC
LIMIT {{ limit | default(15) }}
