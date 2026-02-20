select *
from {{ ref('mart_dotcover_coverage_hotspots') }}
where
    -- WHERE clause contract: every row has statement_coverage_pct < 80 OR coverage_zscore < -2.0
    not (statement_coverage_pct < 80.0 or coverage_zscore < -2.0)

    -- statement_coverage_pct bounded 0-100
    or statement_coverage_pct < 0
    or statement_coverage_pct > 100

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and statement_coverage_pct >= 20.0)
    or (risk_level = 'high' and (statement_coverage_pct < 20.0 or statement_coverage_pct >= 40.0))
    or (risk_level = 'medium' and (statement_coverage_pct < 40.0 or statement_coverage_pct >= 60.0))
    or (risk_level = 'low' and (statement_coverage_pct < 60.0 or statement_coverage_pct >= 80.0))
    or (risk_level = 'passing' and statement_coverage_pct < 80.0)

    -- risk_level_numeric matches risk_level
    or (risk_level = 'critical' and risk_level_numeric != 5)
    or (risk_level = 'high' and risk_level_numeric != 4)
    or (risk_level = 'medium' and risk_level_numeric != 3)
    or (risk_level = 'low' and risk_level_numeric != 2)
    or (risk_level = 'passing' and risk_level_numeric != 1)

    -- Boolean subset chain: is_critical → is_high_plus → is_medium_plus → is_below_target
    or (is_critical and not is_high_plus)
    or (is_high_plus and not is_medium_plus)
    or (is_medium_plus and not is_below_target)

    -- Gap metrics non-negative
    or gap_to_target_pct < 0
    or statements_needed_for_target < 0
