select *
from {{ ref('mart_sonarqube_rule_hotspots') }}
where
    -- Positive counts
    issue_count < 1
    or files_affected < 1

    -- severity_high_plus = severity_blocker + severity_critical
    or severity_high_plus != severity_blocker + severity_critical

    -- Severity breakdown bounded by issue_count
    or severity_blocker + severity_critical + severity_major + severity_minor + severity_info > issue_count

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and severity_blocker <= 0)
    or (risk_level = 'high' and (severity_critical <= 0 or severity_blocker > 0))
    or (risk_level = 'medium' and (severity_major <= 0 or severity_blocker > 0 or severity_critical > 0))
    or (risk_level = 'low' and (severity_blocker > 0 or severity_critical > 0 or severity_major > 0))

    -- impact_score non-negative (weighted: blocker×4 + critical×3 + major×2 + minor×1)
    or impact_score < 0

    -- Effort metrics non-negative
    or total_effort_minutes < 0
    or avg_effort_minutes < 0

    -- Rank columns >= 1
    or occurrence_rank < 1
    or effort_rank < 1
    or impact_rank < 1
