select *
from {{ ref('mart_author_contributions') }}
where
    -- ownership_pct bounded 0-100
    ownership_pct < 0
    or ownership_pct > 100

    -- contribution_rank >= 1
    or contribution_rank < 1

    -- Positive activity counts
    or commit_count < 1
    or files_touched < 1

    -- contribution_tier valid values
    or contribution_tier not in ('top_10_pct', 'top_25_pct', 'top_50_pct', 'bottom_50_pct')

    -- commitment_index non-negative when present
    or (commitment_index is not null and commitment_index < 0)

    -- churn_ratio non-negative when present
    or (churn_ratio is not null and churn_ratio < 0)
