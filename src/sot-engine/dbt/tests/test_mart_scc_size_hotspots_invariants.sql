select *
from {{ ref('mart_scc_size_hotspots') }}
where
    -- WHERE clause contract: at least one hotspot condition must be true
    not (lines_total > 200 or complexity > 15 or complexity_density > 0.05
         or lines_zscore > 2.0 or complexity_zscore > 2.0)

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and not (lines_total > 1000 or complexity > 50 or complexity_density > 0.20))
    or (risk_level = 'low' and (lines_total > 200 or complexity > 15 or complexity_density > 0.05))

    -- risk_level_numeric matches risk_level
    or (risk_level = 'critical' and risk_level_numeric != 4)
    or (risk_level = 'high' and risk_level_numeric != 3)
    or (risk_level = 'medium' and risk_level_numeric != 2)
    or (risk_level = 'low' and risk_level_numeric != 1)

    -- Boolean subset chain: is_critical → is_high_plus → is_medium_plus
    or (is_critical and not is_high_plus)
    or (is_high_plus and not is_medium_plus)

    -- Non-negative counts
    or lines_total < 0
    or code_lines < 0
    or comment_lines < 0
    or blank_lines < 0
    or bytes < 0
    or complexity < 0

    -- Upstream filter: minified and generated files excluded
    or is_minified = true
    or is_generated = true
