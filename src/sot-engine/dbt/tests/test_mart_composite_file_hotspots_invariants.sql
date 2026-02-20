select *
from {{ ref('mart_composite_file_hotspots') }}
where
    -- WHERE clause contract: all rows must have 2+ medium+ risks
    medium_plus_risk_count < 2

    -- Score bounded 0-100
    or composite_score < 0
    or composite_score > 100

    -- Count ordering: critical ⊆ high+ ⊆ medium+
    or high_plus_risk_count > medium_plus_risk_count
    or critical_risk_count > high_plus_risk_count

    -- available_dimensions bounded 0-5
    or available_dimensions < 0
    or available_dimensions > 5

    -- total_score bounded
    or total_score < 0
    or total_score > available_dimensions * 4

    -- Composite risk level matches CASE logic
    or (composite_risk_level = 'critical' and critical_risk_count < 2)
    or (critical_risk_count >= 2 and composite_risk_level != 'critical')
    or composite_risk_level = 'low'  -- unreachable: medium_plus >= 2 triggers 'medium' first

    -- Data flag vs score consistency
    or (not has_complexity_data and complexity_score is not null)
    or (not has_size_data and size_score is not null)
    or (not has_coverage_data and coverage_score is not null)
    or (not has_coupling_data and coupling_score is not null)
    or (not has_issues_data and issues_score is not null)

    -- Dimension scores in range 1-4 when present
    or (complexity_score is not null and complexity_score not in (1, 2, 3, 4))
    or (size_score is not null and size_score not in (1, 2, 3, 4))
    or (coverage_score is not null and coverage_score not in (1, 2, 3, 4))
    or (coupling_score is not null and coupling_score not in (1, 2, 3, 4))
    or (issues_score is not null and issues_score not in (1, 2, 3, 4))

    -- Non-negative issue count
    or total_high_plus_issues < 0
