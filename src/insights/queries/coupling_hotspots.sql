-- Symbol coupling hotspots query
-- Uses mart_symbol_coupling_hotspots to identify architectural coupling patterns
-- Resolves symbol-scanner run_pk from SCC's collection

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
    coupling_risk_numeric,
    instability_zone,
    coupling_pattern,
    coupling_zscore,
    relative_position,
    is_rigid_dependency,
    is_unstable_dependency,
    is_medium_plus,
    is_high_plus,
    is_critical,
    run_coupling_avg,
    run_coupling_stddev,
    run_coupling_p50,
    run_coupling_p90,
    run_fan_in_avg,
    run_fan_out_avg,
    run_total_symbols
FROM mart_symbol_coupling_hotspots
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
ORDER BY total_coupling DESC
LIMIT {{ limit | default(25) }}
