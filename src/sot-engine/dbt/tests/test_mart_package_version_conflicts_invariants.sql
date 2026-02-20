select *
from {{ ref('mart_package_version_conflicts') }}
where
    -- Only conflicts: version_count >= 2
    version_count < 2

    -- projects_affected >= 1
    or projects_affected < 1

    -- conflict_severity thresholds match CASE logic
    or (conflict_severity = 'critical' and version_count < 4)
    or (conflict_severity = 'high' and version_count >= 4)
    or (conflict_severity = 'high' and not (version_count >= 3 or projects_affected >= 5))
    or (conflict_severity = 'medium' and (version_count != 2 or projects_affected < 3))
    or (conflict_severity = 'low' and (version_count >= 3 or projects_affected >= 5 or (version_count = 2 and projects_affected >= 3)))
