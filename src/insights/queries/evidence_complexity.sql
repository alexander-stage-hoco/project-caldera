-- Evidence: complexity hotspots
-- Finds files with max_ccn >= 15 from unified_file_metrics
-- Used by EvidenceCollector to populate complexity evidence items

WITH run_map AS (
    SELECT
        tr_scc.run_pk AS scc_run_pk,
        tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    ufm.relative_path,
    ufm.loc_total,
    ufm.max_ccn,
    ufm.total_ccn,
    ufm.function_count,
    ROUND(ufm.total_ccn * 1.0 / NULLIF(ufm.function_count, 0), 1) AS avg_ccn,
    (SELECT lizard_run_pk FROM run_map) AS tool_run_pk
FROM unified_file_metrics ufm
WHERE ufm.run_pk = (SELECT scc_run_pk FROM run_map)
  AND ufm.max_ccn >= {{ threshold | default(15) }}
ORDER BY ufm.max_ccn DESC
LIMIT {{ limit | default(100) }}
