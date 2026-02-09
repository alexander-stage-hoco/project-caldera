-- Knowledge risk hotspots - file-level knowledge concentration analysis
-- Identifies files at risk due to knowledge silos or high ownership concentration
-- Uses mart_git_blame_knowledge_risk for risk scoring

-- Resolve git-blame-scanner run_pk from SCC's collection
WITH run_map AS (
    SELECT tr_blame.run_pk AS blame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_blame
        ON tr_blame.collection_run_id = tr_scc.collection_run_id
        AND tr_blame.tool_name = 'git-blame-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
)
SELECT
    relative_path,
    total_lines,
    unique_authors,
    top_author,
    top_author_pct,
    last_modified,
    churn_30d,
    churn_90d,
    is_single_author,
    is_high_concentration,
    is_knowledge_silo,
    is_stale,
    risk_score,
    risk_level
FROM mart_git_blame_knowledge_risk
WHERE run_pk = (SELECT blame_run_pk FROM run_map)
ORDER BY risk_score DESC
LIMIT {{ limit | default(30) }}
