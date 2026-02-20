select *
from {{ ref('mart_project_dependency_cycles') }}
where
    -- Cycles need at least 2 nodes
    cycle_length < 2

    -- severity thresholds match CASE logic
    or (severity = 'critical' and cycle_length != 2)
    or (severity = 'high' and (cycle_length <= 2 or cycle_length > 4))
    or (severity = 'medium' and (cycle_length <= 4 or cycle_length > 6))
    or (severity = 'low' and cycle_length <= 6)
