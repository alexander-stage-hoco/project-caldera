select *
from {{ ref('mart_blast_radius_symbol') }}
where
    -- Non-negative blast radius counts
    blast_radius_symbols < 0
    or blast_radius_files < 0

    -- Depth constraints
    or max_depth < 1
    or min_depth < 1
    or max_depth < min_depth

    -- Total paths >= 1
    or total_paths < 1

    -- blast_radius_risk thresholds match CASE logic
    or (blast_radius_risk = 'critical' and blast_radius_symbols < 20)
    or (blast_radius_risk = 'high' and (blast_radius_symbols < 10 or blast_radius_symbols >= 20))
    or (blast_radius_risk = 'medium' and (blast_radius_symbols < 5 or blast_radius_symbols >= 10))
    or (blast_radius_risk = 'low' and blast_radius_symbols >= 5)
