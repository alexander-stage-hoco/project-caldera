-- License compliance summary query
-- Uses mart_scancode_license_hotspots to identify license types and compliance risks
-- Resolves scancode run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_scan.run_pk AS scan_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_scan
        ON tr_scan.collection_run_id = tr_scc.collection_run_id
        AND tr_scan.tool_name = 'scancode'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    spdx_id,
    category,
    detection_count,
    files_affected,
    directories_affected,
    avg_confidence,
    min_confidence,
    max_confidence,
    category_permissive,
    category_weak_copyleft,
    category_copyleft,
    category_unknown,
    detection_rank,
    spread_rank,
    risk_level
FROM mart_scancode_license_hotspots
WHERE run_pk = (SELECT scan_run_pk FROM run_map)
ORDER BY detection_rank ASC
