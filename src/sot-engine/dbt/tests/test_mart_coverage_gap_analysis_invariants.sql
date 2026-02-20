select *
from {{ ref('mart_coverage_gap_analysis') }}
where lines_total <= 0
   or risk_score < 0 or risk_score > 100
   or ccn_normalized < 0 or ccn_normalized > 100
   or coverage_deficit < 0 or coverage_deficit > 100
   or risk_rank < 1
   or (risk_tier = 'CRITICAL' and risk_score < 80)
   or (risk_tier = 'HIGH' and (risk_score < 60 or risk_score >= 80))
   or (risk_tier = 'MEDIUM' and (risk_score < 40 or risk_score >= 60))
   or (risk_tier = 'LOW' and (risk_score < 20 or risk_score >= 40))
   or (risk_tier = 'MINIMAL' and risk_score >= 20)
