-- Import dependencies query
-- Uses stg_file_imports_file_metrics for file-level import patterns
-- and stg_lz_file_imports for most-imported targets
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
    relative_path,
    import_count,
    unique_imports,
    static_import_count,
    dynamic_import_count,
    side_effect_import_count
FROM stg_file_imports_file_metrics
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
ORDER BY import_count DESC
LIMIT {{ limit | default(30) }}
