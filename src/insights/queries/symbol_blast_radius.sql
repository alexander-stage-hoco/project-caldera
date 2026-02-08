-- Symbol blast radius query
-- Uses mart_blast_radius_symbol to identify high-impact symbols
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
    target_symbol,
    target_file_path,
    blast_radius_symbols,
    blast_radius_files,
    max_depth,
    min_depth,
    total_paths,
    blast_radius_risk
FROM mart_blast_radius_symbol
WHERE run_pk = (SELECT symbol_run_pk FROM run_map)
ORDER BY blast_radius_symbols DESC, max_depth DESC
LIMIT {{ limit | default(30) }}
