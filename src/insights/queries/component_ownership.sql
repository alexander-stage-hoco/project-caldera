-- Component ownership: git-blame aggregation per component directory
-- Enriches component inventory with ownership risk signals

WITH run_map AS (
    SELECT tr_blame.run_pk AS blame_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_blame
        ON tr_blame.collection_run_id = tr_scc.collection_run_id
        AND tr_blame.tool_name = 'git-blame-scanner'
    WHERE tr_scc.run_pk = {{ run_pk }}
),
blame_data AS (
    SELECT
        relative_path,
        unique_authors,
        top_author,
        top_author_pct,
        total_lines,
        risk_level
    FROM mart_git_blame_knowledge_risk
    WHERE run_pk = (SELECT blame_run_pk FROM run_map)
),
dir_ownership AS (
    SELECT
        CASE
            WHEN POSITION('/' IN relative_path) > 0
            THEN SPLIT_PART(relative_path, '/', 1)
            ELSE '.'
        END AS directory_path,
        ROUND(AVG(unique_authors), 1) AS avg_unique_authors,
        COUNT(CASE WHEN unique_authors = 1 AND total_lines > 200 THEN 1 END) AS knowledge_silo_count,
        ROUND(AVG(top_author_pct), 1) AS avg_top_author_pct,
        COUNT(CASE WHEN risk_level IN ('critical', 'high') THEN 1 END) AS high_risk_file_count,
        COUNT(*) AS total_files
    FROM blame_data
    GROUP BY 1
)
SELECT
    directory_path,
    avg_unique_authors,
    knowledge_silo_count,
    avg_top_author_pct,
    high_risk_file_count,
    total_files
FROM dir_ownership
ORDER BY knowledge_silo_count DESC, avg_top_author_pct DESC
