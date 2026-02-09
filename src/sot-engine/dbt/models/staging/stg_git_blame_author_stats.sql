-- Staging model for git-blame-scanner author statistics
-- Per-author aggregate metrics for knowledge distribution analysis

SELECT
    run_pk,
    author_email,
    total_files,
    total_lines,
    exclusive_files,
    avg_ownership_pct,
    -- Derived fields
    CASE WHEN exclusive_files > 0 THEN true ELSE false END AS has_exclusive_files,
    CASE WHEN avg_ownership_pct >= 80 THEN true ELSE false END AS is_dominant_owner,
    CASE
        WHEN exclusive_files = total_files THEN 'sole_contributor'
        WHEN avg_ownership_pct >= 80 THEN 'dominant'
        WHEN avg_ownership_pct >= 50 THEN 'major'
        ELSE 'minor'
    END AS contributor_type
FROM {{ source('lz', 'lz_git_blame_author_stats') }}
