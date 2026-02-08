-- Function complexity hotspots query
-- Uses mart_complexity_hotspots to identify high-CCN functions
-- Resolves lizard run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_lizard.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_lizard
        ON tr_lizard.collection_run_id = tr_scc.collection_run_id
        AND tr_lizard.tool_name = 'lizard'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    relative_path,
    function_name,
    long_name,
    ccn,
    nloc,
    params AS parameter_count,
    token_count,
    line_start,
    line_end,
    line_span,
    complexity_density,
    risk_level,
    risk_level_numeric,
    relative_position,
    ccn_zscore,
    is_medium_plus,
    is_high_plus,
    is_critical,
    run_ccn_avg,
    run_ccn_stddev,
    run_ccn_p50,
    run_ccn_p75,
    run_ccn_p90,
    run_ccn_p95,
    run_ccn_p99,
    run_total_functions
FROM mart_complexity_hotspots
WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
ORDER BY ccn DESC
LIMIT {{ limit | default(30) }}
