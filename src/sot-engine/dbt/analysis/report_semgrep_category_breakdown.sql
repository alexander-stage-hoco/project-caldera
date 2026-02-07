-- Semgrep category breakdown with directory-level hotspots
-- Shows smells by category (error_handling, resource_management, dependency, security,
-- dead_code, refactoring, api_design, async_patterns, nullability)
-- with top directories per category and severity breakdown
--
-- Required vars: run_pk (integer)
-- Optional vars: limit (integer, default 5) - top directories per category

{{ category_breakdown(
    tool_names=['semgrep'],
    staging_model='stg_lz_semgrep_smells',
    entity_name='smell'
) }}
