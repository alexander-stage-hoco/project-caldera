select *
from {{ ref('mart_semgrep_rule_hotspots') }}
where
    -- Positive counts
    smell_count < 1
    or files_affected < 1

    -- severity_high_plus = severity_critical + severity_high
    or severity_high_plus != severity_critical + severity_high

    -- Severity breakdown bounded by smell_count
    or severity_critical + severity_high + severity_medium + severity_low + severity_info > smell_count

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and severity_critical <= 0)
    or (risk_level = 'high' and (severity_high <= 0 or severity_critical > 0))
    or (risk_level = 'medium' and (severity_medium <= 0 or severity_critical > 0 or severity_high > 0))
    or (risk_level = 'low' and (severity_critical > 0 or severity_high > 0 or severity_medium > 0))

    -- severity_score non-negative
    or severity_score < 0

    -- Rank columns >= 1
    or smell_rank < 1
    or severity_rank < 1
    or spread_rank < 1
