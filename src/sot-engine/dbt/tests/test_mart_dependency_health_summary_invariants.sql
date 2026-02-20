select *
from {{ ref('mart_dependency_health_summary') }}
where
    -- Non-negative counts
    total_projects < 0
    or total_project_refs < 0
    or total_package_refs < 0
    or unique_packages < 0
    or circular_dependency_count < 0
    or version_conflict_count < 0
    or max_blast_radius < 0

    -- health_grade valid values
    or health_grade not in ('A', 'B', 'C', 'D', 'F')
