select *
from {{ ref('mart_project_blast_radius') }}
where
    -- Non-negative blast radius
    blast_radius_projects < 0

    -- Depth >= 1
    or blast_radius_depth < 1

    -- Total paths >= 1
    or total_paths < 1

    -- blast_radius_risk thresholds match CASE logic
    or (blast_radius_risk = 'critical' and blast_radius_projects < 10)
    or (blast_radius_risk = 'high' and (blast_radius_projects < 5 or blast_radius_projects >= 10))
    or (blast_radius_risk = 'medium' and (blast_radius_projects < 3 or blast_radius_projects >= 5))
    or (blast_radius_risk = 'low' and blast_radius_projects >= 3)
