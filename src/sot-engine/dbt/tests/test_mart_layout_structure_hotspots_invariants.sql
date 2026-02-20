select *
from {{ ref('mart_layout_structure_hotspots') }}
where
    -- risk_level_numeric matches risk_level
    (risk_level = 'critical' and risk_level_numeric != 4)
    or (risk_level = 'high' and risk_level_numeric != 3)
    or (risk_level = 'medium' and risk_level_numeric != 2)
    or (risk_level = 'low' and risk_level_numeric != 1)

    -- Non-negative metrics
    or depth < 0
    or file_count_recursive < 0
    or total_size_bytes_recursive < 0

    -- Rank columns >= 1
    or depth_rank < 1
    or file_rank < 1
    or size_rank < 1
