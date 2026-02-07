-- Roslyn category breakdown with directory-level hotspots
-- Shows violations by category (security, design, resource, dead_code, performance, other)
-- with top directories per category and severity breakdown
--
-- Required vars: run_pk (integer)
-- Optional vars: limit (integer, default 5) - top directories per category

{{ category_breakdown(
    tool_names=['roslyn', 'roslyn-analyzers'],
    staging_model='stg_lz_roslyn_violations',
    entity_name='violation'
) }}
