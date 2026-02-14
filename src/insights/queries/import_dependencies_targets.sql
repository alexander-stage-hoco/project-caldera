-- Most-imported targets query
-- Identifies files that are imported by the most other files
-- These are the files where breaking changes would ripple through the codebase

WITH run_map AS (
    SELECT tr_symbol.run_pk AS symbol_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_symbol
        ON tr_symbol.collection_run_id = tr_scc.collection_run_id
        AND tr_symbol.tool_name = 'symbol-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    imported_path,
    COUNT(*) AS reference_count,
    COUNT(DISTINCT relative_path) AS importing_files
FROM stg_lz_file_imports
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
    AND imported_path IS NOT NULL
GROUP BY imported_path
ORDER BY importing_files DESC, reference_count DESC
LIMIT {{ limit | default(30) }}
