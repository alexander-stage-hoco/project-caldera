select *
from {{ ref('mart_complexity_hotspots') }}
where
    -- WHERE clause contract: every row has ccn > 10 OR ccn_zscore > 2.0
    not (ccn > 10 or ccn_zscore > 2.0)

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and ccn <= 50)
    or (risk_level = 'high' and (ccn <= 20 or ccn > 50))
    or (risk_level = 'medium' and (ccn <= 10 or ccn > 20))
    or (risk_level = 'low' and ccn > 10)

    -- risk_level_numeric matches risk_level
    or (risk_level = 'critical' and risk_level_numeric != 4)
    or (risk_level = 'high' and risk_level_numeric != 3)
    or (risk_level = 'medium' and risk_level_numeric != 2)
    or (risk_level = 'low' and risk_level_numeric != 1)

    -- Boolean subset chain: is_critical → is_high_plus → is_medium_plus
    or (is_critical and not is_high_plus)
    or (is_high_plus and not is_medium_plus)

    -- Non-negative metrics
    or ccn < 1
    or nloc < 0
    or params < 0

    -- line_end >= line_start
    or line_end < line_start
