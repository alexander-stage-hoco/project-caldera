select *
from {{ ref('mart_git_sizer_violation_hotspots') }}
where
    -- Positive counts
    violation_count < 1

    -- level_3_plus = level_3_count + level_4_count
    or level_3_plus != level_3_count + level_4_count

    -- Level breakdown bounded by violation_count
    or level_1_count + level_2_count + level_3_count + level_4_count > violation_count

    -- severity_score non-negative (weighted: level_4×4 + level_3×3 + level_2×2 + level_1×1)
    or severity_score < 0

    -- risk_level thresholds match max_level CASE logic
    or (risk_level = 'critical' and max_level != 4)
    or (risk_level = 'high' and max_level != 3)
    or (risk_level = 'medium' and max_level != 2)
    or (risk_level = 'low' and max_level > 1)

    -- max_level bounded 1-4
    or max_level < 1
    or max_level > 4

    -- min_level bounded 1-4 and <= max_level
    or min_level < 1
    or min_level > 4
    or min_level > max_level

    -- Rank columns >= 1
    or violation_rank < 1
    or severity_rank < 1
