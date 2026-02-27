-- Evidence: ownership / knowledge risk
-- Finds files with risk_level critical/high from mart_git_blame_knowledge_risk
-- Used by EvidenceCollector to populate ownership evidence items

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
    unique_authors,
    top_author,
    top_author_pct,
    total_lines,
    risk_level,
    (SELECT blame_run_pk FROM run_map) AS tool_run_pk
FROM mart_git_blame_knowledge_risk
WHERE run_pk = (SELECT blame_run_pk FROM run_map)
  AND risk_level IN ('critical', 'high')
ORDER BY
    CASE risk_level WHEN 'critical' THEN 1 WHEN 'high' THEN 2 END,
    top_author_pct DESC
LIMIT {{ limit | default(50) }}
