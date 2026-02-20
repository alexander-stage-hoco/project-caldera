select *
from {{ ref('mart_pmd_cpd_clone_hotspots') }}
where
    -- Positive counts
    lines < 1
    or tokens < 1
    or occurrence_count < 2

    -- total_duplicated_lines = lines * occurrence_count
    or total_duplicated_lines != lines * occurrence_count

    -- token_density non-negative
    or token_density < 0

    -- impact_score non-negative
    or impact_score < 0

    -- risk_level thresholds match CASE logic
    or (risk_level = 'critical' and not (lines >= 100 and is_cross_file))
    or (risk_level = 'high' and (lines >= 100 and is_cross_file))
    or (risk_level = 'high' and not (lines >= 100 or (lines >= 50 and is_cross_file) or occurrence_count >= 5))
    or (risk_level = 'low' and (lines >= 20 or is_cross_file or occurrence_count >= 3))

    -- Rank columns >= 1
    or size_rank < 1
    or occurrence_rank < 1
    or impact_rank < 1
    or spread_rank < 1
