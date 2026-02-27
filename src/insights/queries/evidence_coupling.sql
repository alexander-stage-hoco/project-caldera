-- Evidence: coupling hotspots
-- Finds symbols with coupling_risk critical/high from mart_symbol_coupling_hotspots
-- Used by EvidenceCollector to populate coupling evidence items

WITH run_map AS (
    SELECT tr_symbol.run_pk AS symbol_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    symbol_name,
    symbol_type,
    relative_path,
    fan_in,
    fan_out,
    total_coupling,
    instability,
    coupling_risk,
    coupling_pattern,
    (SELECT symbol_run_pk FROM run_map) AS tool_run_pk
FROM mart_symbol_coupling_hotspots
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
  AND coupling_risk IN ('critical', 'high')
ORDER BY total_coupling DESC
LIMIT {{ limit | default(50) }}
