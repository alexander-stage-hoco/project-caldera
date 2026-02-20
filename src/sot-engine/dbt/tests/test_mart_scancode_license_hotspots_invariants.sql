select *
from {{ ref('mart_scancode_license_hotspots') }}
where
    -- Positive counts
    detection_count < 1
    or files_affected < 1

    -- Category breakdown bounded by detection_count
    or category_permissive + category_weak_copyleft + category_copyleft + category_unknown > detection_count

    -- risk_level thresholds match CASE logic
    or (risk_level = 'high' and category_copyleft <= 0)
    or (risk_level = 'medium' and (category_weak_copyleft <= 0 or category_copyleft > 0))
    or (risk_level = 'low' and (category_permissive <= 0 or category_copyleft > 0 or category_weak_copyleft > 0))
    or (risk_level = 'unknown' and (category_copyleft > 0 or category_weak_copyleft > 0 or category_permissive > 0))

    -- Confidence bounds
    or min_confidence < 0
    or max_confidence > 100.0
    or avg_confidence < min_confidence
    or avg_confidence > max_confidence

    -- Rank columns >= 1
    or detection_rank < 1
    or spread_rank < 1
