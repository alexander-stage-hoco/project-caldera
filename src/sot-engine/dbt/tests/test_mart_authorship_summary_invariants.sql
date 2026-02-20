select *
from {{ ref('mart_authorship_summary') }}
where
    -- author_count non-negative, total_loc non-negative
    author_count < 0
    or total_loc < 0

    -- hhi_index bounded 0.0-1.0
    or hhi_index < 0.0
    or hhi_index > 1.0

    -- bus_factor non-negative
    or bus_factor < 0

    -- top_author_pct bounded 0-100
    or top_author_pct < 0
    or top_author_pct > 100

    -- concentration_risk thresholds match CASE logic
    or (concentration_risk = 'high' and hhi_index < 0.5)
    or (concentration_risk = 'medium' and (hhi_index < 0.25 or hhi_index >= 0.5))
    or (concentration_risk = 'low' and hhi_index >= 0.25)

    -- bus_factor_risk thresholds match CASE logic
    or (bus_factor_risk = 'critical' and bus_factor > 1)
    or (bus_factor_risk = 'warning' and (bus_factor <= 1 or bus_factor > 2))
    or (bus_factor_risk = 'healthy' and bus_factor <= 2)

    -- single_author_dominated consistency: true iff top_author_pct >= 80
    or (single_author_dominated and top_author_pct < 80.0)
    or (not single_author_dominated and top_author_pct >= 80.0)
