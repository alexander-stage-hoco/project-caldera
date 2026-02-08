-- Layout structure hotspots query
-- Uses mart_layout_structure_hotspots to identify directory organization issues
-- Resolves layout-scanner run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_layout.run_pk AS layout_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_layout
        ON tr_layout.collection_run_id = tr_scc.collection_run_id
        AND tr_layout.tool_name = 'layout-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    directory_path,
    depth,
    file_count_recursive,
    file_count_direct,
    total_size_bytes_recursive,
    total_size_bytes_direct,
    language_count,
    category_count,
    size_gini,
    size_palma,
    depth_rank,
    depth_zscore,
    file_rank,
    file_zscore,
    size_rank,
    size_zscore,
    risk_level,
    risk_level_numeric,
    is_deeply_nested,
    is_file_heavy,
    is_size_heavy,
    has_size_concentration,
    run_total_directories
FROM mart_layout_structure_hotspots
WHERE run_pk = (SELECT layout_run_pk FROM run_map)
ORDER BY risk_level_numeric DESC, depth DESC
LIMIT {{ limit | default(100) }}
