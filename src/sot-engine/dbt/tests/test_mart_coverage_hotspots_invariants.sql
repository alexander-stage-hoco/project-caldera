select *
from {{ ref('mart_coverage_hotspots') }}
where gap_to_target_pct < 0
   or lines_needed_for_target < 0
   or (risk_level = 'critical' and line_coverage_pct >= 20.0)
   or (risk_level = 'high' and (line_coverage_pct < 20.0 or line_coverage_pct >= 40.0))
   or (risk_level = 'medium' and (line_coverage_pct < 40.0 or line_coverage_pct >= 60.0))
   or (risk_level = 'low' and (line_coverage_pct < 60.0 or line_coverage_pct >= 80.0))
   or (risk_level = 'critical' and risk_level_numeric != 5)
   or (risk_level = 'high' and risk_level_numeric != 4)
   or (risk_level = 'medium' and risk_level_numeric != 3)
   or (risk_level = 'low' and risk_level_numeric != 2)
   or (risk_level = 'passing' and risk_level_numeric != 1)
   or (is_critical and line_coverage_pct >= 20.0)
   or (is_high_plus and line_coverage_pct >= 40.0)
   or (is_medium_plus and line_coverage_pct >= 60.0)
   or (is_below_target and line_coverage_pct >= 80.0)
   or (line_coverage_pct >= 80.0 and coverage_zscore >= -2.0)
