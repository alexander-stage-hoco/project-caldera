-- Authorship summary query
-- Uses mart_authorship_summary for repository-level metrics
-- Resolves git-fame run_pk from SCC's collection

WITH run_map AS (
    SELECT tr_fame.run_pk AS fame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_fame
        ON tr_fame.collection_run_id = tr_scc.collection_run_id
        AND tr_fame.tool_name = 'git-fame'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    author_count,
    bus_factor,
    top_author_pct,
    top_two_pct,
    hhi_index,
    total_loc,
    total_files,
    total_code,
    total_complexity,
    avg_complexity,
    max_complexity,
    concentration_risk,
    bus_factor_risk,
    single_author_dominated
FROM mart_authorship_summary
WHERE run_pk = (SELECT fame_run_pk FROM run_map)
