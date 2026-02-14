-- Circular dependencies query
-- Uses mart_circular_dependencies to surface file-level import cycles
-- Resolves symbol-scanner run_pk from the collection

WITH run_map AS (
    SELECT tr_symbol.run_pk AS symbol_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    start_file,
    cycle_path,
    cycle_length,
    severity
FROM mart_circular_dependencies
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
ORDER BY
    CASE severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    cycle_length ASC
