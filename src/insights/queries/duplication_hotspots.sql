-- Duplication hotspots query
-- Uses mart_pmd_cpd_clone_hotspots to identify code clones
-- Resolves pmd-cpd run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_cpd.run_pk AS cpd_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_cpd
        ON tr_cpd.collection_run_id = tr_scc.collection_run_id
        AND tr_cpd.tool_name = 'pmd-cpd'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    clone_id,
    lines,
    tokens,
    occurrence_count,
    is_cross_file,
    files_affected,
    directories_affected,
    total_duplicated_lines,
    token_density,
    impact_score,
    size_rank,
    occurrence_rank,
    impact_rank,
    spread_rank,
    risk_level
FROM mart_pmd_cpd_clone_hotspots
WHERE run_pk = (SELECT cpd_run_pk FROM run_map)
ORDER BY total_duplicated_lines DESC
LIMIT {{ limit | default(20) }}
