select *
from {{ ref('mart_symbol_coupling_hotspots') }}
where
    -- WHERE clause contract: total_coupling >= 5 OR coupling_zscore > 2.0 OR coupling_pattern != 'normal'
    not (total_coupling >= 5 or coupling_zscore > 2.0 or coupling_pattern != 'normal')

    -- total_coupling = fan_in + fan_out
    or total_coupling != fan_in + fan_out

    -- Non-negative fan counts
    or fan_in < 0
    or fan_out < 0

    -- instability bounded 0.0-1.0
    or instability < 0.0
    or instability > 1.0

    -- coupling_risk thresholds match CASE logic
    or (coupling_risk = 'critical' and total_coupling < 20)
    or (coupling_risk = 'high' and (total_coupling < 10 or total_coupling >= 20))
    or (coupling_risk = 'medium' and (total_coupling < 5 or total_coupling >= 10))
    or (coupling_risk = 'low' and total_coupling >= 5)

    -- coupling_risk_numeric matches coupling_risk
    or (coupling_risk = 'critical' and coupling_risk_numeric != 4)
    or (coupling_risk = 'high' and coupling_risk_numeric != 3)
    or (coupling_risk = 'medium' and coupling_risk_numeric != 2)
    or (coupling_risk = 'low' and coupling_risk_numeric != 1)

    -- Boolean subset chain: is_critical → is_high_plus → is_medium_plus
    or (is_critical and not is_high_plus)
    or (is_high_plus and not is_medium_plus)

    -- instability_zone thresholds match CASE logic
    or (instability_zone = 'unstable' and instability < 0.8)
    or (instability_zone = 'flexible' and (instability < 0.5 or instability >= 0.8))
    or (instability_zone = 'stable' and (instability < 0.2 or instability >= 0.5))
    or (instability_zone = 'rigid' and instability >= 0.2)

    -- coupling_pattern thresholds match CASE logic
    or (coupling_pattern = 'hub' and not (fan_in >= 10 and fan_out >= 10))
    or (coupling_pattern = 'god_object' and not (fan_in >= 10 and fan_out < 5))
    or (coupling_pattern = 'octopus' and not (fan_out >= 10 and fan_in < 5))
    or (coupling_pattern = 'normal' and (fan_in >= 10 and fan_out >= 10))
