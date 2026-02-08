-- Contributor hotspots query
-- Uses mart_git_fame_contributor_hotspots for individual contributor metrics
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
    author_name,
    author_email,
    surviving_loc,
    ownership_pct,
    insertions_total,
    deletions_total,
    commit_count,
    files_touched,
    ownership_rank,
    commit_rank,
    files_rank,
    cumulative_ownership_pct,
    risk_level,
    risk_level_numeric,
    is_bus_factor_member,
    ownership_zscore,
    relative_position,
    code_retention_ratio,
    churn_ratio,
    is_significant_contributor,
    is_high_plus,
    is_critical,
    run_ownership_avg,
    run_ownership_stddev,
    run_ownership_p50,
    run_ownership_p90
FROM mart_git_fame_contributor_hotspots
WHERE run_pk = (SELECT fame_run_pk FROM run_map)
ORDER BY ownership_pct DESC
LIMIT {{ limit | default(15) }}
