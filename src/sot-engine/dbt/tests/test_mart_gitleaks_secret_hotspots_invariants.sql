select *
from {{ ref('mart_gitleaks_secret_hotspots') }}
where
    -- Positive counts
    detection_count < 1
    or files_affected < 1
    or authors_affected < 1

    -- in_head_count + historical_count = detection_count
    or in_head_count + historical_count != detection_count

    -- in_head_pct bounded 0-100
    or in_head_pct < 0
    or in_head_pct > 100

    -- severity_high_plus = severity_critical + severity_high
    or severity_high_plus != severity_critical + severity_high

    -- risk_level consistency: low iff in_head_count = 0
    or (risk_level = 'low' and in_head_count > 0)
    or (in_head_count = 0 and risk_level != 'low')

    -- risk_level consistency: critical iff in_head_count > 0 AND severity_critical > 0
    or (risk_level = 'critical' and (in_head_count = 0 or severity_critical = 0))
    or (in_head_count > 0 and severity_critical > 0 and risk_level != 'critical')

    -- risk_score non-negative
    or risk_score < 0

    -- Rank columns >= 1
    or detection_rank < 1
    or urgency_rank < 1
    or risk_rank < 1
