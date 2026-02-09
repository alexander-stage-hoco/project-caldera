-- Staging model for git-blame-scanner file summaries
-- Per-file authorship metrics for knowledge concentration analysis

SELECT
    run_pk,
    file_id,
    directory_id,
    relative_path,
    total_lines,
    unique_authors,
    top_author,
    top_author_lines,
    top_author_pct,
    last_modified,
    churn_30d,
    churn_90d,
    -- Derived fields
    CASE WHEN unique_authors = 1 THEN true ELSE false END AS is_single_author,
    CASE WHEN top_author_pct >= 80 THEN true ELSE false END AS is_high_concentration,
    CASE WHEN unique_authors = 1 AND total_lines > 100 THEN true ELSE false END AS is_knowledge_silo,
    CASE WHEN churn_90d = 0 THEN true ELSE false END AS is_stale
FROM {{ source('lz', 'lz_git_blame_summary') }}
