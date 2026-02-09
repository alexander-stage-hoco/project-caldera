-- Git-blame-scanner file authorship distributions per directory (direct scope)
-- Provides distribution statistics on authorship concentration, churn, and lines

{{ calculate_distribution_stats(
    tool_name='git-blame-scanner',
    scope='direct',
    metrics_table='lz_git_blame_summary',
    metrics=['total_lines', 'unique_authors', 'top_author_pct', 'churn_30d', 'churn_90d']
) }}
