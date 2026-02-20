select *
from {{ ref('mart_roslyn_rule_hotspots') }}
where
    -- Positive counts
    violation_count < 1
    or files_affected < 1

    -- severity_high_plus = severity_error + severity_warning
    or severity_high_plus != severity_error + severity_warning

    -- Severity breakdown bounded by violation_count
    or severity_error + severity_warning + severity_info + severity_hidden > violation_count

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and severity_error <= 0)
    or (risk_level = 'high' and (severity_warning <= 0 or severity_error > 0))
    or (risk_level = 'medium' and (severity_info <= 0 or severity_error > 0 or severity_warning > 0))
    or (risk_level = 'low' and (severity_error > 0 or severity_warning > 0 or severity_info > 0))

    -- severity_score non-negative
    or severity_score < 0

    -- Rank columns >= 1
    or violation_rank < 1
    or severity_rank < 1
    or spread_rank < 1
