select *
from {{ ref('mart_git_fame_contributor_hotspots') }}
where
    -- WHERE clause contract: ownership_pct >= 10.0 OR is_bus_factor_member OR ownership_zscore > 2.0
    not (ownership_pct >= 10.0 or is_bus_factor_member or ownership_zscore > 2.0)

    -- ownership_pct bounded 0-100
    or ownership_pct < 0
    or ownership_pct > 100

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and ownership_pct < 50.0)
    or (risk_level = 'high' and (ownership_pct < 25.0 or ownership_pct >= 50.0))
    or (risk_level = 'medium' and (ownership_pct < 10.0 or ownership_pct >= 25.0))
    or (risk_level = 'low' and (ownership_pct < 5.0 or ownership_pct >= 10.0))
    or (risk_level = 'minimal' and ownership_pct >= 5.0)

    -- risk_level_numeric matches risk_level
    or (risk_level = 'critical' and risk_level_numeric != 5)
    or (risk_level = 'high' and risk_level_numeric != 4)
    or (risk_level = 'medium' and risk_level_numeric != 3)
    or (risk_level = 'low' and risk_level_numeric != 2)
    or (risk_level = 'minimal' and risk_level_numeric != 1)

    -- Positive activity counts
    or commit_count < 1
    or files_touched < 1

    -- Rank columns >= 1
    or ownership_rank < 1
    or commit_rank < 1
    or files_rank < 1

    -- cumulative_ownership_pct bounded 0-100
    or cumulative_ownership_pct < 0
    or cumulative_ownership_pct > 100
