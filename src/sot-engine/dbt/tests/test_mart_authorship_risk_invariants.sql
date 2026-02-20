select *
from {{ ref('mart_authorship_risk') }}
where
    -- hhi_index bounded 0.0-1.0
    hhi_index < 0.0
    or hhi_index > 1.0

    -- bus_factor non-negative, author_count non-negative
    or bus_factor < 0
    or author_count < 0

    -- top_author_pct bounded 0-100
    or top_author_pct < 0
    or top_author_pct > 100

    -- top_two_pct bounded 0-100
    or top_two_pct < 0
    or top_two_pct > 100

    -- concentration_level thresholds match CASE logic
    or (concentration_level = 'highly_concentrated' and hhi_index < 0.5)
    or (concentration_level = 'moderately_concentrated' and (hhi_index < 0.25 or hhi_index >= 0.5))
    or (concentration_level = 'slightly_concentrated' and (hhi_index < 0.15 or hhi_index >= 0.25))
    or (concentration_level = 'well_distributed' and hhi_index >= 0.15)

    -- bus_factor_assessment thresholds match CASE logic
    or (bus_factor_assessment = 'no_data' and bus_factor != 0)
    or (bus_factor_assessment = 'critical' and (bus_factor != 1 and bus_factor != 0))
    or (bus_factor_assessment = 'at_risk' and bus_factor != 2)
    or (bus_factor_assessment = 'moderate' and (bus_factor < 3 or bus_factor > 3))
    or (bus_factor_assessment = 'healthy' and bus_factor <= 3)

    -- team_health_grade valid values
    or team_health_grade not in ('A', 'B', 'C', 'D', 'F')

    -- single_author_risk consistency: true iff top_author_pct >= 80
    or (single_author_risk and top_author_pct < 80.0)
    or (not single_author_risk and top_author_pct >= 80.0)
